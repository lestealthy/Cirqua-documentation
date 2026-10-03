#!/usr/bin/env python3
"""Regenerate sources/firmware-source.yml from the actual Git submodule state.

The manifest is the documentation's declaration of which firmware revision it
describes. It is generated rather than hand-maintained so that it cannot drift
silently away from the submodule that CI actually checks out.

Usage
-----
    python scripts/generate_source_manifest.py
    python scripts/generate_source_manifest.py --check
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install with: pip install PyYAML")


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "sources" / "firmware-source.yml"
SUBMODULE_PATH = "_external/Cirqua-firmware"

REPOSITORY = "https://github.com/lestealthy/Cirqua"


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def discover() -> dict:
    firmware = REPO_ROOT / SUBMODULE_PATH
    if not firmware.is_dir():
        sys.exit(f"submodule not initialised at {firmware}")

    commit = git("rev-parse", "HEAD", cwd=firmware)
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=firmware)

    # `git remote -v` prints: <name>\t<url> (fetch)
    remotes = git("remote", "-v", cwd=firmware)
    remote_url = ""
    for line in remotes.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].startswith("("):
            remote_url = parts[1]
            break
    remote_url = remote_url.removesuffix(".git") or REPOSITORY

    log = git("log", "--format=%H|%h|%s|%ad", "--date=short", cwd=firmware).splitlines()
    history = [
        {
            "commit": row.split("|")[0],
            "short": row.split("|")[1],
            "subject": row.split("|")[2],
            "date": row.split("|")[3],
        }
        for row in log
        if row.count("|") >= 3
    ]

    units = []
    for node_dir, node_name, role in (
        ("Node1", "Node 1", "Collection Tank A (TAV) level and cluster head display"),
        ("Node2", "Node 2", "Water temperature, dissolved oxygen, Tank B level, ambient telemetry"),
        ("Node3", "Node 3", "Inline flow metering and telemetry forwarding"),
        ("Node4", "Node 4", "Effluent pH, turbidity, conductivity and level"),
    ):
        source = firmware / "FreeRTOS_Implementation" / node_dir / f"{node_dir}.ino"
        if source.is_file():
            units.append(
                {
                    "id": node_dir.lower(),
                    "name": node_name,
                    "file": f"FreeRTOS_Implementation/{node_dir}/{node_dir}.ino",
                    "line_count": len(source.read_text(encoding="utf-8", errors="replace").splitlines()),
                    "role": role,
                    "status": "CURRENT",
                }
            )

    smtp = firmware / "FreeRTOS_Implementation" / "Node4_SMTP" / "Node4_SMTP.ino"
    if smtp.is_file():
        units.append(
            {
                "id": "node4-smtp",
                "name": "Node 4 (SMTP variant)",
                "file": "FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino",
                "line_count": len(smtp.read_text(encoding="utf-8", errors="replace").splitlines()),
                "role": "Node 4 sensor set plus Wi-Fi, NTP time synchronisation and SMTP alerting",
                "status": "CURRENT_VARIANT",
            }
        )

    historical = []
    old_root = firmware / "_OLD"
    if old_root.is_dir():
        for path in sorted(old_root.rglob("*.ino")):
            relative = path.relative_to(firmware).as_posix()
            historical.append(
                {
                    "id": path.stem.lower(),
                    "name": relative.rsplit("/", 1)[0] + "/" + path.stem,
                    "file": relative,
                    "line_count": len(path.read_text(encoding="utf-8", errors="replace").splitlines()),
                    "status": "HISTORICAL",
                }
            )

    return {
        "repository": remote_url or REPOSITORY,
        "repository_slug": "lestealthy/Cirqua",
        "branch": branch,
        "commit": commit,
        "commit_short": commit[:7],
        "path": SUBMODULE_PATH,
        "current_source_dir": "FreeRTOS_Implementation",
        "historical_source_dir": "_OLD",
        "current_units": units,
        "historical_units": historical,
        "source_link_template": f"https://github.com/lestealthy/Cirqua/blob/{commit}/{{path}}",
        "tree_link_template": f"https://github.com/lestealthy/Cirqua/tree/{commit}/{{path}}",
        "commit_history": history,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the manifest is stale")
    args = parser.parse_args()

    data = discover()

    # Preserve the hand-written explanatory comments at the top of the file.
    header = """# Canonical firmware source consumed by this documentation repository.
#
# GENERATED by scripts/generate_source_manifest.py - do not hand-edit the
# commit/branch/unit fields. Run the script after moving the submodule.
#
# This file is the single machine-readable record of WHICH firmware revision
# the published documentation describes. It is verified by
# scripts/validate_docs.py during CI.
"""

    payload = header + "\n" + yaml.safe_dump(data, sort_keys=False, width=110, allow_unicode=True)

    if args.check:
        if not MANIFEST.is_file():
            print("manifest missing")
            return 1
        current = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        drift = []
        for key in ("commit", "branch", "repository", "path", "commit_short"):
            if current.get(key) != data.get(key):
                drift.append(f"{key}: manifest={current.get(key)!r} actual={data.get(key)!r}")
        if drift:
            print("MANIFEST STALE:")
            for item in drift:
                print(f"  - {item}")
            return 1
        print(f"OK - manifest matches submodule at {data['commit_short']}")
        return 0

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(payload, encoding="utf-8")

    print(f"repository   : {data['repository']}")
    print(f"branch       : {data['branch']}")
    print(f"commit       : {data['commit']}")
    print(f"current units: {len(data['current_units'])}")
    print(f"historical   : {len(data['historical_units'])}")
    print(f"commits      : {len(data['commit_history'])}")
    print(f"\nwrote {MANIFEST.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())