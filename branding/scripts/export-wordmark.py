#!/usr/bin/env python3
"""Export the approved Eitr wordmark from its polygon paths. Requires Pillow."""
from pathlib import Path
import shutil
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
NS = "{http://www.w3.org/2000/svg}"
COLORS = {"black": "#000000", "white": "#ffffff", "green": "#78b99a"}
WIDTHS = (512, 1024, 2048)


def main():
    master = ROOT / "source/eitr-wordmark-master.svg"
    tree = ET.parse(master)
    document = tree.getroot()
    x, y, width, height = map(float, document.get("viewBox").split())
    polygons = [[tuple(map(float, point)) for point in
                 re.findall(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", path.get("d"))]
                for path in document.findall(f".//{NS}path")]
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    (ROOT / "svg/eitr-wordmark.svg").write_text(master.read_text())
    for name, color in COLORS.items():
        document.find(f"{NS}g").set("fill", color)
        tree.write(ROOT / f"svg/eitr-wordmark-{name}.svg", encoding="unicode")
        for target_width in WIDTHS:
            target_height = round(target_width * height / width)
            image = Image.new("RGBA", (target_width * 4, target_height * 4))
            draw = ImageDraw.Draw(image)
            for polygon in polygons:
                draw.polygon([((px - x) * target_width * 4 / width,
                               (py - y) * target_height * 4 / height)
                              for px, py in polygon], fill=color)
            image.resize((target_width, target_height), Image.Resampling.LANCZOS).save(
                ROOT / f"png/eitr-wordmark-{name}-{target_width}.png")
    shutil.copyfile(ROOT / "png/eitr-wordmark-black-512.png",
                    ROOT.parent / "fastfetch/assets/eitr-wordmark.png")


if __name__ == "__main__":
    main()
