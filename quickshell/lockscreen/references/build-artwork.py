#!/usr/bin/env python3
"""Export the retained lockscreen artwork at 3840×2160; keep native sources here."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SIZE = (3840, 2160)
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('designs', nargs='*', help='optional background design IDs; default: all')
    known = {'girl-coffee', 'girl-pillow', 'material-you', 'material-you-dark'}
    selected = set(parser.parse_args().designs) or known
    if selected - known:
        parser.error('Unknown background design ID')
    for name in ("girl-coffee", "girl-pillow"):
        if name not in selected:
            continue
        with Image.open(HERE / f"{name}.png") as source:
            ImageOps.fit(source.convert("RGB"), SIZE, method=Image.Resampling.LANCZOS).save(
                ROOT / "themes" / name / "background.png", optimize=True)

    ring = ET.parse(ROOT.parents[1] / "branding/svg/eitr-rune-ring.svg").getroot()
    for mode, design, ink in (("light", "material-you", "#416154"),
                              ("dark", "material-you-dark", "#c4addb")):
        if design not in selected:
            continue
        backdrop = ET.parse(HERE / f"material-{mode}.svg").getroot()
        backdrop.set("width", str(SIZE[0]))
        backdrop.set("height", str(SIZE[1]))
        ornament = ET.SubElement(backdrop, f"{{{SVG}}}g", {
            "transform": "translate(2150 410) scale(300)", "fill": "none",
            "stroke": ink, "opacity": "0.38", "stroke-linecap": "round",
            "stroke-linejoin": "round"})
        for path in ring.findall(f"{{{SVG}}}path"):
            ET.SubElement(ornament, f"{{{SVG}}}path", dict(path.attrib))
        ET.ElementTree(backdrop).write(ROOT / "themes" / design / "background.svg", encoding="unicode")


if __name__ == "__main__":
    main()
