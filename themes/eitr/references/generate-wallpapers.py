#!/usr/bin/env python3
"""Render the Norse runestone wallpaper (3840x2160) into ../backgrounds, and its
live layers into ../motion/02-eitr-runestone.

The EITR emblem sits inside a ring of carved runes. Runes are drawn as straight
strokes, so no font is needed. The output is deterministic. The live layers are
the starry sky and the ring with the emblem; the desktop draws the website's
moving aurora between them (see quickshell/desktop-bar/LiveWallpaperScene.qml).
Auxiliary renderers retain the source for the theme's procedural aurora preview
and rune artwork.
"""
from pathlib import Path
import math
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parent / "backgrounds"
MOTION = HERE.parent / "motion"
LOGO = HERE.parents[2] / "branding/svg/eitr-logo.svg"
WIDTH, HEIGHT = 3840, 2160
SCALE = 2  # Lines are drawn at twice the size, then downscaled for smooth edges.

NIGHT = (5, 8, 12)
HORIZON = (16, 30, 40)
EITR = (126, 224, 181)
AURORA = (79, 195, 201)
VIOLET = (143, 126, 224)
BRONZE = (196, 145, 79)
FROST = (233, 238, 241)

# Elder Futhark strokes in a 0.6 x 1 box (x right, y down).
RUNES = {
    "fehu": [((0, 0), (0, 1)), ((0, .25), (.55, 0)), ((0, .5), (.55, .25))],
    "uruz": [((0, 1), (0, 0)), ((0, 0), (.55, .3)), ((.55, .3), (.55, 1))],
    "thurisaz": [((0, 0), (0, 1)), ((0, .3), (.45, .5)), ((.45, .5), (0, .7))],
    "ansuz": [((0, 0), (0, 1)), ((0, 0), (.5, .25)), ((0, .3), (.5, .55))],
    "raidho": [((0, 0), (0, 1)), ((0, 0), (.45, .22)), ((.45, .22), (0, .45)), ((0, .45), (.5, 1))],
    "kaunan": [((.5, .2), (.1, .5)), ((.1, .5), (.5, .8))],
    "gebo": [((0, .1), (.6, .9)), ((.6, .1), (0, .9))],
    "wunjo": [((0, 0), (0, 1)), ((0, 0), (.45, .22)), ((.45, .22), (0, .45))],
    "hagalaz": [((0, 0), (0, 1)), ((.55, 0), (.55, 1)), ((0, .35), (.55, .6))],
    "naudiz": [((.3, 0), (.3, 1)), ((.05, .3), (.55, .6))],
    "isaz": [((.3, 0), (.3, 1))],
    "jera": [((.25, .1), (.05, .35)), ((.05, .35), (.25, .6)), ((.35, .4), (.55, .65)), ((.55, .65), (.35, .9))],
    "eihwaz": [((.3, 0), (.3, 1)), ((.3, 0), (.55, .2)), ((.3, 1), (.05, .8))],
    "perthro": [((0, 0), (0, 1)), ((0, 0), (.5, .2)), ((.5, .2), (.5, .32)), ((0, 1), (.5, .8)), ((.5, .8), (.5, .68))],
    "algiz": [((.3, 0), (.3, 1)), ((.3, .4), (0, .05)), ((.3, .4), (.6, .05))],
    "sowilo": [((.45, 0), (.1, .4)), ((.1, .4), (.5, .6)), ((.5, .6), (.15, 1))],
    "tiwaz": [((.3, 0), (.3, 1)), ((.3, 0), (0, .3)), ((.3, 0), (.6, .3))],
    "berkanan": [((0, 0), (0, 1)), ((0, 0), (.45, .25)), ((.45, .25), (0, .5)), ((0, .5), (.45, .75)), ((.45, .75), (0, 1))],
    "ehwaz": [((0, 0), (0, 1)), ((.6, 0), (.6, 1)), ((0, 0), (.3, .35)), ((.3, .35), (.6, 0))],
    "mannaz": [((0, 0), (0, 1)), ((.6, 0), (.6, 1)), ((0, 0), (.6, .4)), ((.6, 0), (0, .4))],
    "laguz": [((.1, 0), (.1, 1)), ((.1, 0), (.55, .3))],
    "ingwaz": [((.3, .15), (.6, .5)), ((.6, .5), (.3, .85)), ((.3, .85), (0, .5)), ((0, .5), (.3, .15))],
    "dagaz": [((0, 0), (0, 1)), ((.6, 0), (.6, 1)), ((0, 0), (.6, 1)), ((.6, 0), (0, 1))],
    "othala": [((.3, 0), (.6, .4)), ((.6, .4), (.3, .8)), ((.3, .8), (0, .4)), ((0, .4), (.3, 0)),
               ((.15, .6), (0, 1)), ((.45, .6), (.6, 1))],
}
FUTHARK = list(RUNES)


def vertical_gradient(top, bottom, height=HEIGHT, width=WIDTH, curve=1.0):
    ramp = np.linspace(0, 1, height)[:, None] ** curve
    colors = np.array(top) + (np.array(bottom) - np.array(top)) * ramp
    return np.repeat(colors[:, None, :], width, axis=1)


def to_image(array):
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), "RGB")


def stars(canvas, count, seed, top_bias=2.2):
    generator = np.random.default_rng(seed)
    layer = np.zeros((HEIGHT, WIDTH))
    xs = generator.integers(0, WIDTH, count)
    ys = (generator.random(count) ** top_bias * HEIGHT * 0.7).astype(int)
    layer[ys, xs] = generator.random(count) * 0.9 + 0.1
    glow = np.array(Image.fromarray((layer * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))) / 255
    return canvas + (layer[..., None] * 0.55 + glow[..., None] * 1.8) * np.array(FROST)


def smooth_noise(generator, length, width):
    """Random values smoothed along one axis: organic, not periodic."""
    values = generator.random(length + width * 4)
    kernel = np.exp(-np.linspace(-2, 2, width * 4) ** 2)
    return np.convolve(values, kernel / kernel.sum(), mode="same")[width * 2:width * 2 + length]


# Sampled from the owner's photos of real auroras: a lime fringe and green at the
# curtain's foot, magenta and orchid as it rises, violet at the top.
STORM_LIME = (194, 238, 90)
STORM_GREEN = (63, 227, 154)
STORM_MAGENTA = (224, 79, 195)
STORM_ORCHID = (242, 182, 230)
STORM_VIOLET = (155, 92, 230)


def storm_color(height, blend):
    """Colour by height above the curtain's foot; blend (0 green .. 1 magenta) varies across the sky."""
    fringe = np.clip(1 - height * 9, 0, 1) ** 2
    low = np.clip(1 - height * 1.6, 0, 1) ** 1.5
    middle = np.clip(1 - np.abs(height - 0.45) * 2.6, 0, 1)
    top = height ** 1.2
    greenish = np.array(STORM_LIME) * fringe * 0.8 + np.array(STORM_GREEN) * low + np.array(STORM_VIOLET) * top * 0.6
    pinkish = (np.array(STORM_GREEN) * low * 0.45 + np.array(STORM_MAGENTA) * middle * 1.35
               + np.array(STORM_ORCHID) * middle * 0.3 + np.array(STORM_MAGENTA) * top * 0.45
               + np.array(STORM_VIOLET) * top * 0.4)
    return greenish * (1 - blend) + pinkish * blend


def curtain(seed, base, sway, strength, palette="eitr"):
    """One hanging curtain: bright along a folding base line, fading upward in soft rays."""
    generator = np.random.default_rng(seed)
    x = np.linspace(0, 1, WIDTH)
    phase = generator.random(3) * math.tau
    folds = smooth_noise(generator, WIDTH, 60) - 0.5
    baseline = (base + sway * np.sin(x * 3.3 + phase[0]) + sway * 0.4 * np.sin(x * 7.9 + phase[1])
                + folds * 0.12) * HEIGHT
    rays = smooth_noise(generator, WIDTH, 14)
    rays = (rays - rays.min()) / (rays.max() - rays.min())
    rays = 0.25 + 0.75 * rays ** 1.6 * (0.6 + 0.4 * smooth_noise(generator, WIDTH, 120) * 2)
    envelope = np.clip(np.sin(np.pi * np.clip(x * 1.1 - 0.05, 0, 1)), 0, 1) ** 1.2
    reach = HEIGHT * (0.16 + 0.12 * smooth_noise(generator, WIDTH, 90)) * (1.7 if palette == "storm" else 1)
    y = np.arange(HEIGHT)[:, None]
    above = baseline[None, :] - y
    light = np.where(above > 0, np.exp(-above / reach[None, :]), np.exp(above / (HEIGHT * 0.012)))
    height = np.clip(above / (HEIGHT * 0.42), 0, 1)[..., None]
    if palette == "storm":
        wander = smooth_noise(generator, WIDTH, 260)
        wander = (wander - wander.min()) / (wander.max() - wander.min())
        blend = np.clip((wander - 0.3) * 2.2, 0, 1)[None, :, None]
        color = storm_color(height, blend)
    else:
        color = (np.array(EITR) * (1 - height) ** 1.7 + np.array(AURORA) * (1 - np.abs(height - 0.4) * 2.2).clip(0)
                 + np.array(VIOLET) * height ** 1.4 * 0.9)
    return (light * rays[None, :] * envelope[None, :] * strength)[..., None] * color


def aurora_light(seed, strength=1.0, base=0.40, sway=0.08, palette="eitr"):
    light = sum(curtain(seed + index, base + offset, sway, strength * weight, palette)
                for index, (offset, weight) in enumerate(((0.0, 1.0), (-0.07, 0.55), (0.05, 0.4))))
    blurred = np.array(to_image(light).filter(ImageFilter.GaussianBlur(9))).astype(float)
    return blurred * 0.9 + light * 0.15


def aurora(canvas, seed, strength=1.0, base=0.40, sway=0.08, palette="eitr"):
    return canvas + aurora_light(seed, strength, base, sway, palette)


def light_layer(light):
    """Additive light as a transparent image: alpha carries the brightness."""
    light = np.clip(light, 0, 255)
    alpha = light.max(axis=2, keepdims=True)
    color = np.where(alpha > 0, light * 255 / np.maximum(alpha, 1), 0)
    return Image.fromarray(np.concatenate([color, alpha], axis=2).astype(np.uint8), "RGBA")


def ridge(seed, base, roughness, peaks):
    """A jagged fjord ridge: a few random summits refined by midpoint displacement."""
    generator = np.random.default_rng(seed)
    points = base - np.abs(generator.normal(0, roughness, peaks))
    spread = roughness * 0.6
    for _ in range(8):
        middle = (points[:-1] + points[1:]) / 2 + generator.normal(0, spread, len(points) - 1)
        merged = np.empty(len(points) * 2 - 1)
        merged[0::2], merged[1::2] = points, middle
        points, spread = merged, spread * 0.52
    xs = np.linspace(0, WIDTH, len(points))
    return list(zip(xs, points))


def mountains(image, layers):
    draw = ImageDraw.Draw(image)
    for seed, base, roughness, color in layers:
        outline = ridge(seed, base, roughness, 9)
        draw.polygon([(0, HEIGHT), *outline, (WIDTH, HEIGHT)], fill=color)
    return image


def draw_rune(draw, name, x, y, height, width_px, fill, rotation=None):
    """Top-left at (x, y); with rotation, (x, y) is the rune's centre and its top faces outward."""
    def place(px, py):
        if rotation is None:
            return x + px * height, y + py * height
        dx, dy = (px - 0.3) * height, (py - 0.5) * height
        return (x + dx * math.cos(rotation) - dy * math.sin(rotation),
                y + dx * math.sin(rotation) + dy * math.cos(rotation))
    radius = width_px / 2
    for start, end in RUNES[name]:
        points = [place(*start), place(*end)]
        draw.line(points, fill=fill, width=width_px)
        for px, py in points:
            draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=fill)


def carved_layer(size, paint):
    """Draw at SCALE, downscale for smooth strokes; paint(draw, scale) draws white on black."""
    big = Image.new("L", (size[0] * SCALE, size[1] * SCALE), 0)
    paint(ImageDraw.Draw(big), SCALE)
    return big.resize(size, Image.LANCZOS)


def tint(mask, color, glow_radius=0, glow_strength=0.0):
    color_layer = Image.new("RGB", mask.size, color)
    result = Image.composite(color_layer, Image.new("RGB", mask.size, 0), mask)
    if glow_radius:
        halo = result.filter(ImageFilter.GaussianBlur(glow_radius))
        result = ImageChops.add(result, Image.eval(halo, lambda value: int(value * glow_strength)))
    return result


def emblem(size, color):
    with tempfile.TemporaryDirectory() as directory:
        svg = Path(directory) / "logo.svg"
        svg.write_text(LOGO.read_text().replace("currentColor", "#{:02x}{:02x}{:02x}".format(*color)))
        png = Path(directory) / "logo.png"
        subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), str(svg), "-o", str(png)], check=True)
        return Image.open(png).convert("RGBA")


def niflheim_aurora():
    sky = vertical_gradient(NIGHT, HORIZON, curve=1.4)
    sky = stars(sky, 1600, seed=7)
    sky = to_image(aurora(sky, seed=11, strength=1.0, base=0.42))
    water_line = int(HEIGHT * 0.78)
    image = sky.copy()
    # The fjord mirrors the sky above the mountains, darker and broken into ripples.
    depth = HEIGHT - water_line
    reflection = sky.crop((0, water_line - depth * 2, WIDTH, water_line)).transpose(Image.FLIP_TOP_BOTTOM)
    reflection = reflection.resize((WIDTH, depth)).resize((WIDTH // 3, depth)).resize((WIDTH, depth))
    reflection = Image.blend(Image.new("RGB", reflection.size, NIGHT), reflection, 0.5)
    image.paste(reflection, (0, water_line))
    for seed, top, roughness, color in ((3, 0.66, 0.12, (17, 29, 38)), (5, 0.72, 0.09, (11, 19, 26)),
                                        (9, 0.77, 0.05, (7, 12, 17))):
        outline = [(x, min(y, water_line)) for x, y in ridge(seed, HEIGHT * top, HEIGHT * roughness, 7)]
        land = Image.new("L", image.size, 0)
        ImageDraw.Draw(land).polygon([(0, water_line), *outline, (WIDTH, water_line)], fill=255)
        image.paste(Image.new("RGB", image.size, color), (0, 0), land)
        # Mirrored silhouettes darken the water but let the aurora's reflection through.
        mirror = Image.new("L", image.size, 0)
        ImageDraw.Draw(mirror).polygon([(0, water_line), *[(x, 2 * water_line - y) for x, y in outline],
                                        (WIDTH, water_line)], fill=150)
        image.paste(Image.new("RGB", image.size, color), (0, 0), mirror)
    ImageDraw.Draw(image).line([(0, water_line), (WIDTH, water_line)], fill=(20, 36, 42), width=2)
    return image


RUNESTONE = dict(seed=21, strength=1.25, base=0.62, sway=0.06, palette="storm")


def runestone_sky():
    sky = vertical_gradient((9, 6, 18), (24, 18, 46), curve=0.9)
    return stars(sky, 700, seed=3, top_bias=1.4)


def runestone_ring():
    """The bronze rune ring and glowing emblem on a transparent layer."""
    center, radius = (int(WIDTH * 0.70), HEIGHT // 2), int(HEIGHT * 0.36)

    def paint(draw, scale):
        cx, cy, r = center[0] * scale, center[1] * scale, radius * scale
        for ring, width in ((r * 1.13, 3), (r * 0.86, 3)):
            draw.ellipse([cx - ring, cy - ring, cx + ring, cy + ring], outline=255, width=width * scale)
        sequence = FUTHARK * 2
        rune_height = r * 0.16
        for index, name in enumerate(sequence):
            angle = -math.pi / 2 + index / len(sequence) * math.tau
            draw_rune(draw, name, cx + math.cos(angle) * r, cy + math.sin(angle) * r, rune_height, 4 * scale, 255,
                      rotation=angle + math.pi / 2)

    ring = tint(carved_layer((WIDTH, HEIGHT), paint), BRONZE, glow_radius=6, glow_strength=0.6)
    layer = light_layer(np.array(Image.eval(ring, lambda value: int(value * 0.8))).astype(float))
    mark = emblem(int(radius * 0.95), BRONZE)
    halo = Image.new("RGBA", layer.size, 0)
    halo.paste(mark, (center[0] - mark.width // 2, center[1] - mark.height // 2), mark)
    glow = halo.filter(ImageFilter.GaussianBlur(40))
    layer = Image.alpha_composite(layer, Image.eval(glow, lambda value: int(value * 0.7)))
    return Image.alpha_composite(layer, halo)


def eitr_runestone():
    image = to_image(aurora(runestone_sky(), **RUNESTONE)).convert("RGBA")
    return Image.alpha_composite(image, runestone_ring()).convert("RGB")


def runestone_motion():
    """Layers for the live wallpaper; the desktop draws the moving aurora between
    them with quickshell/desktop-bar/shaders/aurora.frag."""
    folder = MOTION / "02-eitr-runestone"
    folder.mkdir(parents=True, exist_ok=True)
    to_image(runestone_sky()).save(folder / "sky.png", optimize=True)
    runestone_ring().save(folder / "ring.png", optimize=True)


def futhark_band():
    sky = vertical_gradient((9, 13, 18), (6, 9, 13), curve=1.0)
    image = to_image(aurora(sky, seed=31, strength=0.22, base=0.35, sway=0.04))
    rune_height, gap = HEIGHT * 0.07, HEIGHT * 0.034
    total = len(FUTHARK) * (rune_height * 0.6 + gap) - gap
    start, top = (WIDTH - total) / 2, HEIGHT * 0.5 - rune_height / 2

    def paint(draw, scale):
        for index, name in enumerate(FUTHARK):
            x = (start + index * (rune_height * 0.6 + gap)) * scale
            draw_rune(draw, name, x, top * scale, rune_height * scale, 5 * scale, 255)

    band = tint(carved_layer((WIDTH, HEIGHT), paint), FROST, glow_radius=10, glow_strength=0.5)
    image = ImageChops.add(image, Image.eval(band, lambda value: int(value * 0.55)))
    line = ImageDraw.Draw(image)
    for y in (top - gap * 0.8, top + rune_height + gap * 0.8):
        line.line([(start, y), (start + total, y)], fill=(48, 62, 74), width=2)
    return image


def runestone_ring_svg():
    """The rune ring as a scalable outline for the website, with the wallpaper's
    proportions: the rune circle has radius 1, its rings sit at 0.86 and 1.13."""
    def point(x, y):
        return f"{x:.4f} {y:.4f}"
    paths = []
    for ring in (1.13, 0.86):
        paths.append(f"M{point(ring, 0)}A{ring} {ring} 0 1 1 {point(-ring, 0)}A{ring} {ring} 0 1 1 {point(ring, 0)}")
    sequence = FUTHARK * 2
    height = 0.16
    for index, name in enumerate(sequence):
        angle = -math.pi / 2 + index / len(sequence) * math.tau
        cx, cy, rotation = math.cos(angle), math.sin(angle), angle + math.pi / 2

        def place(px, py):
            dx, dy = (px - 0.3) * height, (py - 0.5) * height
            return point(cx + dx * math.cos(rotation) - dy * math.sin(rotation),
                         cy + dx * math.sin(rotation) + dy * math.cos(rotation))
        paths.extend(f"M{place(*start)}L{place(*end)}" for start, end in RUNES[name])
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.2 -1.2 2.4 2.4" fill="none" stroke="currentColor" '
           'stroke-linecap="round" stroke-linejoin="round"><title>Eitr rune ring</title>'
           f'<path stroke-width="0.0058" d="{"".join(paths[:2])}"/>'
           f'<path stroke-width="0.0077" d="{"".join(paths[2:])}"/></svg>\n')
    (HERE.parents[2] / "branding/svg/eitr-rune-ring.svg").write_text(svg)


def main():
    OUTPUT.mkdir(exist_ok=True)
    runestone_ring_svg()
    name = "02-eitr-runestone.png"
    eitr_runestone().save(OUTPUT / name, optimize=True)
    runestone_motion()
    print(name)


if __name__ == "__main__":
    main()
