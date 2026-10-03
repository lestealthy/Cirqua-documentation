#!/usr/bin/env python3
"""
Generate the CIRQUA favicon set from the official project logo.

The favicon is derived mechanically from the official logo asset. It is only
resized and cropped - never redrawn, recoloured or distorted - so brand
integrity is preserved.

Outputs
-------
    docs/assets/branding/cirqua/favicon.png          64x64  (mkdocs favicon)
    docs/assets/branding/cirqua/apple-touch-icon.png 180x180

Usage
-----
    python scripts/generate_favicon.py
    python scripts/generate_favicon.py --check
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required. Install with: pip install Pillow")


REPO_ROOT = Path(__file__).resolve().parent.parent
BRANDING = REPO_ROOT / "docs" / "assets" / "branding" / "cirqua"
SOURCE = BRANDING / "cirqua-logo-all.png"

# The horizontal lockup is very wide (787x125); a favicon square cropped from
# it would be unreadable, so the square mark region of the lockup is used.
SIZES = {"favicon.png": 64, "apple-touch-icon.png": 180}


def _square_mark(image: Image.Image) -> Image.Image:
    """Crop the logo to a centred square without altering its geometry."""
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def render(size: int):
    """Render the icon and return the image (not encoded bytes).

    Callers compare decoded pixels rather than PNG bytes: PNG encoding is not
    byte-stable across Pillow versions or platforms, so a byte comparison would
    report a false "stale" result on CI for an identical image.
    """
    with Image.open(SOURCE) as raw:
        image = raw.convert("RGBA")
        square = _square_mark(image)

        # Fit inside the icon box preserving aspect ratio.
        scale = size / square.size[0]
        resized = square.resize((size, max(1, int(square.size[1] * scale))), Image.LANCZOS)

        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        canvas.alpha_composite(
            resized,
            ((size - resized.size[0]) // 2, (size - resized.size[1]) // 2),
        )
        return canvas


def encode(size: int) -> bytes:
    buffer = io.BytesIO()
    render(size).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def same_pixels(path: Path, size: int) -> bool:
    if not path.is_file():
        return False
    try:
        with Image.open(path) as existing:
            existing = existing.convert("RGBA")
            expected = render(size)
            if existing.size != expected.size:
                return False
            return list(existing.getdata()) == list(expected.getdata())
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not SOURCE.is_file():
        sys.exit(f"official logo not found: {SOURCE}")

    with Image.open(SOURCE) as raw:
        print(f"source logo : {SOURCE.relative_to(REPO_ROOT)} ({raw.size[0]}x{raw.size[1]})")

    stale: list[str] = []
    for filename, size in SIZES.items():
        target = BRANDING / filename
        if same_pixels(target, size):
            print(f"up to date  : {filename} ({size}x{size})")
            continue
        if args.check:
            stale.append(filename)
        else:
            target.write_bytes(encode(size))
            print(f"generated   : {filename} ({size}x{size})")

    if args.check:
        if stale:
            print(f"\nSTALE: {', '.join(stale)}")
            return 1
        print("\nOK")
        return 0

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())