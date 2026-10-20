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
from eitr_paths import code, config as user_config, theme_paths
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

    if mode in {"theme", "theme-category"}:
        for category, light in (("Dark", False), ("Light", True)):
            matching = [directory for directory in directories if is_light(directory) == light]
            if not matching:
                continue
            representative = next((directory for directory in matching if directory.name == current), None)
            if representative is None:
                preferred = "catppuccin-latte" if light else "catppuccin"
                representative = next((directory for directory in matching if directory.name == preferred), matching[0])
            category_image = code("quickshell/desktop-bar/assets/appearance") / f"{category.lower()}.png"
            if not category_image.is_file():
                category_image = category_image.with_suffix(".jpg")
            if not category_image.is_file():
                category_image = representative / "preview.png"
            try:
                with Image.open(category_image) as image:
                    aspect_ratio = image.width / image.height
            except (OSError, ValueError):
                aspect_ratio = 16 / 9
            entries.append({"name": category, "value": category.lower(),
                            "image": category_image.as_uri(),
                            "aspectRatio": aspect_ratio,
                            "current": representative.name == current})
    elif mode in {"theme-dark", "theme-light"}:
        light = mode == "theme-light"
        for directory in directories:
            if is_light(directory) == light:
                entries.append({"name": display_name(directory),
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
    for image in sorted(directory.rglob("*"), key=natural):
        if image.is_file() and image.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            entries.append({"name": image.name, "value": str(image),
                            "image": preview_url(image), "current": str(image) == current})
try:
    palette = tomllib.loads((config / "theme/current/colors.toml").read_text())
except (OSError, ValueError):
    palette = {}
print(json.dumps({"items": entries, "accent": palette.get("accent", "#cdd6f4"),
                  "foreground": palette.get("foreground", "#ffffff")}))
