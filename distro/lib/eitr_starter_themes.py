"""Resume the one-time starter theme installs enrolled by fresh account setup."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys

from eitr_paths import code_root, read_settings, state, theme_paths, write_settings
from eitr_plugin_manifest import identifier, unique_object


def load(path=None):
    path = path or code_root() / 'distro/starter-themes.json'
    rows = json.loads(Path(path).read_text(), object_pairs_hook=unique_object)
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected a starter theme list')
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'kind', 'channel', 'id'}
                or row['kind'] != 'themes' or row['channel'] not in ('official', 'community')):
            raise ValueError('Invalid starter theme entry')
        theme_id = identifier(row['id'])
        if theme_id in seen:
            raise ValueError('Duplicate starter theme ID')
        seen.add(theme_id)
    return rows


def progress_path():
    return state('eitr/starter-themes.json')


def enqueue():
    path = progress_path()
    install_record = path.with_name('installed-paths')
    if path.exists() or install_record.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        if not path.exists() and not install_record.exists():
            # Save the original selection for this account's first login.
            write_settings(path, {'themes': load(), 'outcomes': {}})


def finish():
    """Return true when there is no work left, false when a retry is needed."""
    path = progress_path()
    if not path.exists():
        return True
    with path.with_suffix('.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return install_pending(path)


def install_pending(path):
    progress = read_settings(path)
    rows, outcomes = progress['themes'], progress['outcomes']
    pending = [row for row in rows if row['id'] not in outcomes]
    if not pending:
        return True

    from eitr_store_backends import dispatch
    from eitr_store_content import refresh_community_index
    from eitr_theme_packages import ThemeUnavailable

    community_ready = None
    for row in pending:
        theme_id = row['id']
        try:
            if theme_id not in theme_paths():
                if row['channel'] == 'community':
                    if community_ready is None:
                        community_ready = False
                        refresh_community_index()
                        community_ready = True
                    if not community_ready:
                        continue
                dispatch('install', {'kind': row['kind'], 'channel': row['channel'], 'ids': [theme_id]})
            outcomes[theme_id] = 'installed'
        except ThemeUnavailable:
            outcomes[theme_id] = 'unavailable'
        except (OSError, ValueError, subprocess.SubprocessError):
            # Network, validation and Store lock failures leave this entry pending.
            continue
        write_settings(path, {'outcomes': outcomes})
    return all(row['id'] in outcomes for row in rows)


if __name__ == '__main__':
    if sys.argv[1:] == ['--enqueue']:
        enqueue()
    else:
        raise SystemExit(0 if finish() else 1)
