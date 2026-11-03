"""Preserve former built-ins as official packages without holding up login."""
import fcntl
from pathlib import Path
import subprocess
import sys

from eitr_paths import cache, config, read_settings, state, theme_paths, write_settings
from eitr_theme_packages import Themes

THEMES = ('catppuccin', 'catppuccin-latte', 'daylight', 'gruvbox', 'jade',
          'kanagawa', 'moss', 'nord', 'one-dark-pro', 'rose-pine', 'stillwater', 'wisteria')
URL = 'https://github.com/eitr-org/eitr-themes'


def pending():
    return state('eitr/extra-themes-pending.json')


def enqueue():
    if not pending().exists():
        write_settings(pending(), {'remaining': list(THEMES)})


def current_theme():
    selected = read_settings(config('eitr/appearance.json')).get('theme')
    if selected:
        return selected
    for marker in (cache('current-theme'), Path.home() / '.cache/current-theme'):
        if marker.is_file():
            return marker.read_text().strip()
    return None


def retry(*, backend=None, url=URL):
    """One sparse installation transaction; successful packages are never replayed."""
    if not pending().exists():
        return []
    # A second session must not queue behind an in-progress download.
    with pending().with_suffix('.lock').open('w') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return []
        if not pending().exists():
            return []
        backend = backend or Themes()
        remaining = read_settings(pending())['remaining']
        if not isinstance(remaining, list) or any(theme not in THEMES for theme in remaining):
            raise ValueError('Invalid extra themes migration state')
        # Record progress before fetching: a package removed after partial success
        # must not be restored by a later retry.
        # Any theme with that ID already counts: a package, the user's own or an override.
        present = theme_paths()
        missing = [theme for theme in remaining if theme not in present and not (backend.folder / theme).exists()]
        current = current_theme()
        missing.sort(key=lambda theme: theme != current)
        write_settings(pending(), {'remaining': missing})
        if missing:
            backend.install(url, missing)
        pending().unlink()
        return missing


def start_retry():
    if pending().exists():
        subprocess.Popen([sys.executable, str(Path(__file__).resolve())],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)


if __name__ == '__main__':
    try:
        retry()
    except (OSError, ValueError, subprocess.SubprocessError):
        # Keep the bounded retry for the next login; no notification or desktop writes.
        pass
