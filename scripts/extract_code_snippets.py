#!/usr/bin/env python3
"""
Extract real code snippets from the pinned CIRQUA firmware into the
documentation tree.

Design goals
------------
* Deterministic: the same firmware commit always produces the same output.
* Traceable: every snippet carries repository, file, symbol, commit and the
  exact line range it was taken from.
* Zero hand-written code: nothing in docs/assets/snippets/ is authored by a
  human. If it is not found in the firmware, it is not in the documentation.
* Read-only with respect to the firmware: the submodule is never modified.

Usage
-----
    python scripts/extract_code_snippets.py            # regenerate snippets
    python scripts/extract_code_snippets.py --check    # verify nothing is stale

Output
------
    docs/assets/snippets/<snippet_id>.cpp
    docs/assets/snippets/snippet-index.yml
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install with: pip install PyYAML")


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "sources" / "firmware-source.yml"
SNIPPET_DIR = REPO_ROOT / "docs" / "assets" / "snippets"


# ---------------------------------------------------------------------------
# Snippet registry
#
# anchor_kind:
#   "function"  - capture from a declaration through its matching closing brace
#   "define"    - capture a single #define line plus any trailing comment block
#   "lines"     - capture an explicit 1-based inclusive line range
#
# keep_leading_banner pulls in the decorative comment block immediately above
# the anchor so the published snippet keeps its original engineering context.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Snippet:
    snippet_id: str
    path: str
    anchor_kind: str
    anchor: str
    label: str
    keep_leading_banner: bool = True
    extra_lines_before: int = 0
    extra_lines_after: int = 0


REGISTRY: tuple[Snippet, ...] = (
    # ---------------- Node 1 --------------------------------------------
    Snippet(
        "node1-pin-definitions",
        "FreeRTOS_Implementation/Node1/Node1.ino",
        "lines",
        "5-35",
        "Node 1 hardware pin assignments, tank geometry and alert thresholds",
        keep_leading_banner=False,
    ),
    Snippet(
        "node1-ultrasonic-measurement",
        "FreeRTOS_Implementation/Node1/Node1.ino",
        "function",
        r"void\s+Task_Sensors_Node1\s*\(",
        "Node 1 ultrasonic acquisition task (HC-SR04 trigger/echo to litres)",
    ),
    Snippet(
        "node1-frame-parser",
        "FreeRTOS_Implementation/Node1/Node1.ino",
        "function",
        r"String\s+getFieldFromFrame\s*\(",
        "Node 1 key/value field extraction helper",
    ),
    Snippet(
        "node1-packet-processing",
        "FreeRTOS_Implementation/Node1/Node1.ino",
        "function",
        r"void\s+processNode2Packet\s*\(",
        "Node 2 telemetry frame processing into the protected telemetry struct",
    ),
    Snippet(
        "node1-uart-task",
        "FreeRTOS_Implementation/Node1/Node1.ino",
        "function",
        r"void\s+Task_UART_Node1\s*\(",
        "Node 1 bidirectional UART task with 500 ms transmit interval",
    ),
    Snippet(
        "node1-lcd-task",
        "FreeRTOS_Implementation/Node1/Node1.ino",
        "function",
        r"void\s+Task_LCD_Node1\s*\(",
        "Node 1 16x4 LCD rendering and status-string derivation",
    ),
    Snippet(
        "node1-setup",
        "FreeRTOS_Implementation/Node1/Node1.ino",
        "function",
        r"void\s+setup\s*\(\s*\)\s*\{",
        "Node 1 task creation pinned to cores 0 and 1",
    ),
    # ---------------- Node 2 --------------------------------------------
    Snippet(
        "node2-pin-definitions",
        "FreeRTOS_Implementation/Node2/Node2.ino",
        "lines",
        "10-32",
        "Node 2 pin assignments, DO electrical calibration constants and tank geometry",
        keep_leading_banner=False,
    ),
    Snippet(
        "node2-sensor-task",
        "FreeRTOS_Implementation/Node2/Node2.ino",
        "function",
        r"void\s+Task_Sensors_Node2\s*\(",
        "Node 2 sensor acquisition task: DS18B20, dissolved oxygen, HC-SR04, DHT11",
    ),
    Snippet(
        "node2-parse-node1",
        "FreeRTOS_Implementation/Node2/Node2.ino",
        "function",
        r"bool\s+parseNode1Packet\s*\(",
        "Node 2 parser for the upstream Node 1 frame",
    ),
    Snippet(
        "node2-parse-node3",
        "FreeRTOS_Implementation/Node2/Node2.ino",
        "function",
        r"bool\s+parseNode3ReversePacket\s*\(",
        "Node 2 parser for the Node 3 reverse telemetry frame",
    ),
    Snippet(
        "node2-uart-routing",
        "FreeRTOS_Implementation/Node2/Node2.ino",
        "function",
        r"void\s+Task_UART_Node2\s*\(",
        "Node 2 UART routing, frame consolidation and echo to Node 1",
    ),
    Snippet(
        "node2-setup",
        "FreeRTOS_Implementation/Node2/Node2.ino",
        "function",
        r"void\s+setup\s*\(\s*\)\s*\{",
        "Node 2 task creation",
    ),
    # ---------------- Node 3 --------------------------------------------
    Snippet(
        "node3-pin-definitions",
        "FreeRTOS_Implementation/Node3/Node3.ino",
        "lines",
        "3-13",
        "Node 3 pin assignments and flow calibration constant",
        keep_leading_banner=False,
    ),
    Snippet(
        "node3-pulse-isr",
        "FreeRTOS_Implementation/Node3/Node3.ino",
        "lines",
        "15-23",
        "Node 3 critical-section pulse counter ISR",
        keep_leading_banner=False,
    ),
    Snippet(
        "node3-flow-task",
        "FreeRTOS_Implementation/Node3/Node3.ino",
        "function",
        r"void\s+Task_Flow_Node3\s*\(",
        "Node 3 1 Hz flow rate computation from counted pulses",
    ),
    Snippet(
        "node3-frame-validation",
        "FreeRTOS_Implementation/Node3/Node3.ino",
        "function",
        r"bool\s+validateUpstreamFrame\s*\(",
        "Node 3 upstream frame integrity check",
    ),
    Snippet(
        "node3-uart-forwarding",
        "FreeRTOS_Implementation/Node3/Node3.ino",
        "function",
        r"void\s+Task_UART_Node3\s*\(",
        "Node 3 dual-UART forwarding plus upstream timeout fallback frame",
    ),
    Snippet(
        "node3-setup",
        "FreeRTOS_Implementation/Node3/Node3.ino",
        "function",
        r"void\s+setup\s*\(\s*\)\s*\{",
        "Node 3 task creation",
    ),
    # ---------------- Node 4 --------------------------------------------
    Snippet(
        "node4-pin-definitions",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "lines",
        "10-41",
        "Node 4 pin assignments, ADC constants and tank geometry",
        keep_leading_banner=False,
    ),
    Snippet(
        "node4-calibration-struct",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "lines",
        "53-66",
        "Node 4 non-volatile calibration storage declaration",
        keep_leading_banner=False,
    ),
    Snippet(
        "node4-load-calibration",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"void\s+loadCalibration\s*\(",
        "Node 4 calibration load with factory defaults from NVS",
    ),
    Snippet(
        "node4-adc-configuration",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"void\s+configureADC\s*\(",
        "Node 4 ESP32 ADC attenuation and resolution configuration",
    ),
    Snippet(
        "node4-filtered-adc",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"uint16_t\s+readADCFiltered\s*\(",
        "Node 4 16-sample averaged raw ADC read",
    ),
    Snippet(
        "node4-sensor-voltage",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"float\s+readSensorVoltage\s*\(",
        "Node 4 calibration-aware millivolt acquisition",
    ),
    Snippet(
        "node4-tank-volume",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"bool\s+readTankVolume\s*\(",
        "Node 4 effluent tank volume measurement with range rejection",
    ),
    Snippet(
        "node4-ph-processing",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "lines",
        "458-509",
        "Node 4 pH computation, temperature compensation and validity gating",
        keep_leading_banner=False,
    ),
    Snippet(
        "node4-turbidity-processing",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "lines",
        "511-582",
        "Node 4 turbidity to NTU conversion and saturation handling",
        keep_leading_banner=False,
    ),
    Snippet(
        "node4-ec-processing",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "lines",
        "584-635",
        "Node 4 conductivity K-factor conversion and temperature compensation",
        keep_leading_banner=False,
    ),
    Snippet(
        "node4-sensor-task",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"void\s+Task_Sensors_Node4\s*\(",
        "Node 4 combined sensor sampling task",
    ),
    Snippet(
        "node4-calibration-console",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"void\s+handleSerialCalibrationCommands\s*\(",
        "Node 4 PC serial calibration and diagnostics console",
    ),
    Snippet(
        "node4-packet-cleaner",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"String\s+cleanUpstreamPacket\s*\(",
        "Node 4 upstream packet cleaning (removes stale AT/AH fields)",
    ),
    Snippet(
        "node4-uart-task",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"void\s+Task_UART_Node4\s*\(",
        "Node 4 UART forwarding and cluster packet assembly",
    ),
    Snippet(
        "node4-lcd-task",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"void\s+Task_LCD_Node4\s*\(",
        "Node 4 local 16x4 LCD rendering",
    ),
    Snippet(
        "node4-setup",
        "FreeRTOS_Implementation/Node4/Node4.ino",
        "function",
        r"void\s+setup\s*\(\s*\)\s*\{",
        "Node 4 task creation",
    ),
    # ---------------- Node 4 SMTP variant ------------------------------
    Snippet(
        "node4-smtp-network-config",
        "FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino",
        "lines",
        "11-24",
        "Node 4 SMTP variant network and SMTP configuration block (placeholders only)",
        keep_leading_banner=False,
    ),
    Snippet(
        "node4-smtp-init-network",
        "FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino",
        "function",
        r"void\s+initNetworkAndTime\s*\(",
        "Node 4 SMTP Wi-Fi association and NTP time synchronisation",
    ),
    Snippet(
        "node4-smtp-send-mail",
        "FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino",
        "function",
        r"bool\s+sendMailMessage\s*\(",
        "Node 4 SMTP message dispatch helper",
    ),
    Snippet(
        "node4-smtp-alert-logic",
        "FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino",
        "lines",
        "301-350",
        "Node 4 SMTP heartbeat and fault-alert rate limiting",
        keep_leading_banner=False,
    ),
    Snippet(
        "node4-smtp-setup",
        "FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino",
        "function",
        r"void\s+setup\s*\(\s*\)\s*\{",
        "Node 4 SMTP task creation",
    ),
    # ---------------- Historical ----------------------------------------
    Snippet(
        "legacy-node3-ping",
        "_OLD/node3_fixed/node3_fixed.ino",
        "lines",
        "1-40",
        "Historical / Legacy - Node 3 predecessor sketch (not current architecture)",
        keep_leading_banner=False,
    ),
)


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

BANNER_LINE = re.compile(r"^\s*//\s*={3,}\s*$|^\s*//\s*-{3,}\s*$")


def _scan_line(code: str, state: dict) -> int:
    """Count structural braces in one line of C/C++ source.

    `state` carries the multi-line lexical state (block comment) between calls.
    Returns the net brace depth change for this line, ignoring braces that
    appear inside comments, string literals or character literals.
    """
    delta = 0
    i = 0
    n = len(code)

    while i < n:
        char = code[i]

        # --- inside a multi-line block comment ----------------------------
        if state.get("block_comment"):
            end = code.find("*/", i)
            if end == -1:
                return delta  # comment continues onto the next line
            state["block_comment"] = False
            i = end + 2
            continue

        # --- line comment --------------------------------------------------
        if char == "/" and i + 1 < n:
            if code[i + 1] == "/":
                return delta
            if code[i + 1] == "*":
                state["block_comment"] = True
                i += 2
                continue

        # --- string literal -------------------------------------------------
        if char == '"':
            i += 1
            while i < n:
                if code[i] == "\\":
                    i += 2
                    continue
                if code[i] == '"':
                    i += 1
                    break
                if code[i] == "\n":
                    break  # unterminated; bail out safely
                i += 1
            continue

        # --- character literal ----------------------------------------------
        # Note: an apostrophe inside a comment never reaches here, because
        # comments are consumed above. This matters for real code such as
        #   /* Don't invalidate the reading ... */
        if char == "'":
            i += 1
            while i < n:
                if code[i] == "\\":
                    i += 2
                    continue
                if code[i] == "'":
                    i += 1
                    break
                if code[i] == "\n":
                    break
                i += 1
            continue

        if char == "{":
            delta += 1
        elif char == "}":
            delta -= 1

        i += 1

    return delta


def _read(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text.splitlines()


def _find_anchor(lines: list[str], pattern: str) -> int:
    """Return 0-based index of the first line matching `pattern`."""
    regex = re.compile(pattern)
    for index, line in enumerate(lines):
        if regex.search(line):
            return index
    raise LookupError(f"anchor not found: {pattern!r}")


def _banner_start(lines: list[str], anchor_index: int) -> int:
    """Walk backwards over a contiguous comment banner above `anchor_index`."""
    index = anchor_index - 1
    start = None
    while index >= 0:
        stripped = lines[index].strip()
        if stripped.startswith("//") or stripped == "":
            if start is None:
                start = index
            elif stripped == "":
                break  # blank line ends the banner
            index -= 1
            continue
        break
    return start if start is not None else anchor_index


def _block_end(lines: list[str], open_index: int) -> int:
    """Return 0-based index of the line closing the brace opened at `open_index`.

    The opening line is expected to contain the opening brace. Braces inside
    comments (line and block) and inside string/character literals are ignored.
    """
    depth = 0
    started = False
    state = {"block_comment": False}

    for index in range(open_index, len(lines)):
        delta = _scan_line(lines[index], state)
        if delta:
            depth += delta
            started = True
        if started and depth <= 0:
            return index

    raise LookupError("unbalanced braces; could not find block end")


def _parse_line_range(spec: str, total: int) -> tuple[int, int]:
    start_text, _, end_text = spec.partition("-")
    start = int(start_text)
    end = int(end_text) if end_text else start
    if start < 1 or end > total or end < start:
        raise ValueError(f"invalid line range {spec!r} for a {total}-line file")
    return start, end


def extract(snippet: Snippet, firmware_root: Path) -> dict:
    source = firmware_root / snippet.path
    if not source.is_file():
        raise FileNotFoundError(f"firmware file missing: {source}")

    lines = _read(source)
    total = len(lines)

    if snippet.anchor_kind == "lines":
        start, end = _parse_line_range(snippet.anchor, total)
        body = lines[start - 1 : end]
        start_line, end_line = start, end
        symbol = ""

    elif snippet.anchor_kind == "define":
        anchor_index = _find_anchor(lines, snippet.anchor)
        start_line = anchor_index + 1
        end_line = start_line + snippet.extra_lines_after
        body = lines[anchor_index:end_line]
        symbol = snippet.anchor.strip()

    elif snippet.anchor_kind == "function":
        anchor_index = _find_anchor(lines, snippet.anchor)
        begin = _banner_start(lines, anchor_index) if snippet.keep_leading_banner else anchor_index
        end_index = _block_end(lines, anchor_index)
        start_line = max(begin + 1, 1) - snippet.extra_lines_before
        end_line = min(end_index + 1, total) + snippet.extra_lines_after
        body = lines[start_line - 1 : end_line]
        symbol = snippet.anchor

    else:  # pragma: no cover - guarded by the dataclass
        raise ValueError(f"unknown anchor_kind: {snippet.anchor_kind}")

    code = "\n".join(body).rstrip() + "\n"

    # Enforce relative-only, forward-slash paths in published output.
    relative_path = snippet.path.replace("\\", "/")

    return {
        "id": snippet.snippet_id,
        "label": snippet.label,
        "symbol": symbol,
        "path": relative_path,
        "start_line": start_line,
        "end_line": end_line,
        "line_count": len(body),
        "status": "HISTORICAL" if relative_path.startswith("_OLD/") else "CURRENT",
        "code": code,
    }


# ---------------------------------------------------------------------------
# Redaction
#
# The SMTP variant carries credential-shaped placeholders. They are already
# placeholders in the source, but the documentation must never render
# anything that resembles a live secret. Guard regardless.
# ---------------------------------------------------------------------------

SECRET_KEYS = (
    "WIFI_PASSWORD",
    "AUTHOR_PASSWORD",
    "API_KEY",
    "SECRET",
    "TOKEN",
)


def redact(code: str) -> tuple[str, list[str]]:
    """Replace credential values with a redaction marker.

    Returns the cleaned code and the list of keys that were redacted.
    """
    findings: list[str] = []
    pattern = re.compile(
        r'(#define\s+(?:' + "|".join(SECRET_KEYS) + r')\s+)("(?:[^"\\]|\\.)*")'
    )

    def _replace(match: re.Match) -> str:
        key = match.group(1).split()[1]
        findings.append(key)
        return f'{match.group(1)}"<REDACTED - set at build time>"'

    return pattern.sub(_replace, code), findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the generated snippets are out of date",
    )
    args = parser.parse_args()

    if not MANIFEST.is_file():
        sys.exit(f"manifest not found: {MANIFEST}")

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    firmware_root = REPO_ROOT / manifest["path"]
    commit = manifest["commit"]
    template = manifest.get("source_link_template", "")

    if not firmware_root.is_dir():
        sys.exit(
            f"firmware submodule not initialised at {firmware_root}\n"
            "Run: git submodule update --init --recursive"
        )

    SNIPPET_DIR.mkdir(parents=True, exist_ok=True)

    index: list[dict] = []
    redacted_total: list[str] = []
    stale: list[str] = []
    failures: list[str] = []

    for snippet in REGISTRY:
        try:
            record = extract(snippet, firmware_root)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{snippet.snippet_id}: {exc}")
            continue

        code, redacted = redact(record["code"])
        record["code"] = code
        if redacted:
            redacted_total.extend(redacted)
            record["redacted_keys"] = sorted(set(redacted))

        record["commit"] = commit
        record["commit_short"] = commit[:7]
        record["source_url"] = template.format(commit=commit, path=record["path"])
        record["snippet_file"] = f"assets/snippets/{snippet.snippet_id}.cpp"

        target = SNIPPET_DIR / f"{snippet.snippet_id}.cpp"
        payload = code if code.endswith("\n") else code + "\n"
        if target.is_file() and target.read_text(encoding="utf-8") == payload:
            pass
        else:
            stale.append(snippet.snippet_id)
            if not args.check:
                target.write_text(payload, encoding="utf-8")

        index.append({key: value for key, value in record.items() if key != "code"})

    index_doc = {
        "generated_from": manifest["repository"],
        "branch": manifest["branch"],
        "commit": commit,
        "snippet_count": len(index),
        "redacted_keys": sorted(set(redacted_total)),
        "snippets": index,
    }
    index_path = SNIPPET_DIR / "snippet-index.yml"
    serialised = yaml.safe_dump(index_doc, sort_keys=False, width=100, allow_unicode=True)

    if index_path.is_file() and index_path.read_text(encoding="utf-8") == serialised:
        pass
    else:
        stale.append("snippet-index.yml")
        if not args.check:
            index_path.write_text(serialised, encoding="utf-8")

    print(f"firmware commit : {commit}")
    print(f"firmware path   : {manifest['path']}")
    print(f"snippets        : {len(index)} extracted")
    print(f"output          : {SNIPPET_DIR.relative_to(REPO_ROOT)}")

    if redacted_total:
        print(f"redacted keys   : {', '.join(sorted(set(redacted_total)))}")

    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(f"  - {failure}")

    if args.check and (stale or failures):
        print(f"\nOUT OF DATE: {', '.join(stale)}")
        return 1

    if not args.check and failures:
        return 1

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())