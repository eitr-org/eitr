#!/usr/bin/env python3
"""Export the About rune logo and its transparent Settings preview from the SVG.

Requires rsvg-convert, fontconfig, Pillow and fontTools. Run from any directory.
"""

import argparse
from io import BytesIO
from pathlib import Path
import subprocess

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MASTER = HERE.parent / "svg/eitr-logo.svg"
# The 24 Elder Futhark letters, rather than the entire mixed Runic Unicode block.
FUTHARK = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
CELL_WIDTH, CELL_HEIGHT = 12, 24


def font_path(pattern):
    return subprocess.check_output(
        ["fc-match", "-f", "%{file}", pattern], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path, default=Path("/tmp/rune-logo-previews"))
    args = parser.parse_args()
    args.preview_dir.mkdir(parents=True, exist_ok=True)
    primary_path = font_path("JetBrainsMono Nerd Font")
    fallback_path = font_path("JetBrainsMono Nerd Font:charset=16a0")
    with TTFont(primary_path) as primary, TTFont(fallback_path) as fallback:
        primary_chars = primary.getBestCmap()
        fallback_chars = fallback.getBestCmap()
    assert len(FUTHARK) == len(set(FUTHARK)) == 24
    assert all(ord(rune) in primary_chars or ord(rune) in fallback_chars for rune in FUTHARK)
    fonts = [ImageFont.truetype(path, 20) for path in (primary_path, fallback_path)]
    raster = subprocess.check_output(["rsvg-convert", "--width", "2048", str(MASTER)])
    alpha = Image.open(BytesIO(raster)).getchannel("A")
    mask = alpha.crop(alpha.getbbox())
    report = [f"Primary: {Path(primary_path).name}", f"Fallback: {Path(fallback_path).name}"]
    rows = 20
    columns = round(rows * mask.width / mask.height * CELL_HEIGHT / CELL_WIDTH)
    # Area coverage preserves the silhouette and the SVG's even-odd E hole.
    sampled = mask.resize((columns, rows), Image.Resampling.BOX)
    lines = []
    rune_index = 0
    for row in range(rows):
        line = ""
        for column in range(columns):
            if sampled.getpixel((column, row)) >= 128:
                line += FUTHARK[rune_index % len(FUTHARK)]
                rune_index += 1
            else:
                line += " "
        lines.append(line.rstrip())
    stem = "eitr-runes"
    assets = HERE.parents[1] / "fastfetch/assets"
    (assets / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    image = Image.new("RGBA", (columns * CELL_WIDTH, rows * CELL_HEIGHT), "#00000000")
    draw = ImageDraw.Draw(image)
    for row, line in enumerate(lines):
        for column, rune in enumerate(line):
            if rune == " ":
                continue
            font = fonts[0 if ord(rune) in primary_chars else 1]
            # Kitty centers fallback glyphs in the primary font's cell.
            bounds = font.getbbox(rune)
            x = column * CELL_WIDTH + (CELL_WIDTH - bounds[2] + bounds[0]) / 2 - bounds[0]
            y = row * CELL_HEIGHT + (CELL_HEIGHT - bounds[3] + bounds[1]) / 2 - bounds[1]
            draw.text((x, y), rune, font=font, fill="#ffffff")
    image.save(assets / f"{stem}.png")
    report.append(f"{stem}: {columns} columns x {rows} rows, {rune_index} runes")
    (args.preview_dir / "font-report.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
