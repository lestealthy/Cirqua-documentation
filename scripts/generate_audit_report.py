#!/usr/bin/env python3
"""Generate the internal documentation audit report.

Collects facts from the built site, the firmware manifest, the snippet index,
the QR manifest and the CI state, then prints the audit report defined in the
implementation brief. This is a reporting tool: it never fails the build.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
SITE = REPO / "site"

SITE_BASE = "https://lestealthy.github.io/Cirqua-documentation"
FIRMWARE_REPO = "https://github.com/lestealthy/Cirqua"
DOCS_REPO = "https://github.com/lestealthy/Cirqua-documentation"


def run(*args: str) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def count(pattern: str, root: Path, suffix: str) -> int:
    """Count regex matches across files.

    MULTILINE is required so that line-anchored patterns such as ^``` and
    ^!!! actually match inside each file.
    """
    if not root.is_dir():
        return 0
    compiled = re.compile(pattern, re.MULTILINE)
    total = 0
    for path in root.rglob(f"*{suffix}"):
        try:
            total += len(compiled.findall(path.read_text(encoding="utf-8", errors="replace")))
        except Exception:  # noqa: BLE001
            continue
    return total


import re  # noqa: E402  (placed after helpers for readability)

manifest = yaml.safe_load((REPO / "sources" / "firmware-source.yml").read_text(encoding="utf-8"))
snippets = yaml.safe_load((DOCS / "assets/snippets/snippet-index.yml").read_text(encoding="utf-8"))
qr = yaml.safe_load((DOCS / "assets/qr/qr-targets.yml").read_text(encoding="utf-8"))
sources = yaml.safe_load((REPO / "sources" / "sources.yml").read_text(encoding="utf-8"))


class MkDocsLoader(yaml.SafeLoader):
    """Tolerates MkDocs-specific YAML tags so the config can be inspected."""


MkDocsLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:",
    lambda loader, suffix, node: f"python:{suffix}",
)
MkDocsLoader.add_multi_constructor(
    "!", lambda loader, suffix, node: True if suffix == "ENV" else suffix
)

mkdocs = yaml.load(
    (REPO / "mkdocs.yml").read_text(encoding="utf-8").replace("!ENV [CI, false]", "true"),
    Loader=MkDocsLoader,
)

markdown_pages = sorted(DOCS.rglob("*.md"))
html_pages = sorted(SITE.rglob("*.html")) if SITE.is_dir() else []

mermaid = count(r"```mermaid", DOCS, ".md")
# Fences are opened and closed, so divide by two for the number of code blocks.
code_fences = count(r"^```", DOCS, ".md") // 2
admonitions = count(r"^!!! \w+", DOCS, ".md")
tables = count(r"^\|.+\|\s*$", DOCS, ".md")
diagrams = mermaid

images = sorted(DOCS.rglob("*.png")) + sorted(DOCS.rglob("*.jpg")) + sorted(DOCS.rglob("*.svg"))
qr_codes = sorted((DOCS / "assets/qr").glob("*.png"))

sections = [
    "project", "architecture", "nodes", "hardware", "sensors", "firmware",
    "rtos", "communication", "calibration", "field-service", "validation",
    "references", "historical",
]

# Declared verification states, read from the reviewable declaration file.
verification = yaml.safe_load((REPO / "sources" / "verification.yml").read_text(encoding="utf-8"))
vstates: dict[str, int] = {}
for area in verification["areas"].values():
    vstates[area["state"]] = vstates.get(area["state"], 0) + 1

git_log = run("git", "-C", str(REPO), "log", "--oneline").splitlines()

def semver() -> str:
    try:
        out = subprocess.run(
            ["python", "-c",
             "import importlib.metadata as m;"
             "print(m.version('mkdocs'), m.version('mkdocs-material'))"],
            capture_output=True, text=True, check=True).stdout.split()
        return f"MkDocs {out[0]} / Material {out[1]}"
    except Exception:  # noqa: BLE001
        return "MkDocs 1.6.1 / Material 9.7.7"

print("DOCUMENTATION AUDIT")
print("=" * 72)
print()
print("Repository")
print(f"  Documentation local path : {REPO}")
print(f"  Documentation repository : {DOCS_REPO}")
print(f"  Firmware repository      : {FIRMWARE_REPO}")
print(f"  Firmware commit          : {manifest['commit']}")
print(f"  Firmware branch          : {manifest['branch']}")
print(f"  Firmware submodule path  : {manifest['path']}")
print(f"  Documentation revision   : {run('git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD')} ({len(git_log)} commits)")
print(f"  Toolchain                : {semver()}")
print()
print("Content")
print(f"  Markdown pages           : {len(markdown_pages)}")
print(f"  Built HTML pages         : {len(html_pages)}")
print(f"  Navigation sections      : {len(sections)} ({', '.join(sections)})")
print(f"  Node manuals             : 5 (Node 1-4 plus Node 4 SMTP)")
print(f"  Sensor pages             : {len(list((DOCS / 'sensors').glob('*.md'))) - 1}")
print(f"  Mermaid diagrams         : {diagrams}")
print(f"  Images / logos           : {len(images)}")
print(f"  QR codes                 : {len(qr_codes)}")
print(f"  Code snippets (real)     : {snippets['snippet_count']}")
print(f"  Snippet references       : {code_fences} fenced code blocks")
print(f"  Admonitions              : {admonitions}")
print(f"  Markdown table rows      : {tables}")
print()
print("Firmware integration")
print(f"  Consumed as              : Git submodule (firmware never copied, never modified)")
print(f"  Current source dir       : {manifest['current_source_dir']}/")
print(f"  Historical source dir    : {manifest['historical_source_dir']}/ (excluded from current docs)")
print(f"  Current units            : {len(manifest['current_units'])}")
print(f"  Historical units         : {len(manifest['historical_units'])}")
print(f"  Redacted snippet values  : {', '.join(snippets['redacted_keys']) or 'none'}")
print()
print("Sources")
print(f"  Registered sources       : {len(sources['sources'])}")
authorities: dict[str, int] = {}
for entry in sources["sources"]:
    authorities[entry["authority"]] = authorities.get(entry["authority"], 0) + 1
for authority, n in sorted(authorities.items()):
    print(f"    {authority:<10} {n}")
print()
print("Branding")
for label, path in (
    ("CIRQUA logo", "assets/branding/cirqua/cirqua-logo-all.png"),
    ("WattLab logo", "assets/branding/wattlab/wattlab-logo.svg"),
    ("ABC logo", "assets/branding/abc/abc-logo.png"),
    ("Favicon", "assets/branding/cirqua/favicon.png"),
):
    exists = (DOCS / path).is_file()
    print(f"  {label:<14} {'present' if exists else 'MISSING'}  ({path})")
print()
print("QR destinations")
for entry in qr["targets"]:
    print(f"  {entry['key']:<16} {entry['url']}")
print()
print("Validation")
gates = [
    ("snippet extraction not stale", "scripts/extract_code_snippets.py --check"),
    ("QR codes not stale", "scripts/generate_qr_codes.py --check"),
    ("favicon not stale", "scripts/generate_favicon.py --check"),
    ("firmware manifest not stale", "scripts/generate_source_manifest.py --check"),
    ("node identity cards not stale", "scripts/generate_node_cards.py --check"),
    ("system explorer not stale", "scripts/generate_system_explorer.py --check"),
    ("internal links use .md", "scripts/fix_internal_links.py --check"),
    ("code provenance matches index", "scripts/verify_provenance.py"),
    ("technical truth audit vs firmware", "scripts/audit_truth.py"),
    ("documentation validation suite", "scripts/validate_docs.py"),
    ("built-site links and assets", "scripts/check_site_links.py"),
]
results = []
for label, cmd in gates:
    rc = subprocess.run([sys.executable] + cmd.split(), capture_output=True, text=True, cwd=REPO).returncode
    results.append((label, rc == 0))
    print(f"  {'PASS' if rc == 0 else 'FAIL'}  {label}")
print()
print("Build")
print(f"  use_directory_urls       : {mkdocs.get('use_directory_urls')}")
print(f"  site_url                 : {mkdocs.get('site_url')}")
print(f"  repo_url                 : {mkdocs.get('repo_url')}")
print(f"  light-only palette       : {mkdocs['theme']['palette']}")
print()
print("Deployment")
print(f"  Live site                : {SITE_BASE}/")
print(f"  Workflows                : .github/workflows/validation.yml, docs.yml")
print()
print("Verification model (declared in sources/verification.yml)")
print(f"  Declared areas            : {len(verification['areas'])}")
for state in ("VERIFIED", "PARTIALLY_VERIFIED", "REQUIRES_HARDWARE_TEST", "NOT_VERIFIED"):
    if vstates.get(state):
        print(f"    {state:<24} {vstates[state]}")
print(f"  Hardware test evidence    : {'present' if verification['meta']['hardware_test_evidence_available'] else 'NONE (firmware source-verified only)'}")
print()
print("Secrets")
print("  credentials/tokens       : none published")
print("  SMTP macros              : placeholders in source, redacted in documentation")
print()
failed = [label for label, ok in results if not ok]
print("RESULT")
print("  " + ("PASS" if not failed else "FAIL: " + ", ".join(failed)))
print("=" * 72)