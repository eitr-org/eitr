"""Build, edit and remove complete user-owned themes and their integration files."""
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from eitr_i18n import tr
from eitr_paths import code, code_root, own, theme_paths
from eitr_own_pictures import HEX, clean_name, slug, store_picture, source_stem
from eitr_own_palette import (
    _module, _contrasting, brighter, generate_palette, mix, palette_tools, render_colors, to_hls,
)

MARKER = "own-theme.json"
# The theme used before creation, else the fresh-install default (distro/user-defaults.json).
DEFAULT_THEME = "eitr"
EDITABLE = ("accent", "background", "foreground", "color1", "color2", "color3", "color4", "color5", "color6")
YARU = ((0, "Yaru-red"), (25, "Yaru-wartybrown"), (48, "Yaru-yellow"), (75, "Yaru-olive"), (110, "Yaru-sage"),
        (175, "Yaru-prussiangreen"), (215, "Yaru-blue"), (270, "Yaru-purple"), (315, "Yaru-magenta"), (360, "Yaru-red"))
KVANTUM = ((0, "red"), (25, "peach"), (45, "yellow"), (115, "green"), (172, "teal"), (195, "sapphire"),
           (217, "blue"), (235, "lavender"), (267, "mauve"), (316, "pink"), (360, "red"))

def theme_builder():
    """themes/build-theme-files.py: the btop and Neovim writers shipped themes use."""
    return _module("themes/build-theme-files.py", "eitr_theme_builder")


def nearest(table, hue):
    degrees = hue * 360
    return min(table, key=lambda item: abs(item[0] - degrees))[1]


def reference_integration(light):
    """The integration of a shipped theme whose Neovim colors come from its palette."""
    integrations = json.loads(code("themes/integrations.json").read_text())
    for theme, integration in sorted(integrations.items()):
        driven = integration["neovim"].get("eitr") or any(
            plugin.get("palette") for plugin in integration["neovim"].get("plugins", []))
        directory = code_root() / "themes" / theme
        if driven and (directory / "colors.toml").is_file() and (directory / "light.mode").is_file() == light:
            return integration
    raise ValueError(tr('No palette-driven theme integration is installed.'))


def write_preview(directory, colors):
    from PIL import Image, ImageDraw, ImageOps
    picture = next(iter(sorted((directory / "backgrounds").iterdir())), None)
    canvas = Image.new("RGB", (1280, 720), colors["background"])
    if picture is not None:
        with Image.open(picture) as source:
            canvas.paste(ImageOps.fit(source.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 640, 1280, 720), fill=colors["background"])
    keys = ("accent", "foreground", *(f"color{index}" for index in range(1, 7)))
    for index, key in enumerate(keys):
        left = 24 + index * 154
        draw.rounded_rectangle((left, 656, left + 138, 704), radius=10, fill=colors[key])
    canvas.save(directory / "preview.png", optimize=True)


def write_theme_files(directory, colors, light):
    builder = theme_builder()
    integration = reference_integration(light)
    hue, _, saturation = to_hls(colors["accent"])
    flavor = "latte" if light else "mocha"
    (directory / "colors.toml").write_text(render_colors(colors))
    (directory / "icons.theme").write_text(("Yaru" if saturation < 0.15 else nearest(YARU, hue)) + "\n")
    (directory / "dolphin.theme").write_text(f"catppuccin-{flavor}-{nearest(KVANTUM, hue)}\n")
    vscode = {key: value for key, value in integration["vscode"].items() if key != "vsix"}
    (directory / "vscode.json").write_text(json.dumps(vscode, indent=2, ensure_ascii=False) + "\n")
    # Palette-driven Neovim schemes also name these shades; derive them instead of storing them.
    shade = "#ffffff" if light else "#000000"
    extended = dict(colors, mode="light" if light else "dark", darker_background=mix(colors["background"], shade, 0.35),
                    lighter_background=mix(colors["background"], colors["foreground"], 0.06),
                    dark_foreground=colors["color8"])
    (directory / "neovim.lua").write_text(builder.neovim(directory.name, integration["neovim"], extended))
    (directory / "btop.theme").write_text(builder.btop(directory.name, colors))
    (directory / "rgb.color").write_text(colors["accent"][1:].upper() + "\n")
    marker = directory / "light.mode"
    if light:
        marker.touch()
    else:
        marker.unlink(missing_ok=True)
    write_preview(directory, colors)


def base_themes():
    return {theme_id for theme_id, directory in theme_paths().items()
            if not (directory / MARKER).is_file()}


def own_themes():
    directory = own("themes")
    if not directory.is_dir():
        return {}
    return {path.name: path for path in sorted(directory.iterdir()) if (path / MARKER).is_file()}


def theme_dir(identifier):
    if not re.fullmatch(r"[a-z0-9-]{1,40}", identifier or "") or identifier not in own_themes():
        raise ValueError(tr('Not one of your themes'))
    return own("themes") / identifier


def free_theme_name(name):
    identifier = slug(name)
    if identifier in base_themes() or (own("themes") / identifier).exists():
        raise ValueError(tr('A theme named {name} already exists.', name=f'{name}'))
    return identifier


def create_theme(name, source, mode=None, previous="", opener=None):
    """Write a complete theme from a picture; returns its directory. Applies nothing."""
    name = clean_name(name)
    identifier = free_theme_name(name)
    root = own("themes")
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{identifier}-", dir=root))
    try:
        picture = store_picture(source, staging / "backgrounds", source_stem(source), opener)
        colors, mode = generate_palette(picture, mode)
        (staging / "display-name").write_text(name + "\n")
        write_theme_files(staging, colors, mode == "light")
        previous = previous if previous in base_themes() else ""
        (staging / MARKER).write_text(json.dumps({"version": 1, "name": name, "mode": mode,
                                                  "previous": previous}, indent=2) + "\n")
        os.chmod(staging, 0o755)
        target = root / identifier
        os.rename(staging, target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


def theme_colors(identifier):
    return palette_tools().load(theme_dir(identifier))


def set_theme_color(identifier, key, value):
    """Change one color of an own theme and rewrite its derived files."""
    if key not in EDITABLE:
        raise ValueError(tr('This color cannot be changed here.'))
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    if not HEX.match(value):
        raise ValueError(tr('Enter a color as six hex digits, for example #2bb87a.'))
    tools = palette_tools()
    directory = theme_dir(identifier)
    colors = dict(tools.load(directory))
    colors[key] = value.lower()
    if key == "accent":
        colors["cursor"] = colors["accent"]
    light = tools.luminance(colors["background"]) > tools.luminance(colors["foreground"])
    if key.startswith("color"):
        colors["color" + str(int(key[5:]) + 8)] = brighter(colors[key], colors["background"], light, tools)
    if key == "background" and tools.contrast(colors["foreground"], colors["background"]) < 4.5:
        # A new background may flip dark and light; the text follows so it stays readable.
        colors["foreground"] = _contrasting(colors["foreground"], colors["background"], 7.0, tools)
    if key in ("foreground", "background"):
        if tools.contrast(colors["foreground"], colors["background"]) < 4.5:
            raise ValueError(tr('Text would be hard to read: foreground and background need more contrast.'))
        colors["color15"] = colors["foreground"]
    light = tools.luminance(colors["background"]) > tools.luminance(colors["foreground"])
    write_theme_files(directory, colors, light)
    return colors


def delete_theme(identifier):
    shutil.rmtree(theme_dir(identifier))
    shutil.rmtree(own("wallpapers") / "themes" / identifier, ignore_errors=True)


def fallback_theme(identifier):
    try:
        previous = json.loads((theme_dir(identifier) / MARKER).read_text()).get("previous", "")
    except (OSError, ValueError, AttributeError):
        previous = ""
    return previous if previous in base_themes() else DEFAULT_THEME
