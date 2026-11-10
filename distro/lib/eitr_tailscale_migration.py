"""Tailscale's bar icon and panel moved to the official Tailscale plugin: desktops that
have Tailscale get that plugin once, at a pinned reviewed commit, without holding up login."""
import fcntl
from pathlib import Path
import shutil
import subprocess
import sys

from eitr_i18n import tr
from eitr_paths import state, write_settings

URL = 'https://github.com/eitr-org/eitr-plugins'
PLUGIN = 'tailscale'
# The reviewed commit that added the plugin; installing it never follows a later HEAD.
COMMIT = '71c54e4dfb6b1169dc3034cfa6b403a83766c912'


def pending():
    return state('eitr/tailscale-plugin-pending.json')


def enqueue():
    if not pending().exists():
        write_settings(pending(), {'plugin': PLUGIN})


def retry(*, backend=None, notify=None):
    """Install the pinned plugin once. Network failures keep the pending file for the next
    login; a desktop without Tailscale, or with the plugin already, simply finishes."""
    if not pending().exists():
        return False
    with pending().with_suffix('.lock').open('w') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if not pending().exists():
            return False
        if backend is None:
            from eitr_plugin_runtime import Plugins
            backend = Plugins()
        installed = False
        if shutil.which('tailscale') and PLUGIN not in backend.records():
            review = backend.prepare_review(URL, plugin_id=PLUGIN, revision=COMMIT)
            installed = backend.confirm_review(review['token'])
        pending().unlink()
    if installed:
        (notify or send_notification)()
    return installed


def send_notification():
    subprocess.run(['notify-send', '-a', 'Eitr', tr('Tailscale is now a plugin'),
                    tr('Its icon and panel come from the official Tailscale plugin. Hide or remove it in Control Center > Plugins.')],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_retry():
    if pending().exists():
        subprocess.Popen([sys.executable, str(Path(__file__).resolve())],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['--enqueue']:
        enqueue()
        raise SystemExit(0)
    try:
        retry()
    except (OSError, ValueError, subprocess.SubprocessError):
        # Offline or a failed fetch: the pending file stays for the next login, quietly.
        pass
