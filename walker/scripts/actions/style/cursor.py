#!/usr/bin/env python3
"""One cursor family with automatic or explicitly selected light/dark colors."""
import configparser
from io import StringIO
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
from eitr_paths import code, config as user_config, read_settings, write_settings
from eitr_i18n import tr, mark as menu_mark
import shutil
import subprocess
import struct
import tempfile

HOME = Path.home()
CONFIG = user_config()
PREFERENCE = CONFIG / "eitr/cursor.json"
FAMILIES = {
    "bibata": {"dark": "Bibata-Modern-Classic", "light": "Bibata-Modern-Ice"},
    "breeze": {"dark": "breeze_cursors", "light": "Breeze_Light"},
    "dmz": {"dark": "Vanilla-DMZ-AA", "light": "Vanilla-DMZ"},
}
DEFAULTS = {"family": "bibata", "color": "auto", "size": 24}
SIZES = (16, 24, 32, 48, 64)
LABELS = {"bibata": "Bibata Modern", "breeze": "Breeze", "dmz": "Vanilla DMZ"}


def read():
    data = read_settings(PREFERENCE, DEFAULTS)
    try:
        if not isinstance(data, dict):
            return dict(DEFAULTS)
    except (OSError, ValueError):
        return dict(DEFAULTS)
    return {**data, "family": data.get("family") if isinstance(data.get("family"), str) and data["family"] in FAMILIES else "bibata",
            "color": data.get("color") if isinstance(data.get("color"), str) and data["color"] in ("auto", "light", "dark") else "auto",
            "size": data.get("size") if type(data.get("size")) is int and data["size"] in SIZES else 24}


def resolve(choice):
    color = choice["color"]
    if color == "auto":
        color = "light" if (CONFIG / "theme/current/light.mode").exists() else "dark"
    return FAMILIES[choice["family"]][color]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".cursor-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as file:
            file.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def ini(path, section, values):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read(path)
    if not parser.has_section(section):
        parser.add_section(section)
    for key, value in values.items():
        parser.set(section, key, str(value))
    output = StringIO()
    parser.write(output, space_around_delimiters=False)
    write(path, output.getvalue())


def theme_directory(theme):
    roots = [HOME / ".icons", HOME / ".local/share/icons", Path("/usr/local/share/icons"), Path("/usr/share/icons")]
    return next((root / theme for root in roots if (root / theme / "cursors").is_dir()), None)


def installed(theme):
    return theme_directory(theme) is not None


def preview(theme):
    directory = theme_directory(theme)
    if directory is None:
        return ""
    source = directory / "cursors/left_ptr"
    try:
        data = source.read_bytes()
        magic, header, version, count = struct.unpack_from("<4I", data)
        if magic != 0x72756358 or count > 1024 or header < 16:
            return ""
        images = [struct.unpack_from("<3I", data, header + i * 12) for i in range(count)]
        images = [entry for entry in images if entry[0] == 0xfffd0002]
        if not images:
            return ""
        kind, size, offset = min(images, key=lambda entry: abs(entry[1] - 32))
        chunk, kind, size, version, width, height, hot_x, hot_y, delay = struct.unpack_from("<9I", data, offset)
        if chunk < 36 or not (0 < width <= 512 and 0 < height <= 512):
            return ""
        pixels = data[offset + chunk:offset + chunk + width * height * 4]
        from PIL import Image
        image = Image.frombytes("RGBA", (width, height), pixels, "raw", "BGRA")
        target = HOME / ".cache/eitr/cursor-previews" / (theme + ".png")
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target)
        return str(target)
    except (OSError, ValueError, struct.error, ImportError):
        return ""


def entries(group):
    choice = read()
    rows = []
    values = (LABELS if group == "family" else
              {size: f"{size} px" + (" (Default)" if size == 24 else "") for size in SIZES}
              if group == "size" else {"auto": "Auto", "dark": "Dark", "light": "Light"})
    for value, label in values.items():
        candidate = {**choice, group: value}
        theme = resolve(candidate)
        selected = choice[group] == value
        rows.append({"id": str(value), "label": label, "selected": selected,
                     "icon": "\uf00c" if selected else preview(theme),
                     "detail": menu_mark("Set the cursor size") if group == "size" else theme})
    return rows if group == "size" else sorted(rows, key=lambda row: row["label"].casefold())


def sync(choice):
    theme, size = resolve(choice), choice["size"]
    if not installed(theme):
        raise ValueError(tr('Cursor theme {theme} is not installed. Install the corresponding cursor package first.', theme=f'{theme}'))
    for toolkit in ("gtk-3.0", "gtk-4.0"):
        ini(CONFIG / toolkit / "settings.ini", "Settings", {"gtk-cursor-theme-name": theme, "gtk-cursor-theme-size": size})
    ini(CONFIG / "kcminputrc", "Mouse", {"cursorTheme": theme, "cursorSize": size})
    for root in (HOME / ".icons", HOME / ".local/share/icons"):
        ini(root / "default/index.theme", "Icon Theme", {"Inherits": theme})
    environment = CONFIG / "hypr/cursor-env.conf"
    variables = f"env = XCURSOR_THEME,{theme}\nenv = XCURSOR_SIZE,{size}\nenv = HYPRCURSOR_SIZE,{size}\n"
    # Hyprland reads the variables at (re)load, so reload only when they change;
    # the login-time sync then leaves the compositor's state alone.
    changed = not environment.is_file() or environment.read_text() != variables
    if changed:
        write(environment, variables)
    if os.environ.get("EITR_NO_SESSION") != "1":
        commands = [["hyprctl", "setcursor", theme, str(size)],
                    *([["hyprctl", "reload"]] if changed else []),
                    ["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme],
                    ["gsettings", "set", "org.gnome.desktop.interface", "cursor-size", str(size)]]
        for command in commands:
            try:
                subprocess.run(command, check=True, timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.SubprocessError) as error:
                print(tr('Cursor preference saved; refresh failed: {error}', error=f'{error}'), file=sys.stderr)
    return {**choice, "theme": theme}


def main(args):
    choice = read()
    if len(args) == 2 and args[0] == "entries" and args[1] in ("family", "color", "size"):
        return entries(args[1])
    if args == ["status"]:
        return {**choice, "theme": resolve(choice)}
    if args == ["sync"]:
        return sync(choice)
    if len(args) == 3 and args[0] == "set":
        key, value = args[1:]
        if key == "size":
            value = int(value)
        valid = {"family": FAMILIES, "color": ("auto", "light", "dark"), "size": SIZES}
        if key not in valid or value not in valid[key]:
            raise ValueError(tr('Invalid cursor choice'))
        choice[key] = value
        result = sync(choice)
        write_settings(PREFERENCE, choice)
        return result
    raise ValueError('Usage: cursor.py status|sync|set family|color|size VALUE')


if __name__ == "__main__":
    try:
        print(json.dumps(main(sys.argv[1:])))
    except (OSError, ValueError, configparser.Error) as error:
        # Walker runs choices without a terminal; show why nothing changed.
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", tr('Cursor'), str(error)], check=False)
        raise SystemExit(str(error))
