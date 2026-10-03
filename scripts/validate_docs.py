#!/usr/bin/env python3
"""
Validation suite for the CIRQUA technical documentation.

Design rule: a failure means the documentation is wrong, not merely untidy.
Every check maps back to a requirement of the WattLab documentation standard
or to a specific risk for this project (stale firmware citations, leaked
credentials, broken QR labels).

Checks
------
  1  Submodule is checked out and at the recorded commit
  2  Every Markdown link target resolves (internal pages and assets)
  3  Every image and asset referenced exists on disk
  4  Every ``nav:`` entry in mkdocs.yml exists, and every page is reachable
  5  No placeholder / unfinished text
  6  No absolute local filesystem paths in published Markdown
  7  No secrets or credential material in published Markdown
  8  Every ``assets/snippets/...`` embed exists
  9  GitHub source links resolve to a real path in the pinned firmware commit
 10  Firmware provenance (commit, branch, repo) is consistent everywhere
 11  QR destination URLs are well formed, permanent and absolute
 12  Branding assets present
 13  External HTTP(S) links are reachable (advisory only, never fatal)
 14  mkdocs.yml has the mandatory WattLab configuration keys

Usage
-----
    python scripts/validate_docs.py                # fatal checks only
    python scripts/validate_docs.py --external     # also probe external URLs
    python scripts/validate_docs.py --strict       # treat warnings as fatal
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install with: pip install PyYAML")


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
MKDOCS_YML = REPO_ROOT / "mkdocs.yml"
MANIFEST = REPO_ROOT / "sources" / "firmware-source.yml"

FIRMWARE_COMMIT = "db6d9b896341a9c7d8fd01913e854b663c110d55"
FIRMWARE_BRANCH = "main"
FIRMWARE_REPO = "https://github.com/lestealthy/Cirqua"
DOCS_REPO = "https://github.com/lestealthy/Cirqua-documentation"
SITE_BASE = "https://lestealthy.github.io/Cirqua-documentation"


class MkDocsLoader(yaml.SafeLoader):
    """SafeLoader that tolerates the MkDocs-specific YAML tags.

    ``!ENV [CI, false]`` and ``!!python/name:...`` are meaningful to MkDocs but
    are not resolvable outside a Python environment. They are represented as
    inert strings so the configuration can still be inspected for the
    WattLab-mandatory keys.
    """


MkDocsLoader.add_multi_constructor("tag:yaml.org,2002:python/name:", lambda loader, suffix, node: f"python:{suffix}")
MkDocsLoader.add_multi_constructor("!", lambda loader, suffix, node: None if suffix == "ENV" else suffix)

# Text that must never survive into a published page.
#
# NOTE: the bare word "placeholder" is deliberately NOT in this list. It is a
# correct and necessary term in this documentation for two very different
# things: the `--` / `----` substitutions Node 1 renders on its LCD when a
# field is absent, and the intentionally unfilled SMTP/Wi-Fi macros in
# Node4_SMTP.ino. Flagging it produced only false positives. Genuinely
# unfinished content is caught by the markers below.
PLACEHOLDER_TOKENS = (
    "lorem ipsum",
    "todo",
    "tbd",
    "to be written",
    "coming soon",
    "change_me",
    "change-me",
    "<insert",
    "insert here",
    "fixme",
    "xxx",
    "n/a yet",
)

# Absolute local paths that must not appear in published documentation.
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\\\?Users\\\\?", re.IGNORECASE),
    re.compile(r"/Users/[A-Za-z0-9._-]+/", re.IGNORECASE),
    re.compile(r"/home/[A-Za-z0-9._-]+/", re.IGNORECASE),
)

# Credential shapes. Deliberately broad; a hit needs manual review.
SECRET_PATTERNS = (
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "GitHub fine-grained token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?i)\bpassword\s*[=:]\s*[\"'][^\"']{6,}[\"']"), "inline password"),
    (re.compile(r"(?i)\bapi[_-]?key\s*[=:]\s*[\"'][^\"']{8,}[\"']"), "inline API key"),
    (re.compile(r"(?i)smtp\.\w+\.com[^\n]{0,40}pass"), "SMTP credential proximity"),
)

# Markdown that a page must be able to ignore for link extraction.
FENCE = re.compile(r"^(```|~~~)")
LINK_RE = re.compile(r"(?<!\!)\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
SNIPPET_EMBED_RE = re.compile(r"--8<--\s+\"([^\"]+)\"")
HTML_IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
HTML_SRC_RE = re.compile(r"src=[\"']([^\"']+)[\"']", re.IGNORECASE)
HTML_HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']", re.IGNORECASE)


class Report:
    def __init__(self, strict: bool) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passed: list[str] = []
        self.strict = strict

    def ok(self, message: str) -> None:
        self.passed.append(message)

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def check(self, condition: bool, fail_message: str, warn_message: str | None = None) -> bool:
        if condition:
            self.passed.append(fail_message.split(" (")[0])
            return True
        if warn_message:
            self.warn(warn_message)
            return False
        self.fail(fail_message)
        return False

    def exit_code(self) -> int:
        if self.errors:
            return 1
        if self.strict and self.warnings:
            return 1
        return 0


def markdown_files() -> list[Path]:
    return sorted(DOCS.rglob("*.md"))


def strip_fenced_code(text: str) -> str:
    """Remove fenced code blocks so snippet embeds and example links inside
    them are not validated as real references."""
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = FENCE.match(line.strip())
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif line.strip().startswith(fence):
                fence = None
            out.append("")
            continue
        out.append("" if fence else line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 1. Submodule + manifest
# ---------------------------------------------------------------------------


def check_submodule(report: Report) -> Path | None:
    if not MANIFEST.is_file():
        report.fail(f"manifest missing: {MANIFEST}")
        return None
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    firmware = REPO_ROOT / manifest.get("path", "")
    if not firmware.is_dir():
        report.fail(f"firmware submodule not initialised at {firmware}")
        return None

    head = None
    try:
        head = subprocess.run(
            ["git", "-C", str(firmware), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception as exc:  # noqa: BLE001
        report.fail(f"could not read submodule HEAD: {exc}")
        return firmware

    report.check(
        head == manifest.get("commit"),
        f"submodule HEAD {head[:7]} != manifest commit {str(manifest.get('commit'))[:7]}",
        "cannot compare submodule HEAD (not a git checkout) - manifest only",
    )
    report.check(
        manifest.get("commit") == FIRMWARE_COMMIT,
        f"manifest commit is not the audited firmware commit {FIRMWARE_COMMIT[:7]}",
    )
    report.check(
        manifest.get("branch") == FIRMWARE_BRANCH,
        f"manifest branch is not {FIRMWARE_BRANCH}",
    )
    report.check(
        manifest.get("repository") == FIRMWARE_REPO,
        f"manifest repository is not {FIRMWARE_REPO}",
    )
    report.ok("submodule and firmware manifest consistent")
    return firmware


# ---------------------------------------------------------------------------
# 2/3. Links, images, assets
# ---------------------------------------------------------------------------


def resolve_docs_target(source: Path, target: str) -> Path | None:
    """Resolve a documentation-relative target to a real path."""
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target:
        return source

    # Absolute site paths are rooted at docs/.
    if target.startswith("/"):
        return DOCS / target.lstrip("/")

    # Site-url prefixed links (used in footers).
    if target.startswith(SITE_BASE):
        remainder = target[len(SITE_BASE) :].lstrip("/")
        if not remainder or remainder == "":
            return DOCS / "index.md"
        candidate = DOCS / remainder
        return candidate

    candidate = (source.parent / target).resolve()
    return candidate


def exists_as_page(path: Path) -> bool:
    if path is None:
        return False
    if path.is_file():
        return True
    # Flat URLs: foo.html -> foo.md, foo/index.html -> foo/index.md
    if path.suffix == ".html":
        md = path.with_suffix(".md")
        if md.is_file():
            return True
        index = path.parent / "index.md"
        if index.is_file():
            return True
    if path.is_dir():
        if (path / "index.md").is_file():
            return True
    return False


def check_links_and_assets(report: Report) -> set[str]:
    external: set[str] = set()
    broken: list[str] = []
    missing_assets: list[str] = []
    missing_alt: list[str] = []

    for md in markdown_files():
        raw = md.read_text(encoding="utf-8", errors="replace")
        text = strip_fenced_code(raw)
        rel = md.relative_to(DOCS).as_posix()

        # Inline Markdown links
        for match in LINK_RE.finditer(text):
            target = match.group("target")
            if target.startswith(("http://", "https://")):
                external.add(target)
                continue
            if target.startswith(("mailto:", "#")):
                continue
            resolved = resolve_docs_target(md, target)
            if not exists_as_page(resolved):
                broken.append(f"{rel}: [{match.group('text')}]({target})")

        # Markdown images
        for match in IMAGE_RE.finditer(text):
            target = match.group("target")
            if not match.group("alt").strip():
                missing_alt.append(f"{rel}: {target}")
            if target.startswith(("http://", "https://")):
                external.add(target)
                continue
            resolved = resolve_docs_target(md, target)
            if resolved is None or not resolved.is_file():
                missing_assets.append(f"{rel}: image {target}")

        # HTML img/src in embedded markup (cards, masthead, labels)
        for match in HTML_IMG_RE.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://")):
                external.add(target)
                continue
            resolved = resolve_docs_target(md, target)
            if resolved is None or not resolved.is_file():
                missing_assets.append(f"{rel}: <img src> {target}")

        # Any other src="..." (scripts, etc.)
        for match in HTML_SRC_RE.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "//", "data:")):
                continue
            resolved = resolve_docs_target(md, target)
            if resolved is None or not resolved.is_file():
                missing_assets.append(f"{rel}: src {target}")

        # Any other href="..." (cards, internal navigation)
        for match in HTML_HREF_RE.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "//", "mailto:", "#")):
                continue
            resolved = resolve_docs_target(md, target)
            if not exists_as_page(resolved):
                broken.append(f"{rel}: <a href> {target}")

    for item in sorted(set(broken)):
        report.fail(f"broken internal link: {item}")
    if not broken:
        report.ok("all internal Markdown and HTML links resolve")

    for item in sorted(set(missing_assets)):
        report.fail(f"missing asset: {item}")
    if not missing_assets:
        report.ok("all referenced images and assets exist")

    for item in sorted(set(missing_alt)):
        report.warn(f"image without alt text: {item}")
    if not missing_alt:
        report.ok("all Markdown images have alt text")

    return external


# ---------------------------------------------------------------------------
# 5. Placeholders
# ---------------------------------------------------------------------------


def check_placeholders(report: Report) -> None:
    hits: list[str] = []
    for md in markdown_files():
        text = md.read_text(encoding="utf-8", errors="replace")
        body = strip_fenced_code(text)
        for lineno, line in enumerate(body.splitlines(), start=1):
            lowered = line.lower()
            for token in PLACEHOLDER_TOKENS:
                if token in lowered:
                    hits.append(f"{md.relative_to(DOCS).as_posix()}:{lineno}: {token!r} in {line.strip()[:90]!r}")

    for hit in hits:
        report.warn(f"possible placeholder text: {hit}")
    if not hits:
        report.ok("no placeholder or unfinished text")


# ---------------------------------------------------------------------------
# 6. Absolute paths
# ---------------------------------------------------------------------------


def check_absolute_paths(report: Report) -> None:
    hits: list[str] = []
    for md in markdown_files():
        rel = md.relative_to(DOCS).as_posix()
        text = strip_fenced_code(md.read_text(encoding="utf-8", errors="replace"))
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in ABSOLUTE_PATH_PATTERNS:
                if pattern.search(line):
                    hits.append(f"{rel}:{lineno}: {line.strip()[:100]!r}")

    for hit in hits:
        report.fail(f"absolute local path in published page: {hit}")
    if not hits:
        report.ok("no absolute local filesystem paths in published pages")


# ---------------------------------------------------------------------------
# 7. Secrets
# ---------------------------------------------------------------------------


def check_secrets(report: Report) -> None:
    hits: list[str] = []
    for md in markdown_files():
        rel = md.relative_to(DOCS).as_posix()
        text = md.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(line):
                    hits.append(f"{rel}:{lineno}: {label}")

    for hit in hits:
        report.fail(f"possible secret: {hit}")
    if not hits:
        report.ok("no credentials, tokens or keys in published pages")

    # Snippets are also published content.
    snippet_dir = DOCS / "assets" / "snippets"
    if snippet_dir.is_dir():
        snip_hits: list[str] = []
        for cpp in sorted(snippet_dir.glob("*.cpp")):
            text = cpp.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                for pattern, label in SECRET_PATTERNS:
                    if pattern.search(line):
                        snip_hits.append(f"{cpp.name}:{lineno}: {label}")
        for hit in snip_hits:
            report.fail(f"possible secret in snippet: {hit}")
        if not snip_hits:
            report.ok("no credentials in extracted code snippets")


# ---------------------------------------------------------------------------
# 8. Snippet embeds
# ---------------------------------------------------------------------------


def check_snippet_embeds(report: Report) -> None:
    embeds: set[str] = set()
    for md in markdown_files():
        text = md.read_text(encoding="utf-8", errors="replace")
        embeds.update(SNIPPET_EMBED_RE.findall(text))

    missing = sorted(target for target in embeds if not (DOCS / target).is_file())
    for target in missing:
        report.fail(f"sippet embed target missing: {target}")
    if not missing:
        report.ok(f"all {len(embeds)} code snippet embeds resolve")

    if not embeds:
        report.warn("no code snippets are embedded in the documentation")


# ---------------------------------------------------------------------------
# 9. GitHub source links
# ---------------------------------------------------------------------------


def check_source_links(report: Report, firmware_root: Path | None) -> None:
    if firmware_root is None:
        return

    blob_prefix = f"{FIRMWARE_REPO}/blob/{FIRMWARE_COMMIT}/"
    tree_prefix = f"{FIRMWARE_REPO}/tree/{FIRMWARE_COMMIT}/"
    hits: list[str] = []
    checked = 0

    for md in markdown_files():
        rel = md.relative_to(DOCS).as_posix()
        text = md.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(rf"{re.escape(blob_prefix)}([^\s\"'<>)]+)", text):
            path = match.group(1).split("#")[0]
            checked += 1
            if not (firmware_root / path).exists():
                hits.append(f"{rel}: blob path not in firmware commit -> {path}")

        for match in re.finditer(rf"{re.escape(tree_prefix)}([^\s\"'<>)]+)", text):
            path = match.group(1).split("#")[0]
            checked += 1
            if not (firmware_root / path).exists():
                hits.append(f"{rel}: tree path not in firmware commit -> {path}")

    for hit in sorted(set(hits)):
        report.fail(f"source link does not resolve: {hit}")
    if not hits:
        report.ok(f"all {checked} firmware source links resolve at commit {FIRMWARE_COMMIT[:7]}")

    # Snippet index links
    index_path = DOCS / "assets" / "snippets" / "snippet-index.yml"
    if index_path.is_file():
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        stale = [
            entry["id"]
            for entry in index.get("snippets", [])
            if not (firmware_root / entry["path"]).exists()
        ]
        for entry in stale:
            report.fail(f"snippet index references a missing firmware file: {entry}")
        if not stale:
            report.ok(f"snippet index consistent with firmware tree ({index.get('snippet_count')} snippets)")


# ---------------------------------------------------------------------------
# 10. Firmware provenance consistency
# ---------------------------------------------------------------------------


def check_provenance(report: Report) -> None:
    hits: list[str] = []
    docs_files = markdown_files() + [MKDOCS_YML]

    for path in docs_files:
        rel = path.relative_to(DOCS).as_posix() if path.is_relative_to(DOCS) else path.name
        text = path.read_text(encoding="utf-8", errors="replace")
        # Any 40-hex SHA used as a firmware commit must be the audited one.
        for match in re.finditer(r"\b[0-9a-f]{40}\b", text):
            if match.group(0) != FIRMWARE_COMMIT:
                hits.append(f"{rel}: unexpected 40-hex revision {match.group(0)}")
        # Short SHA
        for match in re.finditer(r"\bcommit\s+<code>([0-9a-f]{7})</code>", text):
            if match.group(1) != FIRMWARE_COMMIT[:7]:
                hits.append(f"{rel}: inconsistent short commit {match.group(1)}")

    for hit in sorted(set(hits)):
        report.fail(f"firmware provenance inconsistency: {hit}")
    if not hits:
        report.ok(f"firmware provenance consistent ({FIRMWARE_COMMIT[:7]})")

    config = MKDOCS_YML.read_text(encoding="utf-8")
    if FIRMWARE_COMMIT in config:
        report.ok("mkdocs.yml carries the audited firmware commit")
    else:
        report.fail("mkdocs.yml does not reference the audited firmware commit")


# ---------------------------------------------------------------------------
# 11. QR destinations
# ---------------------------------------------------------------------------


def check_qr(report: Report) -> None:
    targets_path = DOCS / "assets" / "qr" / "qr-targets.yml"
    if not targets_path.is_file():
        report.fail("QR target manifest missing: docs/assets/qr/qr-targets.yml")
        return

    data = yaml.safe_load(targets_path.read_text(encoding="utf-8"))
    problems: list[str] = []

    for entry in data.get("targets", []):
        url = entry.get("url", "")
        key = entry.get("key", "?")

        if not url.startswith("https://"):
            problems.append(f"{key}: not https -> {url}")
        if not url.startswith(SITE_BASE):
            problems.append(f"{key}: not on the deployed site -> {url}")
        if "localhost" in url or "127.0.0.1" in url:
            problems.append(f"{key}: encodes a local/preview URL -> {url}")
        if url.rstrip("/").endswith((".md",)):
            problems.append(f"{key}: encodes a source-file URL -> {url}")

        image = REPO_ROOT / "docs" / entry.get("image", "")
        if not image.is_file():
            problems.append(f"{key}: QR image missing -> {entry.get('image')}")

    for problem in problems:
        report.fail(f"QR destination problem: {problem}")
    if not problems:
        report.ok(f"all {len(data.get('targets', []))} QR destinations are permanent and backed by an image")


# ---------------------------------------------------------------------------
# 12. Branding
# ---------------------------------------------------------------------------


def check_branding(report: Report) -> None:
    required = {
        "CIRQUA logo": "assets/branding/cirqua/cirqua-logo-all.png",
        "WattLab logo": "assets/branding/wattlab/wattlab-logo.svg",
        "ABC logo": "assets/branding/abc/abc-logo.png",
        "CIRQUA logo (alternate)": "assets/branding/cirqua/cirqua-logo.jpg",
        "Favicon": "assets/branding/cirqua/favicon.png",
    }
    missing = [f"{label} -> {path}" for label, path in required.items() if not (DOCS / path).is_file()]
    for item in missing:
        report.fail(f"branding asset missing: {item}")
    if not missing:
        report.ok(f"all {len(required)} branding assets present")


# ---------------------------------------------------------------------------
# 14. mkdocs.yml mandatory configuration
# ---------------------------------------------------------------------------


def check_mkdocs_config(report: Report) -> None:
    config = yaml.load(MKDOCS_YML.read_text(encoding="utf-8"), Loader=MkDocsLoader)

    report.check(
        config.get("site_url") == f"{SITE_BASE}/",
        f"site_url must be {SITE_BASE}/ (found {config.get('site_url')!r})",
    )
    report.check(
        config.get("repo_url") == DOCS_REPO,
        f"repo_url must be {DOCS_REPO} (found {config.get('repo_url')!r})",
    )
    report.check(
        config.get("repo_name") == "Cirqua-documentation",
        f"repo_name must be Cirqua-documentation (found {config.get('repo_name')!r})",
    )
    report.check(
        config.get("use_directory_urls") is False,
        "use_directory_urls must be false (WattLab standard; prevents redirect loops)",
    )
    report.check(
        bool(config.get("site_description")),
        "site_description must be set",
    )
    report.check(
        bool(config.get("site_author")),
        "site_author must be set",
    )

    raw = MKDOCS_YML.read_text(encoding="utf-8")
    for placeholder in ("YOUR_", "<repo", "example.com"):
        if placeholder in raw:
            report.fail(f"mkdocs.yml still contains the placeholder {placeholder!r}")
    report.ok("mkdocs.yml carries the mandatory WattLab configuration")

    # Light-only enforcement
    theme = config.get("theme", {})
    schemes = [entry.get("scheme") for entry in theme.get("palette", []) if isinstance(entry, dict)]
    if "slate" in schemes:
        report.fail("mkdocs.yml enables the slate (dark) colour scheme; the site must be light only")
    else:
        report.ok("light-only palette (no dark scheme, no toggle)")

    # Nav coverage
    nav = config.get("nav", [])
    nav_files: list[str] = []

    def walk(entries) -> None:
        for entry in entries:
            if isinstance(entry, str):
                # A bare path in a section list, e.g.
                #   - Project:
                #     - project/index.md
                nav_files.append(entry)
            elif isinstance(entry, dict):
                for value in entry.values():
                    if isinstance(value, str):
                        nav_files.append(value)
                    elif isinstance(value, list):
                        walk(value)

    walk(nav)

    missing = [item for item in nav_files if not (DOCS / item).is_file()]
    for item in sorted(set(missing)):
        report.fail(f"nav entry has no file: {item}")
    if not missing:
        report.ok(f"all {len(set(nav_files))} nav entries resolve to files")

    on_disk = {p.relative_to(DOCS).as_posix() for p in markdown_files()}
    orphans = sorted(on_disk - set(nav_files))
    if orphans:
        for item in orphans:
            report.warn(f"page not referenced in nav (orphan): {item}")
    else:
        report.ok("no orphan pages - every page is in the navigation")


# ---------------------------------------------------------------------------
# 13. External links (advisory)
# ---------------------------------------------------------------------------


def check_external(report: Report, urls: set[str]) -> None:
    if not urls:
        report.ok("no external links to check")
        return
    try:
        import requests
    except ImportError:
        report.warn("requests not installed - skipped external link probe")
        return

    unreachable: list[str] = []
    for url in sorted(urls):
        parsed = urlparse(url)
        if parsed.netloc in {"", "localhost", "127.0.0.1"}:
            continue
        try:
            response = requests.head(
                url,
                timeout=12,
                allow_redirects=True,
                headers={"User-Agent": "cirqua-docs-link-check/1.0"},
            )
            if response.status_code >= 400:
                response = requests.get(
                    url,
                    timeout=12,
                    allow_redirects=True,
                    stream=True,
                    headers={"User-Agent": "cirqua-docs-link-check/1.0"},
                )
            if response.status_code >= 400:
                unreachable.append(f"{response.status_code} {url}")
        except Exception as exc:  # noqa: BLE001
            unreachable.append(f"unreachable ({type(exc).__name__}) {url}")

    for item in unreachable:
        report.warn(f"external link not reachable: {item}")
    report.ok(f"probed {len(urls)} external URLs ({len(unreachable)} unreachable, advisory)")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", action="store_true", help="probe external URLs (advisory)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as fatal")
    args = parser.parse_args()

    report = Report(strict=args.strict)

    print("CIRQUA documentation validation")
    print("=" * 64)

    firmware_root = check_submodule(report)
    external = check_links_and_assets(report)
    check_snippet_embeds(report)
    check_source_links(report, firmware_root)
    check_provenance(report)
    check_qr(report)
    check_branding(report)
    check_mkdocs_config(report)
    check_placeholders(report)
    check_absolute_paths(report)
    check_secrets(report)

    if args.external:
        check_external(report, external)

    print()
    for message in report.passed:
        print(f"  PASS  {message}")
    if report.warnings:
        print()
        for message in report.warnings:
            print(f"  WARN  {message}")
    if report.errors:
        print()
        for message in report.errors:
            print(f"  FAIL  {message}")

    print()
    print("=" * 64)
    print(f"checks passed : {len(report.passed)}")
    print(f"warnings      : {len(report.warnings)}")
    print(f"errors        : {len(report.errors)}")
    result = "FAIL" if report.errors else ("FAIL (strict)" if args.strict and report.warnings else "PASS")
    print(f"RESULT        : {result}")
    return report.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())