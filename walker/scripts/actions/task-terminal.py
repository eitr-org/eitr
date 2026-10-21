#!/usr/bin/env python3
"""Present Walker maintenance tasks; preserve failed output for inspection."""
import os
import importlib.util
import fcntl
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_terminal import wait_for_escape
from eitr_paths import code, config as user_config
from eitr_i18n import tr
import re
import shutil
import subprocess
import struct
import tomllib
import termios

LOGO = "ᛖ ᛁ ᛏ ᚱ"


def cell_ratio():
    """Character-cell width / height, using Kitty's reported pixel geometry."""
    try:
        rows, columns, pixels_x, pixels_y = struct.unpack(
            "HHHH", fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b"\0" * 8))
        if rows and columns and pixels_x and pixels_y:
            return (pixels_x / columns) / (pixels_y / rows)
    except (OSError, ValueError):
        pass
    return 0.5


def raster_height(width, aspect, ratio):
    # Each block character represents two vertically stacked samples.
    return max(2, round(width * ratio / aspect) * 2)


def wordmark():
    renderer = code("fastfetch/eitr.py")
    image = code("fastfetch/assets/eitr-wordmark.png")
    if renderer.is_file() and image.is_file():
        try:
            from PIL import Image
            with Image.open(image) as source:
                bounds = source.getchannel("A").getbbox()
                if bounds is None:
                    return LOGO
                aspect = (bounds[2] - bounds[0]) / (bounds[3] - bounds[1])
            width = min(48, shutil.get_terminal_size().columns)
            spec = importlib.util.spec_from_file_location("eitr_about", renderer)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            rendered = module.terminal_logo(image, width, raster_height(width, aspect, cell_ratio()))
            if rendered:
                return rendered.removeprefix("$1")
        except (ImportError, OSError, ValueError):
            pass
    return LOGO


def banner():
    directory = Path(os.environ.get("XDG_CONFIG_HOME", str(user_config())))
    accent = "#509475"
    try:
        palette = tomllib.loads((directory / "theme/current/colors.toml").read_text())
        value = palette.get("accent", "")
        if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            accent = value
    except (OSError, tomllib.TOMLDecodeError):
        pass
    os.environ["EITR_TERMINAL_ACCENT"] = accent
    rgb = [int(accent[i:i + 2], 16) for i in (1, 3, 5)]
    columns = shutil.get_terminal_size().columns
    logo = centered(wordmark(), columns)
    print(f"\n\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{logo}\033[0m", flush=True)
    print(rune_band(rgb, columns) + "\n", flush=True)


FUTHARK = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"


def rune_band(rgb, columns):
    """The Elder Futhark under the wordmark, in the accent, brightest in the middle."""
    runes = FUTHARK if columns >= 2 * len(FUTHARK) + 2 else FUTHARK[:max(1, (columns - 2) // 2)]
    cells = []
    for index, rune in enumerate(runes):
        middle = (len(runes) - 1) / 2 or 1
        strength = 1 - 0.75 * abs(index - middle) / middle
        red, green, blue = (round(channel * strength) for channel in rgb)
        cells.append(f"\033[38;2;{red};{green};{blue}m{rune}")
    padding = " " * max(0, (columns - 2 * len(runes) + 1) // 2)
    return padding + " ".join(cells) + "\033[0m"


def centered(logo, columns):
    rows = logo.splitlines()
    width = max((len(row) for row in rows), default=0)
    padding = " " * max(0, (columns - width) // 2)
    return "\n".join(padding + row for row in rows)


def main(args):
    if not args:
        return 2
    banner()
    if args == ["--banner-only"]:
        return 0
    try:
        result = subprocess.run(args).returncode
    except OSError as error:
        print(error, file=sys.stderr)
        result = 1
    except KeyboardInterrupt:
        result = 130
    if result and result != 130 and sys.stdin.isatty():
        try:
            print(tr('Task failed.'))
            wait_for_escape()
        except (EOFError, KeyboardInterrupt):
            pass
    return result


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
