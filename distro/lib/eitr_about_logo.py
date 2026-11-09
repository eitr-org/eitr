"""About's logo preference shares the machine-local desktop style settings."""
from eitr_paths import config, read_settings, write_settings
from eitr_choice_lists import ABOUT_LOGOS


def current(config_home=None):
    path = config_home / 'eitr/style.json' if config_home is not None else config('eitr/style.json')
    try:
        value = read_settings(path).get('aboutLogo')
    except (OSError, ValueError):
        return 'emblem'
    return value if any(choice['id'] == value for choice in ABOUT_LOGOS) else 'emblem'


def select(value):
    if not any(choice['id'] == value for choice in ABOUT_LOGOS):
        raise ValueError('Unknown About logo')
    write_settings(config('eitr/style.json'), {'aboutLogo': value})
