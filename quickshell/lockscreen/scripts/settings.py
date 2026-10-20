#!/usr/bin/env python3
import configparser
import json
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import cache, code, config as user_config
from eitr_i18n import tr
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STATE = user_config("lockscreen/selected")
LOGIN_HELPERS = (Path('/usr/lib/eitr/desktop-login-select'), Path('/usr/local/bin/desktop-login-select'))
NAMES = {
    'clockwork/neo-orbital': 'Clockwork Neo Orbital',
    'clockwork/tape': 'Clockwork Tape',
    'girl-coffee': 'Girl · Coffee',
    'girl-pillow': 'Girl · Pillow',
    'material-you-dark': 'Material Dark',
    'material-you': 'Material Light',
    'nothing': 'Nothing',
    'theme-wallpaper': 'Theme Wallpaper',
}


def designs():
    return {
        str(path.parent.relative_to(ROOT / "themes")): NAMES.get(str(path.parent.relative_to(ROOT / "themes")), path.parent.name)
        for path in sorted((ROOT / "themes").rglob("Main.qml"))}


def selected():
    try:
        value = STATE.read_text().strip()
    except OSError:
        value = "hyprlock"
    return value if value in designs() else "hyprlock"


def theme_wallpaper():
    candidates = []
    try:
        candidates.append(Path(cache('current-wallpaper').read_text().strip()))
    except OSError:
        pass
    candidates.append(cache('current-wallpaper-image'))
    candidates.extend(sorted(user_config('theme/current/backgrounds').glob('*')))
    candidates.append(code('themes/norse/backgrounds/01-eitr-runestone.png'))
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
            if resolved.is_file() and resolved.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
                return resolved
        except (OSError, RuntimeError):
            continue
    return None


def design_config(value):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read(ROOT / "themes" / value / "theme.conf")
    settings = dict(parser["General"]) if parser.has_section("General") else {}
    if value == 'theme-wallpaper':
        wallpaper = theme_wallpaper()
        settings['background'] = wallpaper.as_uri() if wallpaper else ''
    return settings


def login_wallpaper_jpeg(limit=(3840, 2160)):
    """The current wallpaper as a JPEG for the login screen, which cannot read the home folder."""
    import io
    from PIL import Image
    source = theme_wallpaper()
    if source is None:
        return None
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail(limit, Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=90)
    return output.getvalue()


def give_login_wallpaper(helper):
    """Hand the current wallpaper to the root-owned login helper (Theme Wallpaper design)."""
    data = login_wallpaper_jpeg()
    if data is None:
        return True
    result = subprocess.run(['sudo', '-n', str(helper), '--wallpaper'], input=data, capture_output=True)
    return result.returncode == 0


def refresh_login_wallpaper():
    """After a wallpaper change: keep the login screen's copy current when it shows the wallpaper."""
    if selected() != 'theme-wallpaper':
        return
    helper = next((path for path in LOGIN_HELPERS if path.is_file()), None)
    if helper is not None:
        give_login_wallpaper(helper)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "current"
    if command == "current":
        print(selected())
        return
    if command == "list":
        for value, label in designs().items():
            print(f"{value}\t{label}")
        return
    if command == "refresh-login":
        refresh_login_wallpaper()
        return
    if command not in ("select", "config", "preview"):
        raise SystemExit('Unknown command')
    if len(sys.argv) < 3:
        raise SystemExit('Usage: settings.py {command} DESIGN'.format(command=f'{command}'))
    value = sys.argv[2]
    if value not in designs():
        raise SystemExit('Unknown lockscreen')
    if command == "select":
        # The packaged helper first; an older installation's sudo rule may still
        # allow only the previous /usr/local helper until its login setup reruns.
        helpers = [path for path in LOGIN_HELPERS if path.is_file()]
        errors = []
        for helper in helpers:
            if value == 'theme-wallpaper' and not give_login_wallpaper(helper):
                errors.append(f'{helper} could not store the login wallpaper')
                continue
            result = subprocess.run(['sudo', '-n', str(helper), value], capture_output=True, text=True)
            if result.returncode == 0:
                break
            errors.append(result.stderr.strip())
        else:
            if helpers:
                raise SystemExit(tr('Login screen could not be updated: {errors}', errors='; '.join(errors)))
        STATE.parent.mkdir(parents=True, exist_ok=True)
        temporary = STATE.with_suffix(".tmp")
        temporary.write_text(value + "\n")
        temporary.replace(STATE)
    elif command == "config":
        print(json.dumps(design_config(value)))
    elif command == "preview":
        wallpaper = theme_wallpaper() if value == 'theme-wallpaper' else None
        print(wallpaper or ROOT / 'themes' / value / 'preview.png')
    else:
        raise SystemExit('Unknown command')


if __name__ == "__main__":
    main()
