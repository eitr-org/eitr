#!/usr/bin/env python3
"""Read the active theme palette and answer light/dark questions.

The theme directory holds a flat ``colors.toml`` (accent, foreground,
background, cursor, selection_*, color0-color15) and an optional
``light.mode`` marker.  ``light.mode`` is the single source of truth for
whether a theme is light; luminance helpers are for contrast decisions only.

Usage:
  palette.py get KEY...        print one value per line (empty if missing)
  palette.py is-light          exit 0 for light themes, 1 for dark themes
  palette.py fzf-colors        print an fzf --color value, or nothing
  palette.py accent-text       print the accent, lightened or darkened in the same
                               hue until it reads as text on the background
Set THEME_DIR (or pass --dir) to read a theme other than the current one.
"""

import argparse
import colorsys
import os
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config
import re
import tomllib

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def current_dir():
    return Path(os.environ.get("THEME_DIR") or user_config("theme/current"))


def load(directory=None):
    """Return the palette's valid hex colors; an empty dict if it is missing."""
    path = Path(directory or current_dir()) / "colors.toml"
    try:
        with path.open("rb") as source:
            data = tomllib.load(source)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return {key: value for key, value in data.items()
            if isinstance(value, str) and HEX_COLOR.match(value)}


def is_light(directory=None):
    return (Path(directory or current_dir()) / "light.mode").exists()


def rgb(color):
    return tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))


def luminance(color):
    channels = [value / 255 for value in rgb(color)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in channels]
    return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(first, second):
    bright, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (bright + 0.05) / (dark + 0.05)


def readable(color, background, foreground, target=4.5):
    """The colour lightened (same hue) just enough to reach the target contrast."""
    hue, lightness, saturation = colorsys.rgb_to_hls(*(value / 255 for value in rgb(color)))
    toward = 1.0 if luminance(background) < 0.5 else 0.0
    for step in range(41):
        level = lightness + (toward - lightness) * step / 40
        mixed = "#" + "".join(f"{round(value * 255):02x}" for value in colorsys.hls_to_rgb(hue, level, saturation))
        if contrast(mixed, background) >= target:
            return mixed
    return foreground


def accent_text(palette):
    """A dark accent is fine as a fill; text and thin lines need a readable shade of it."""
    if not all(key in palette for key in ("foreground", "background", "accent")):
        return palette.get("accent", "")
    return readable(palette.get("accent_text", palette["accent"]),
                    palette.get("surface", palette["background"]), palette["foreground"])


def fzf_colors(palette):
    """Map a palette onto fzf's color roles; empty when the palette is incomplete."""
    if not all(key in palette for key in ("foreground", "background", "accent")):
        return ""
    fg, bg, accent = palette["foreground"], palette["background"], palette["accent"]
    roles = {
        "fg": fg, "bg": bg, "hl": palette.get("color1", accent),
        "fg+": fg, "bg+": palette.get("color0", bg), "hl+": palette.get("color1", accent),
        "info": palette.get("color5", accent), "prompt": accent_text(palette),
        "pointer": accent_text(palette), "marker": palette.get("color2", accent),
        "spinner": palette.get("color3", accent), "header": palette.get("color6", accent),
        "border": accent,
    }
    return ",".join(f"{role}:{color}" for role, color in roles.items())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", type=Path, help="theme directory (default: current theme)")
    commands = parser.add_subparsers(dest="command", required=True)
    get = commands.add_parser("get")
    get.add_argument("keys", nargs="+")
    commands.add_parser("is-light")
    commands.add_parser("fzf-colors")
    commands.add_parser("accent-text")
    args = parser.parse_args(argv)

    if args.command == "is-light":
        return 0 if is_light(args.dir) else 1
    palette = load(args.dir)
    if args.command == "get":
        for key in args.keys:
            print(palette.get(key, ""))
    elif args.command == "accent-text":
        print(accent_text(palette))
    else:
        print(fzf_colors(palette))
    return 0


if __name__ == "__main__":
    sys.exit(main())
