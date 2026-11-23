#!/usr/bin/env python3
"""Generate wallpaper-and-palette previews for built-in or Store themes."""
import argparse
from pathlib import Path
import sys
import tomllib

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "distro/lib"))
from eitr_theme_preview import render_preview


def contact_sheet(previews, output):
    columns = 4
    width, height = 320, 207
    sheet = Image.new("RGB", (columns * width, ((len(previews) + columns - 1) // columns) * height), "#171717")
    draw = ImageDraw.Draw(sheet)
    for index, preview in enumerate(previews):
        left, top = index % columns * width, index // columns * height
        with Image.open(preview) as image:
            sheet.paste(image.resize((width, 180), Image.Resampling.LANCZOS), (left, top))
        draw.text((left + 8, top + 186), preview.parent.name, fill="white")
    sheet.save(output, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", type=Path, nargs="*", default=[ROOT / "themes"])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--contact-sheet", type=Path)
    args = parser.parse_args()
    previews, stale = [], []
    for root in args.roots:
        palettes = sorted(root.glob("*/colors.toml"))
        if not palettes:
            parser.error(f"No themes found in {root}")
        for palette in palettes:
            target = palette.with_name("preview.png")
            payload = render_preview(palette.parent, tomllib.loads(palette.read_text()))
            previews.append(target)
            if target.is_file() and target.read_bytes() == payload:
                continue
            if args.check:
                stale.append(target)
            else:
                target.write_bytes(payload)
    if stale:
        for target in stale:
            print(f"Out of date: {target}", file=sys.stderr)
        return 1
    if args.contact_sheet:
        contact_sheet(previews, args.contact_sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
