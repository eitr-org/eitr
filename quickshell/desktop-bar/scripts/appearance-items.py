#!/usr/bin/env python3
import json
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
from eitr_paths import config as user_config, own, theme_paths
from eitr_i18n import tr
import eitr_own_style
import tomllib
import hashlib
from PIL import Image

home = Path.home()
mode = sys.argv[1] if len(sys.argv) > 1 else "wallpaper"
cache = Path(os.environ.get("XDG_CACHE_HOME", str(home / ".cache")))
config = user_config()
def preview_url(path):
    with Image.open(path) as source:
        if source.format != "WEBP":
            return path.as_uri()
    info = path.stat()
    key = hashlib.sha256(f"{path}:{info.st_mtime_ns}:{info.st_size}".encode()).hexdigest()
    directory = cache / "desktop-appearance"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{key}.png"
    if not target.exists():
        with Image.open(path) as image:
            image.thumbnail((1536, 950))
            image.save(target, "PNG")
    return target.as_uri()
def read_current(name):
    try:
        return (cache / name).read_text().strip()
    except OSError:
        return ""

def display_name(directory):
    try:
        label = (directory / "display-name").read_text().strip()
        if label:
            return label
    except OSError:
        pass
    return directory.name.replace("-", " ").replace("_", " ").title()

entries = []
if mode.startswith("theme"):
    current = read_current("current-theme")
    directories = [directory for directory in theme_paths().values()
                   if (directory / "preview.png").is_file()]
    def is_light(directory):
        return (directory / "light.mode").is_file()

    # The colours the Themes & Plugins cards show, for the swatches beside each name.
    SWATCH_KEYS = ("background", "foreground", "accent", "color1", "color2", "color3", "color4", "color5", "color6")

    def swatches(directory):
        try:
            colors = tomllib.loads((directory / "colors.toml").read_text())
        except (OSError, tomllib.TOMLDecodeError):
            return []
        return [colors[key] for key in SWATCH_KEYS if isinstance(colors.get(key), str)]

    if mode in {"theme", "theme-dark", "theme-light"}:
        for directory in directories:
            if mode == "theme" or is_light(directory) == (mode == "theme-light"):
                mine = (directory / "own-theme.json").is_file()
                entries.append({"name": tr('{name} (yours)', name=display_name(directory)) if mine else display_name(directory),
                                "value": directory.name,
                                "image": (directory / "preview.png").as_uri(),
                                "palette": swatches(directory),
                                "current": directory.name == current})
else:
    import eitr_wallpapers as choices
    current = choices.resolve({"name": choices.focused_monitor()}, choices.saved_global(), temporary={})
    directory = config / "theme/current/backgrounds"
    import re
    def natural(path):
        return [int(part) if part.isdigit() else part.lower()
                for part in re.split(r"(\d+)", path.name)]
    current_theme = read_current("current-theme")
    themes = theme_paths()
    current_label = display_name(themes[current_theme]) if current_theme in themes else ""
    # The theme's wallpapers, then (with "wallpaper-all") every other installed theme's in
    # name order, then the user's own (eitr_own_style). Choosing one changes only the wallpaper.
    groups = [(current_label, sorted(directory.rglob("*"), key=natural))]
    if mode == "wallpaper-all":
        others = sorted(((display_name(folder), folder) for name, folder in themes.items() if name != current_theme),
                        key=lambda pair: pair[0].lower())
        groups += [(label, sorted((folder / "backgrounds").rglob("*"), key=natural)) for label, folder in others]
    groups.append(("", eitr_own_style.wallpapers(beside=directory)))
    SMALL_WORDS = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to"}

    def title(path):
        """"02-fenrir-devours-the-sun.jpg" -> "Fenrir Devours the Sun": no order number or extension."""
        words = re.sub(r"^\d+[\s._-]*", "", path.stem).replace("_", " ").replace("-", " ").split()
        return " ".join(word if index and word in SMALL_WORDS else word[:1].upper() + word[1:]
                        for index, word in enumerate(words)) or path.stem
    for label, images in groups:
        for image in images:
            if image.is_file() and image.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                entries.append({"name": title(image), "value": str(image), "theme": label,
                                "image": preview_url(image), "current": choices.canonical(str(image)) == choices.canonical(current) if current else False})
try:
    palette = tomllib.loads((config / "theme/current/colors.toml").read_text())
except (OSError, ValueError):
    palette = {}
print(json.dumps({"mode": mode, "items": entries, "accent": palette.get("accent", "#cdd6f4"),
                  "background": palette.get("background", "#202024"),
                  "foreground": palette.get("foreground", "#ffffff")}))
