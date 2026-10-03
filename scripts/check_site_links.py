"""Crawl the built site and verify every internal link and asset resolves.

Operates on the built HTML in site/ (or takes a base URL to probe the deployed
site). This catches broken links that source-level validation cannot, such as a
link emitted by a template or a missing asset referenced from a template.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

SITE = Path("site")

HREF = re.compile(r'href="?([^"\s>]*)"?', re.IGNORECASE)
SRC = re.compile(r'src="?([^"\s>]*)"?', re.IGNORECASE)

SKIP_SCHEMES = ("mailto:", "tel:", "data:", "javascript:", "#")

# GitHub Pages serves this project from a subdirectory, so templates emit
# site-root-relative URLs such as /Cirqua-documentation/assets/... Those are
# correct when deployed; when checking the built tree they must have the base
# path stripped before resolving against site/.
SITE_BASE_PATH = "/Cirqua-documentation/"


def main() -> int:
    if not SITE.is_dir():
        sys.exit("site/ not found - run: mkdocs build")

    html_files = sorted(SITE.rglob("*.html"))
    broken: list[str] = []
    checked = 0

    for page in html_files:
        text = page.read_text(encoding="utf-8", errors="replace")
        page_rel = page.relative_to(SITE).as_posix()

        for pattern, kind in ((HREF, "link"), (SRC, "asset")):
            for match in pattern.finditer(text):
                target = match.group(1)
                if not target or target.startswith(SKIP_SCHEMES):
                    continue
                if target.startswith("http://") or target.startswith("https://"):
                    continue  # external, checked separately

                # Resolve against the page URL within the site.
                base = urlparse(f"https://local/{page_rel}")
                resolved = urlparse(urljoin(base.geturl(), target))
                clean = resolved.path.lstrip("/")

                # Strip the GitHub Pages base path so root-relative URLs
                # (emitted by templates for the 404 page) resolve locally.
                if clean.startswith(SITE_BASE_PATH.lstrip("/")):
                    clean = clean[len(SITE_BASE_PATH.lstrip("/")) :]
                checked += 1

                candidate = SITE / clean
                ok = candidate.is_file()
                if not ok and clean.endswith("/"):
                    ok = (SITE / clean / "index.html").is_file()
                if not ok and not resolved.path.endswith((".html", "/")):
                    alt = SITE / (clean + ".html")
                    ok = alt.is_file()
                if not ok:
                    alt2 = SITE / clean / "index.html"
                    ok = alt2.is_file()

                if not ok:
                    broken.append(f"{page_rel}: {kind} -> {target}")

    print(f"html pages crawled : {len(html_files)}")
    print(f"internal refs      : {checked}")
    print(f"broken             : {len(set(broken))}")

    for item in sorted(set(broken))[:40]:
        print(f"  BROKEN {item}")

    print("\nRESULT: " + ("FAIL" if broken else "PASS - every internal link and asset resolves"))
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())