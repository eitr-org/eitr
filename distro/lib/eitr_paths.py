"""EITR runtime paths: package code, user preferences and deliberate overrides."""
import json
import os
from pathlib import Path, PurePosixPath
import tempfile

# Source tools use the checkout; installed tools use the package prefix.
ROOT = Path(__file__).resolve().parents[2] if Path(__file__).parent.name == 'lib' and Path(__file__).parent.parent.name == 'distro' else Path('/usr/share/eitr')
COMPONENTS = {'desktop-bar', 'lockscreen', 'emoji-picker', 'calculator', 'wallpaper-transition'}


def xdg(name, fallback):
    value = os.environ.get(name, '')
    return Path(value) if os.path.isabs(value) else Path.home() / fallback


def config(relative=''):
    return xdg('XDG_CONFIG_HOME', '.config') / relative


def state(relative=''):
    return xdg('XDG_STATE_HOME', '.local/state') / relative


def cache(relative=''):
    return xdg('XDG_CACHE_HOME', '.cache') / relative


def data(relative=''):
    return xdg('XDG_DATA_HOME', '.local/share') / relative


def safe_relative(relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Expected a safe relative EITR path')
    return path


def code_root(root=None):
    supplied = os.environ.get('EITR_CODE_ROOT', '') if os.geteuid() != 0 else ''
    return Path(root or (supplied if os.path.isabs(supplied) else ROOT))


def code(relative, root=None):
    relative = safe_relative(relative)
    if os.geteuid() != 0:
        override = config('eitr/overrides') / relative
        if override.is_file():
            return override
    return code_root(root) / relative


def shell_path(component, root=None):
    if component not in COMPONENTS:
        raise ValueError('Unknown EITR shell component')
    override = config(f'eitr/overrides/quickshell/{component}')
    return override if (override / 'shell.qml').is_file() and os.geteuid() != 0 else code_root(root) / 'quickshell' / component


def theme_paths(root=None):
    """One whole-directory override per theme ID, user first."""
    merged = {}
    for directory in (code_root(root) / 'themes', config('themes')):
        if directory.is_dir():
            for entry in directory.iterdir():
                if entry.is_dir() and (entry / 'colors.toml').is_file():
                    merged[entry.name] = entry
    return dict(sorted(merged.items()))


def read_settings(path, defaults=None):
    try:
        settings = json.loads(Path(path).read_text())
    except FileNotFoundError:
        return dict(defaults or {}, version=1)
    if not isinstance(settings, dict) or type(settings.get('version', 1)) is not int or settings.get('version', 1) != 1:
        raise ValueError(f'Unsupported settings schema: {path}')
    return {**(defaults or {}), **settings, 'version': 1}


def write_settings(path, changes):
    """Atomic update that preserves compatible unknown preference fields."""
    path = Path(path)
    settings = {**read_settings(path), **changes, 'version': 1}
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            json.dump(settings, output, ensure_ascii=False, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return settings
