#!/usr/bin/env python3
"""Trace the selected Eitr alpha mask and export vector-first branding assets.

Run with: uv run --with cairosvg --with pillow branding/scripts/export-logo.py
"""
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024, 2048, 4096)
COLORS = {"black": "#000000", "white": "#ffffff", "green": "#32644c"}


def trace():
    with Image.open(ROOT / "source/eitr-logo-master.png") as source:
        alpha = source.getchannel("A")
        alpha = alpha.crop(alpha.getbbox())
        padding = round(max(alpha.size) * 0.06)
        side = max(alpha.size) + padding * 2
        mask = Image.new("L", (side, side), 0)
        mask.paste(alpha, ((side - alpha.width) // 2, (side - alpha.height) // 2))
    pixels = mask.load()
    def filled(x, y):
        return 0 <= x < side and 0 <= y < side and pixels[x, y] >= 128
    edges = {}
    def edge(a, b):
        edges.setdefault(a, []).append(b)
    for y in range(side):
        for x in range(side):
            if not filled(x, y):
                continue
            if not filled(x, y - 1): edge((x, y), (x + 1, y))
            if not filled(x + 1, y): edge((x + 1, y), (x + 1, y + 1))
            if not filled(x, y + 1): edge((x + 1, y + 1), (x, y + 1))
            if not filled(x - 1, y): edge((x, y + 1), (x, y))
    contours = []
    while edges:
        start = next(iter(edges))
        points, current = [start], start
        while True:
            current_edges = edges[current]
            following = current_edges.pop()
            if not current_edges: del edges[current]
            current = following
            if current == start: break
            points.append(current)
        if len(points) < 20: continue
        split = max(range(len(points)), key=lambda i: (points[i][0] - start[0]) ** 2 + (points[i][1] - start[1]) ** 2)
        points = simplify(points[:split + 1])[:-1] + simplify(points[split:] + [start])[:-1]
        contours.append("M" + " L".join(f"{x},{y}" for x, y in points) + " Z")
    if len(contours) != 2:
        raise RuntimeError(f"Expected outer contour and rune hole, found {len(contours)}")
    return side, '<path fill-rule="evenodd" d="' + " ".join(contours) + '"/>'


def simplify(points, tolerance=0.8):
    """Ramer–Douglas–Peucker: retain corners, remove subpixel contour noise."""
    if len(points) <= 2: return points
    a, b = points[0], points[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = (dx * dx + dy * dy) ** 0.5
    distances = [abs(dy * (x - a[0]) - dx * (y - a[1])) / length for x, y in points]
    index = max(range(len(points)), key=distances.__getitem__)
    if distances[index] <= tolerance: return [a, b]
    return simplify(points[:index + 1], tolerance)[:-1] + simplify(points[index:], tolerance)


def svg(side, paths, color, width=None, height=None, background=None):
    width, height = width or side, height or side
    scale = min(width, height) * (0.55 if background else 1) / side
    x, y = (width - side * scale) / 2, (height - side * scale) / 2
    backdrop = f'<rect width="{width}" height="{height}" fill="{background}"/>' if background else ""
    return (f'<svg xmlns="{SVG_NS}" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}"><title>Eitr logo</title>'
            f'{backdrop}<g fill="{color}" transform="translate({x:g} {y:g}) scale({scale:g})">'
            f'{paths}</g></svg>\n')


def main():
    side, paths = trace()
    for directory in ("svg", "png", "banners", "icons", "pdf"):
        (ROOT / directory).mkdir(exist_ok=True)
    master = svg(side, paths, "currentColor")
    (ROOT / "svg/eitr-logo.svg").write_text(master)
    for name, color in COLORS.items():
        asset = svg(side, paths, color)
        (ROOT / f"svg/eitr-logo-{name}.svg").write_text(asset)
        if name == "white":
            installed = ROOT.parent / "quickshell/desktop-bar/assets"
            installed.mkdir(parents=True, exist_ok=True)
            (installed / "eitr-logo-white.svg").write_text(asset)
        for size in SIZES:
            cairosvg.svg2png(bytestring=asset.encode(), output_width=size, output_height=size,
                            write_to=str(ROOT / f"png/eitr-logo-{name}-{size}.png"))
        cairosvg.svg2pdf(bytestring=asset.encode(), write_to=str(ROOT / f"pdf/eitr-logo-{name}.pdf"))
    for name, foreground, background in (
        ("dark", "#68aa87", "#10231c"), ("light", "#32644c", "#f3f8f1")):
        asset = svg(side, paths, foreground, 1920, 1080, background)
        (ROOT / f"banners/eitr-{name}-1920x1080.svg").write_text(asset)
        cairosvg.svg2png(bytestring=asset.encode(), write_to=str(ROOT / f"banners/eitr-{name}-1920x1080.png"))
    icon = svg(side, paths, "#32644c", 256, 256, "#f3f8f1")
    image = Image.open(BytesIO(cairosvg.svg2png(bytestring=icon.encode())))
    image.save(ROOT / "icons/eitr.ico", sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
    print("Exported SVG, transparent PNG (16–4096px), vector PDF, banners and ICO.")


if __name__ == "__main__":
    main()
