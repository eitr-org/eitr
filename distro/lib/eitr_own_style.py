"""The user's own wallpapers, themes and lockscreens.

They live only on this computer, under $XDG_DATA_HOME/eitr/{wallpapers,themes,lockscreens}
(eitr_paths.own). Package updates, layout adoption and the theme generators never
write there, and nothing here uploads or shares them. Pictures come from a local
file or an https address; each is decoded before a copy is kept.
"""
import colorsys
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request

from eitr_i18n import tr
from eitr_paths import code, code_root, own, read_settings, write_settings

MAX_BYTES = 50 * 1024 * 1024
MAX_PIXELS = 120_000_000
MIN_SIDE = 64
TIMEOUT = 20
FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MARKER = "own-theme.json"
# A shipped theme to return to when the current own theme is deleted: the one used
# before it was created, else the fresh-install default (distro/user-defaults.json).
DEFAULT_THEME = "afterglow"
# Lockscreen designs that show a picture and accept an accent and a greeting.
LOCK_DESIGNS = ("theme-wallpaper", "material-you-dark", "material-you")
LOCK_PREFIX = "user:"
EDITABLE = ("accent", "background", "foreground", "color1", "color2", "color3", "color4", "color5", "color6")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


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


def theme_builder():
    """themes/build-theme-files.py: the btop and Neovim writers shipped themes use."""
    return _module("themes/build-theme-files.py", "eitr_theme_builder")


# Names and pictures

def clean_name(name):
    name = " ".join(str(name).split())
    if not name or len(name) > 40 or any(ord(character) < 32 or ord(character) == 127 for character in name):
        raise ValueError(tr('Use a name of 1 to 40 characters.'))
    return name


def slug(name):
    value = re.sub(r"[^a-z0-9]+", "-", clean_name(name).lower()).strip("-")[:40].strip("-")
    if not value:
        raise ValueError(tr('The name needs at least one letter or digit.'))
    return value


def check_source(source):
    """A local picture path or an https address; raises ValueError otherwise."""
    source = str(source).strip()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", source):
        parts = urllib.parse.urlsplit(source)
        if parts.scheme.lower() != "https" or not parts.hostname:
            raise ValueError(tr('Use an https address or a file on this computer.'))
        if parts.username is not None or parts.password is not None:
            raise ValueError(tr('Do not put login credentials in the address.'))
        return source
    path = Path(source).expanduser()
    if not path.is_file():
        raise ValueError(tr('No picture file at {path}.', path=f'{path}'))
    return str(path.resolve())


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code_, message, headers, address):
        if urllib.parse.urlsplit(address).scheme.lower() != "https":
            raise ValueError(tr('The address redirected away from https.'))
        return super().redirect_request(request, response, code_, message, headers, address)


def download(url, opener=None):
    """The bytes at an https address, refusing anything larger than MAX_BYTES."""
    url = check_source(url)
    if not url.lower().startswith("https://"):
        raise ValueError(tr('Use an https address or a file on this computer.'))
    opener = opener or urllib.request.build_opener(_HttpsOnly())
    request = urllib.request.Request(url, headers={"User-Agent": "Eitr"})
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            length = response.headers.get("Content-Length")
            if length and length.isdigit() and int(length) > MAX_BYTES:
                raise ValueError(tr('The picture is larger than 50 MB.'))
            data = response.read(MAX_BYTES + 1)
    except OSError as error:
        raise ValueError(tr('Could not download the picture: {error}', error=f'{error}')) from error
    if len(data) > MAX_BYTES:
        raise ValueError(tr('The picture is larger than 50 MB.'))
    return data


def picture_format(data):
    """The decoded picture's suffix; raises ValueError unless it is a whole JPEG, PNG or WebP."""
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as image:
            kind = image.format
            width, height = image.size
            if kind not in FORMATS:
                raise ValueError(tr('Use a JPEG, PNG or WebP picture.'))
            if width * height > MAX_PIXELS:
                raise ValueError(tr('The picture has too many pixels.'))
            if min(width, height) < MIN_SIDE:
                raise ValueError(tr('The picture is too small.'))
            image.load()
    except ValueError:
        raise
    except (OSError, SyntaxError, Image.DecompressionBombError) as error:
        raise ValueError(tr('This is not a picture Eitr can read.')) from error
    return FORMATS[kind]


def read_source(source, opener=None):
    source = check_source(source)
    if source.lower().startswith("https://"):
        return download(source, opener)
    path = Path(source)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(tr('The picture is larger than 50 MB.'))
    return path.read_bytes()


def store_picture(source, directory, stem, opener=None):
    """Keep a verified copy of the picture in directory; returns its path."""
    data = read_source(source, opener)
    suffix = picture_format(data)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target, number = directory / (stem + suffix), 2
    while target.exists():
        target, number = directory / f"{stem}-{number}{suffix}", number + 1
    descriptor, temporary = tempfile.mkstemp(prefix=".picture-", dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def source_stem(source):
    name = Path(urllib.parse.urlsplit(source).path if "://" in source else source).stem
    try:
        return slug(name)
    except ValueError:
        return "wallpaper"


# Wallpapers

def wallpapers():
    directory = own("wallpapers")
    if not directory.is_dir():
        return []
    return sorted((path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in SUFFIXES),
                  key=lambda path: (path.stem.casefold(), path.suffix))


def add_wallpaper(source, opener=None):
    return store_picture(source, own("wallpapers"), source_stem(source), opener)


def own_wallpaper(path):
    """The path if it is one of the user's wallpapers, else ValueError."""
    path = Path(path)
    if path.parent.resolve() != own("wallpapers").resolve() or not path.is_file():
        raise ValueError(tr('Not one of your wallpapers'))
    return path


# Palettes

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
    pixels = list(image.getdata())
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


KEY_ORDER = ("accent", "cursor", "foreground", "background", "selection_foreground", "selection_background",
             *(f"color{index}" for index in range(16)))


def render_colors(colors):
    lines = [f'{key} = "{colors[key]}"' for key in KEY_ORDER[:6]] + [""]
    lines += [f'{key} = "{colors[key]}"' for key in KEY_ORDER[6:]]
    return "\n".join(lines) + "\n"


# Integration files, chosen from the palette

YARU = ((0, "Yaru-red"), (25, "Yaru-wartybrown"), (48, "Yaru-yellow"), (75, "Yaru-olive"), (110, "Yaru-sage"),
        (175, "Yaru-prussiangreen"), (215, "Yaru-blue"), (270, "Yaru-purple"), (315, "Yaru-magenta"), (360, "Yaru-red"))
KVANTUM = ((0, "red"), (25, "peach"), (45, "yellow"), (115, "green"), (172, "teal"), (195, "sapphire"),
           (217, "blue"), (235, "lavender"), (267, "mauve"), (316, "pink"), (360, "red"))


def nearest(table, hue):
    degrees = hue * 360
    return min(table, key=lambda item: abs(item[0] - degrees))[1]


def reference_integration(light):
    """The integration of a shipped theme whose Neovim colors come from its palette."""
    integrations = json.loads(code("themes/integrations.json").read_text())
    for theme, integration in sorted(integrations.items()):
        driven = any(plugin.get("palette") for plugin in integration["neovim"]["plugins"])
        if driven and (code_root() / "themes" / theme / "light.mode").is_file() == light:
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
    extended = dict(colors, darker_background=mix(colors["background"], shade, 0.35),
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


# Themes

def shipped_themes():
    root = code_root() / "themes"
    return {path.name for path in root.iterdir() if (path / "colors.toml").is_file()} if root.is_dir() else set()


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
    if identifier in shipped_themes() or identifier in own_themes():
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
        previous = previous if previous in shipped_themes() else ""
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


def fallback_theme(identifier):
    try:
        previous = json.loads((theme_dir(identifier) / MARKER).read_text()).get("previous", "")
    except (OSError, ValueError, AttributeError):
        previous = ""
    return previous if previous in shipped_themes() else DEFAULT_THEME


# Lockscreens

def own_lockscreens():
    directory = own("lockscreens")
    found = {}
    if not directory.is_dir():
        return found
    for path in sorted(directory.iterdir()):
        try:
            settings = read_settings(path / "lockscreen.json")
        except (OSError, ValueError):
            continue
        picture = path / str(settings.get("picture", ""))
        if (re.fullmatch(r"[a-z0-9-]{1,40}", path.name) and settings.get("design") in LOCK_DESIGNS
                and picture.parent == path and picture.is_file()):
            found[LOCK_PREFIX + path.name] = dict(settings, picture=str(picture), directory=str(path))
    return found


def lockscreen(value):
    found = own_lockscreens().get(value)
    if found is None:
        raise ValueError(tr('Not one of your lockscreens'))
    return found


def create_lockscreen(name, design, source, accent="", greeting="", opener=None):
    name = clean_name(name)
    if design not in LOCK_DESIGNS:
        raise ValueError(tr('Choose one of the listed designs.'))
    accent = accent.strip()
    if accent and not accent.startswith("#"):
        accent = "#" + accent
    if accent and not HEX.match(accent):
        raise ValueError(tr('Enter a color as six hex digits, for example #2bb87a.'))
    greeting = " ".join(greeting.split())
    if len(greeting) > 80:
        raise ValueError(tr('Keep the greeting under 80 characters.'))
    identifier = slug(name)
    root = own("lockscreens")
    if (root / identifier).exists():
        raise ValueError(tr('A lockscreen named {name} already exists.', name=f'{name}'))
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{identifier}-", dir=root))
    try:
        picture = store_picture(source, staging, "picture", opener)
        write_settings(staging / "lockscreen.json", {"name": name, "design": design, "picture": picture.name,
                                                     "accent": accent.lower(), "greeting": greeting})
        os.chmod(staging, 0o755)
        os.rename(staging, root / identifier)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return LOCK_PREFIX + identifier


def delete_lockscreen(value):
    shutil.rmtree(lockscreen(value)["directory"])
