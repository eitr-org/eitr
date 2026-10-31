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

    if mode == "theme":
        active = next((directory for directory in theme_paths().values() if directory.name == current),
                      config / "theme/current")
        mode = "theme-light" if is_light(active) else "theme-dark"
    if mode in {"theme-dark", "theme-light"}:
        light = mode == "theme-light"
        for directory in directories:
            if is_light(directory) == light:
                mine = directory.parent == own("themes")
                entries.append({"name": tr('{name} (yours)', name=display_name(directory)) if mine else display_name(directory),
                                "value": directory.name,
                                "image": (directory / "preview.png").as_uri(),
                                "current": directory.name == current})
else:
    current = read_current("current-wallpaper")
    directory = config / "theme/current/backgrounds"
    import re
    def natural(path):
        return [int(part) if part.isdigit() else part.lower()
                for part in re.split(r"(\d+)", path.name)]
    # The theme's wallpapers, then the user's own (eitr_own_style).
    images = sorted(directory.rglob("*"), key=natural) + eitr_own_style.wallpapers(beside=directory)
    for image in images:
        if image.is_file() and image.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            entries.append({"name": image.name, "value": str(image),
                            "image": preview_url(image), "current": str(image) == current})
try:
    palette = tomllib.loads((config / "theme/current/colors.toml").read_text())
except (OSError, ValueError):
    palette = {}
print(json.dumps({"mode": mode, "items": entries, "accent": palette.get("accent", "#cdd6f4"),
                  "background": palette.get("background", "#202024"),
                  "foreground": palette.get("foreground", "#ffffff")}))
