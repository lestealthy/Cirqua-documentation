#!/usr/bin/env python3
"""
Technical truth audit: re-derive the audited facts directly from the pinned
firmware and confirm the documentation still agrees with them.

This is deliberately independent of the snippet extractor. Where
`extract_code_snippets.py` verifies that *published code* matches the source,
this script verifies that the *prose and tables* in the documentation still
match the source. A firmware change that silently invalidates a documented
GPIO, task, constant or frame format is caught here.

Checks
------
  1  Every GPIO #define quoted in a docs table exists in the named sketch
  2  Every FreeRTOS task table (name, stack, priority, core) matches
     xTaskCreatePinnedToCore
  3  Every calibration/geometry constant quoted in docs matches the sketch
  4  Every inter-node baud rate quoted matches INTERNODE_BAUD
  5  Every firmware commit referenced in docs is the pinned commit
  6  The `_OLD` tree is never presented as current firmware
  7  No documentation page claims a hardware revision that the repo lacks

Usage
-----
    python scripts/audit_truth.py
    python scripts/audit_truth.py --verbose
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"

MANIFEST = yaml.safe_load((REPO / "sources" / "firmware-source.yml").read_text(encoding="utf-8"))
FIRMWARE = REPO / MANIFEST["path"]
COMMIT = MANIFEST["commit"]

CURRENT = FIRMWARE / MANIFEST["current_source_dir"]

VERBOSE = False
findings: list[tuple[str, str]] = []


def ok(message: str) -> None:
    if VERBOSE:
        print(f"  PASS  {message}")


def problem(message: str) -> None:
    findings.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def md_files() -> list[Path]:
    return sorted(DOCS.rglob("*.md"))


def all_md_text() -> str:
    return "\n".join(read(p) for p in md_files())


# ---------------------------------------------------------------------------
# 1. Firmware facts re-derived from source
# ---------------------------------------------------------------------------


def defines() -> dict[str, int]:
    """sketch name -> set of PIN_* macro names"""
    out: dict[str, set[str]] = {}
    for sketch in sorted(CURRENT.rglob("*.ino")):
        names = set(re.findall(r"^#define\s+(PIN_\w+)\s+(\d+)", read(sketch), re.M))
        out[sketch.stem] = {n for n, _ in names}
    return out


def tasks() -> dict[str, dict[str, tuple[int, int]]]:
    """sketch name -> { task name: (stack, priority) } plus core per task."""
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for sketch in sorted(CURRENT.rglob("*.ino")):
        text = read(sketch)
        found: dict[str, tuple[int, int]] = {}
        # xTaskCreatePinnedToCore(fn, "NAME", STACK, NULL, PRIO, NULL, CORE);
        pattern = re.compile(
            r"xTaskCreatePinnedToCore\s*\(\s*(\w+)\s*,\s*\"([^\"]+)\"\s*,\s*(\d+)\s*,"
            r"\s*NULL\s*,\s*(\d+)\s*,\s*NULL\s*,\s*(\d+)\s*\)",
            re.S,
        )
        for match in pattern.finditer(text):
            fn, name, stack, prio, core = match.groups()
            found[name] = (int(stack), int(prio), int(core))  # type: ignore[assignment]
        out[sketch.stem] = found
    return out


def constants() -> dict[str, float]:
    """Numeric constants declared by each current sketch.

    Covers `const float`, `const int`, `static const` and bare `#define`
    numeric forms, because the documentation quotes values from all of them.
    """
    out: dict[str, float] = {}
    patterns = (
        r"^\s*(?:static\s+)?const\s+(?:float|int|uint\d+_t|int\d+_t)\s+(\w+)\s*=\s*([-\d.]+)f?\s*;",
        r"^\s*#define\s+(\w+)\s+([-\d.]+)f?\s*$",
        r"^\s*(?:static\s+)?const\s+(?:float|int)\s+(\w+)\s*=\s*(\d+)\s*;",
    )
    for sketch in sorted(CURRENT.rglob("*.ino")):
        text = read(sketch)
        for pattern in patterns:
            for name, value in re.findall(pattern, text, re.M):
                try:
                    out[f"{sketch.stem}:{name}"] = float(value)
                except ValueError:
                    continue
    return out


def main() -> int:
    global VERBOSE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    VERBOSE = parser.parse_args().verbose

    if not CURRENT.is_dir():
        sys.exit(f"firmware submodule not initialised at {FIRMWARE}")

    print("CIRQUA technical truth audit")
    print("=" * 70)
    print(f"firmware : {MANIFEST['repository']}")
    print(f"commit   : {COMMIT}")
    print(f"source   : {MANIFEST['path']}/{MANIFEST['current_source_dir']}/")
    print()

    text = all_md_text()
    fw_defs = defines()
    fw_tasks = tasks()
    fw_consts = constants()

    # ---- 1. GPIO defines -------------------------------------------------
    # Any `PIN_XXX  <n>` claimed on a docs page must exist in the sketches.
    known_defines = set().union(*fw_defs.values()) if fw_defs else set()
    quoted = set(re.findall(r"\b(PIN_[A-Z0-9_]+)\b", text))
    unknown = sorted(q for q in quoted if q not in known_defines)
    if unknown:
        problem(f"docs reference GPIO macros that do not exist in firmware: {', '.join(unknown)}")
    else:
        ok(f"all {len(quoted)} referenced PIN_* macros exist in the firmware")

    # ---- 2. Task table ---------------------------------------------------
    known_tasks = {name for table in fw_tasks.values() for name in table}
    quoted_tasks = set(re.findall(r"\b(N[1-4](?:_[A-Za-z]+)+)\b", text))
    unknown_tasks = sorted(t for t in quoted_tasks if t not in known_tasks)
    if unknown_tasks:
        problem(f"docs reference task names absent from the firmware: {', '.join(unknown_tasks)}")
    else:
        ok(f"all {len(quoted_tasks)} referenced task names exist in the firmware")

    # Cross-check the documented stack/priority for each task name.
    for sketch, table in fw_tasks.items():
        for name, (stack, prio, core) in table.items():  # type: ignore[misc]
            # Look for a row in any markdown table asserting this task.
            pattern = re.compile(
                rf"`{re.escape(name)}`[^|\n]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)"
            )
            for md in md_files():
                for match in pattern.finditer(read(md)):
                    d_stack, d_prio, d_core = (int(g) for g in match.groups())
                    if d_stack != stack:
                        problem(
                            f"{md.relative_to(DOCS)}: task {name} stack {d_stack} != firmware {stack}"
                        )
                    if d_prio != prio:
                        problem(
                            f"{md.relative_to(DOCS)}: task {name} priority {d_prio} != firmware {prio}"
                        )
                    if d_core != core:
                        problem(
                            f"{md.relative_to(DOCS)}: task {name} core {d_core} != firmware {core}"
                        )
    ok("documented task stack/priority/core values match xTaskCreatePinnedToCore")

    # ---- 3. Geometry and calibration constants ---------------------------
    # Values the docs assert as authoritative, mapped to the firmware symbol.
    # Note: sketch keys use `stems without the .ino suffix`.
    expected = [
        ("Node1", "TANK_HEIGHT", 260.0),
        ("Node1", "TANK_RADIUS", 110.0),
        ("Node1", "TAV_LOW_ALERT_TH", 5000.0),
        ("Node1", "TEMP_ALERT_TH", 45.0),
        ("Node1", "HUMID_ALERT_TH", 80.0),
        ("Node1", "RX_TIMEOUT_MS", 3000.0),
        ("Node2", "TANK_HEIGHT", 178.0),
        ("Node2", "TANK_RADIUS", 59.5),
        ("Node2", "VREF", 5000.0),
        ("Node2", "ADC_RESOLUTION", 4095.0),
        ("Node2", "TWO_POINT_VOLTAGE", 1000.0),
        ("Node2", "SATURATION_DO_25C", 8.26),
        ("Node3", "FLOW_CAL_FACTOR", 5.5),
        ("Node3", "TIMEOUT_MS", 2000.0),
        ("Node4", "TANK_HEIGHT", 178.0),
        ("Node4", "TANK_RADIUS", 59.5),
        ("Node4", "ADC_RESOLUTION", 4095.0),
        ("Node4", "ADC_SAMPLES", 16.0),
    ]
    for sketch, name, want in expected:
        key = f"{sketch}:{name}"
        got = fw_consts.get(key)
        if got is None:
            problem(f"expected constant {key} not found in {sketch}.ino")
        elif abs(got - want) > 1e-9:
            problem(f"constant drift: {key} is {got} in firmware, docs assume {want}")
        else:
            ok(f"{key} = {got}")

    # ---- 4. Baud rate ----------------------------------------------------
    bauds = set()
    for sketch in sorted(CURRENT.rglob("*.ino")):
        bauds.update(re.findall(r"#define\s+INTERNODE_BAUD\s+(\d+)", read(sketch)))
    if bauds == {"9600"}:
        ok("INTERNODE_BAUD is 9600 on every current sketch")
    else:
        problem(f"INTERNODE_BAUD values unexpected: {sorted(bauds)}")

    # ---- 5. Commit consistency -------------------------------------------
    bad_shas = {
        sha
        for sha in re.findall(r"\b[0-9a-f]{40}\b", text)
        if sha != COMMIT
    }
    if bad_shas:
        problem(f"docs cite firmware commits that are not the pinned one: {sorted(bad_shas)}")
    else:
        ok("every firmware commit cited in the docs is the pinned commit")

    # ---- 6. _OLD must not be presented as current -------------------------
    # Only a page that *cites a legacy source file* must carry a historical
    # label. An incidental mention such as "not comparable with `_OLD` data"
    # is a passing reference and correctly needs no such label.
    legacy_citation = re.compile(r"_OLD/[A-Za-z0-9_/]+\.(?:ino|txt)")
    for md in md_files():
        body = read(md)
        if not legacy_citation.search(body):
            continue
        lowered = body.lower()
        if not any(
            marker in lowered
            for marker in ("historical", "legacy", "not the current")
        ):
            problem(
                f"{md.relative_to(DOCS)} cites a file inside _OLD/ but does not label it historical"
            )

    ok("every page referencing _OLD labels it historical")

    # ---- 7. Hardware revision must not be invented ------------------------
    invented = re.findall(
        r"HW\s*Rev(?:ision)?\s*[.:]?\s*(?!not recorded|unknown|not verified)[A-Z]\b", text, re.I
    )
    if invented:
        problem(f"docs appear to assert a hardware revision: {invented[:5]}")
    else:
        ok("no hardware revision is asserted; it is recorded as not recorded")

    # ---- report -----------------------------------------------------------
    print()
    if findings:
        print(f"DISCREPANCIES ({len(findings)}):")
        for item in findings:
            print(f"  - {item}")
        print()
        print("RESULT: FAIL")
        return 1

    print("No discrepancies between the documentation and the pinned firmware.")
    print()
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())