"""Create, list and remove the user's picture-based lockscreens."""
import os
from pathlib import Path
import re
import shutil
import tempfile

from eitr_i18n import tr
from eitr_paths import own, read_settings, write_settings
from eitr_own_pictures import HEX, clean_name, slug, store_picture

# Designs that show a picture and accept an accent and a greeting.
LOCK_DESIGNS = ("theme-wallpaper", "material-you-dark", "material-you")
LOCK_PREFIX = "user:"

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
