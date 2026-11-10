"""Deterministic picture palettes and shared color/contrast operations."""
import colorsys
import importlib.util
import sys

from eitr_paths import code

KEY_ORDER = ("accent", "cursor", "foreground", "background", "selection_foreground", "selection_background",
             *(f"color{index}" for index in range(16)))

def _module(relative, name):
    specification = importlib.util.spec_from_file_location(name, code(relative))
    module = importlib.util.module_from_spec(specification)
    # No __pycache__ beside shipped themes or scripts.
    writes, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        specification.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes
    return module


def palette_tools():
    """walker/scripts/themes/palette.py: luminance, contrast and readable()."""
    return _module("walker/scripts/themes/palette.py", "eitr_theme_palette")


def _hex(red, green, blue):
    return "#" + "".join(f"{max(0, min(255, round(value * 255))):02x}" for value in (red, green, blue))


def hls(hue, lightness, saturation):
    return _hex(*colorsys.hls_to_rgb(hue % 1.0, max(0.0, min(1.0, lightness)), max(0.0, min(1.0, saturation))))


def to_hls(color):
    return colorsys.rgb_to_hls(*(int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)))


def mix(first, second, amount):
    one = [int(first[index:index + 2], 16) for index in (1, 3, 5)]
    two = [int(second[index:index + 2], 16) for index in (1, 3, 5)]
    return _hex(*((a + (b - a) * amount) / 255 for a, b in zip(one, two)))


def analyse(path):
    """Dominant colors of a picture, deterministic: (mean luminance, [(share, hex)])."""
    from PIL import Image
    tools = palette_tools()
    with Image.open(path) as source:
        image = source.convert("RGB")
    image.thumbnail((96, 96), Image.Resampling.BOX)
    pixels = list(image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata())
    brightness = sum(tools.luminance(_hex(*(value / 255 for value in pixel))) for pixel in pixels) / len(pixels)
    quantized = image.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    colors = quantized.getpalette()
    counts = sorted(quantized.getcolors(), key=lambda item: (-item[0], item[1]))
    swatches = [(count / len(pixels), _hex(*(value / 255 for value in colors[index * 3:index * 3 + 3])))
                for count, index in counts]
    return brightness, swatches


def suggested_mode(path):
    return "light" if analyse(path)[0] > 0.4 else "dark"


def _contrasting(color, background, target, tools):
    """Push lightness away from the background until the contrast target is met."""
    hue, lightness, saturation = to_hls(color)
    toward = 1.0 if tools.luminance(background) < 0.5 else 0.0
    for step in range(41):
        candidate = hls(hue, lightness + (toward - lightness) * step / 40, saturation)
        if tools.contrast(candidate, background) >= target:
            return candidate
    return hls(hue, toward, saturation)


def brighter(color, background, light, tools):
    """The bright ANSI variant of a terminal color, still readable on the background."""
    hue, lightness, saturation = to_hls(color)
    return _contrasting(hls(hue, lightness + (-0.08 if light else 0.12), saturation), background, 4.5, tools)


def generate_palette(path, mode=None):
    """A complete colors.toml palette from a picture; returns (palette, mode)."""
    tools = palette_tools()
    brightness, swatches = analyse(path)
    mode = mode or ("light" if brightness > 0.4 else "dark")
    light = mode == "light"
    dominant_hue, _, dominant_saturation = to_hls(swatches[0][1])

    def score(item):
        share, color = item
        _, lightness, saturation = to_hls(color)
        return saturation * share ** 0.5 * (1 - abs(lightness - 0.5))
    share, vivid = max(swatches, key=score)
    accent_hue, _, accent_saturation = to_hls(vivid)
    if accent_saturation < 0.15:
        accent_hue, accent_saturation = dominant_hue, 0.45
    tint = min(dominant_saturation, 0.3) * 0.6
    background = hls(dominant_hue, 0.95 if light else 0.07, tint)
    foreground = _contrasting(hls(dominant_hue, 0.16 if light else 0.88, min(tint, 0.12)), background, 7.0, tools)
    accent = _contrasting(hls(accent_hue, 0.42 if light else 0.58, max(0.45, min(accent_saturation, 0.85))),
                          background, 3.0, tools)
    saturation = max(0.45, min(0.75, sum(to_hls(color)[2] for _, color in swatches) / len(swatches) * 1.5))
    colors = {"accent": accent, "cursor": accent, "foreground": foreground, "background": background}
    selection = mix(background, accent, 0.35)
    colors["selection_background"] = selection
    colors["selection_foreground"] = foreground if tools.contrast(foreground, selection) >= 4.5 else background
    colors["color0"] = hls(dominant_hue, 0.86 if light else 0.15, tint)
    for number, degrees in enumerate((355, 135, 45, 215, 300, 180), 1):
        normal = _contrasting(hls(degrees / 360, 0.40 if light else 0.62, saturation), background, 4.5, tools)
        colors[f"color{number}"], colors[f"color{number + 8}"] = normal, brighter(normal, background, light, tools)
    colors["color7"] = _contrasting(hls(dominant_hue, 0.30 if light else 0.78, min(tint, 0.1)), background, 4.5, tools)
    colors["color8"] = _contrasting(hls(dominant_hue, 0.55 if light else 0.38, tint), background, 3.0, tools)
    colors["color15"] = foreground
    return colors, mode


def render_colors(colors):
    lines = [f'{key} = "{colors[key]}"' for key in KEY_ORDER[:6]] + [""]
    lines += [f'{key} = "{colors[key]}"' for key in KEY_ORDER[6:]]
    return "\n".join(lines) + "\n"
