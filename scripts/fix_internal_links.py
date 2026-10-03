#!/usr/bin/env python3
"""Normalise internal documentation links to ``.md`` sources.

Why this exists
---------------
The site is built with ``use_directory_urls: false``, so a source file
``nodes/node1.md`` is published as ``nodes/node1.html``. That means the
correct URL in a *Markdown* link is ``nodes/node1.md``: MkDocs rewrites it to
``nodes/node1.html`` in the built site. Writing ``.html`` in the source is
what produces the "Did you mean 'nodes/node1.md'?" warnings that would fail
``mkdocs build --strict``.

Rules applied
-------------
* Markdown links ``[text](target.html)`` become ``[text](target.md)`` ONLY when
  the target resolves to a real documentation page.
* Absolute ``https://``/``http://`` links are never touched, including the
  deployed ``.html`` URLs that the QR-code page deliberately publishes.
* Links inside fenced code blocks are never touched.
* Raw HTML ``href="..."`` / ``src="..."`` attributes are never touched, because
  MkDocs does not rewrite them - they must keep the real ``.html`` suffix.

Usage
-----
    python scripts/fix_internal_links.py
    python scripts/fix_internal_links.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

FENCE = re.compile(r"^(```|~~~)")
MD_LINK = re.compile(r"(?<!!)(\[[^\]]*\])\(([^)\s]+)(\s+\"[^\"]*\")?\)")
HTML_ATTR = re.compile(r"(?:href|src)\s*=\s*[\"']", re.IGNORECASE)

SKIP_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:", "#", "data:")


def split_fences(text: str) -> list[tuple[bool, str]]:
    """Return (is_code, line) pairs so code blocks can be left untouched."""
    out: list[tuple[bool, str]] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        match = FENCE.match(stripped)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif stripped.startswith(fence):
                fence = None
            out.append((True, line))
            continue
        out.append((fence is not None, line))
    return out


def page_exists(source: Path, base: str) -> bool:
    """True when `base` (a relative path) resolves to a real documentation page."""
    if not base.endswith(".html"):
        return False
    candidate_md = base[: -len(".html")] + ".md"

    if base.startswith("/"):
        resolved = DOCS / candidate_md.lstrip("/")
    else:
        resolved = (source.parent / candidate_md).resolve()

    return resolved.is_file()


def convert(source: Path, line: str) -> tuple[str, int]:
    if HTML_ATTR.search(line):
        return line, 0

    changed = 0

    def repl(match: re.Match) -> str:
        nonlocal changed
        label, target, title = match.group(1), match.group(2), match.group(3) or ""
        if target.startswith(SKIP_PREFIXES):
            return match.group(0)

        # Split off the anchor fragment, then any query string. Both must be
        # preserved verbatim; only the path component is rewritten.
        path, hash_sep, fragment = target.partition("#")
        path, query_sep, query = path.partition("?")
        suffix = query_sep + query + hash_sep + fragment

        if not page_exists(source, path):
            return match.group(0)

        changed += 1
        new_path = path[: -len(".html")] + ".md"
        return f"{label}({new_path}{suffix}{title})"

    return MD_LINK.sub(repl, line), changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report remaining .html links and exit 1")
    args = parser.parse_args()

    total_changed = 0
    touched: list[str] = []

    for md in sorted(DOCS.rglob("*.md")):
        original = md.read_text(encoding="utf-8")
        pieces = split_fences(original)
        out: list[str] = []
        file_changes = 0

        for is_code, line in pieces:
            if is_code:
                out.append(line)
                continue
            new_line, changed = convert(md, line)
            file_changes += changed
            out.append(new_line)

        rebuilt = "".join(out)

        if rebuilt != original and not args.check:
            md.write_text(rebuilt, encoding="utf-8")

        if file_changes:
            total_changed += file_changes
            touched.append(f"{md.relative_to(DOCS).as_posix()} ({file_changes})")

    if args.check:
        remaining: list[str] = []
        for md in sorted(DOCS.rglob("*.md")):
            for is_code, line in split_fences(md.read_text(encoding="utf-8")):
                if is_code or HTML_ATTR.search(line):
                    continue
                for match in MD_LINK.finditer(line):
                    target = match.group(2)
                    if target.startswith(SKIP_PREFIXES):
                        continue
                    path = target.partition("#")[0]
                    if path.endswith(".html"):
                        remaining.append(f"{md.relative_to(DOCS).as_posix()}: {target}")
        for item in remaining:
            print(f"  still .html: {item}")
        if remaining:
            print(f"\n{len(remaining)} Markdown links still use .html")
            return 1
        print("OK - all internal Markdown links use .md sources")
        return 0

    print(f"links rewritten: {total_changed}")
    for item in touched:
        print(f"  {item}")
    if not total_changed:
        print("nothing to rewrite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())