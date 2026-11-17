"""Share the login screen: a separate Sunshine that runs only while nobody is signed in.

`eitr-login-share.service` (a system unit, disabled until the switch is turned on) runs
`eitr-system remote-login-run`, which watches logind and starts Sunshine as the system
account `eitr-loginshare` while no user session exists on seat0, and stops it the moment
one starts. It streams with the sharing account's own identity (certificate, paired
devices), copied at every start into a root-owned folder, so Moonlight sees the same PC
before and after sign-in and devices unpaired there stop working here too. No audio.
See distro/REMOTE-ACCESS.md.
"""
import json
import os
from pathlib import Path
import pwd
import shutil
import signal
import subprocess
import threading
import time

from eitr_i18n import tr
import eitr_remote as remote

UNIT = 'eitr-login-share.service'
ACCOUNT = 'eitr-loginshare'
# Outside remote-access/ (root only): the account must reach its own folder.
STATE = Path('/var/lib/eitr/login-share')
STATUS = Path('/run/eitr/login-share.json')
SUNSHINE_FILES = ('sunshine_state.json', 'credentials/cacert.pem', 'credentials/cakey.pem')
# The greeter has no PipeWire or D-Bus session (Sunshine aborts on a tray without one),
# and the web UI stays local like the user's.
SETTINGS = {'upnp': 'off', 'origin_web_ui_allowed': 'pc', 'port': '47989', 'capture': 'kms', 'stream_audio': 'false',
            'system_tray': 'disabled'}
STOP_SECONDS = 5
# A Sunshine that keeps exiting is retried after a growing pause, up to this many seconds.
LONGEST_PAUSE = 300


def owner():
    """The sharing account Set Up Sharing recorded, ready to stream (password step done)."""
    previous = remote.journal('sunshine')
    if not previous:
        raise RuntimeError(tr('Run Sharing Setup first.'))
    if not previous.get('armed'):
        raise RuntimeError(tr('Start sharing once and set Sunshine’s password first.'))
    return previous['user']


def user_signed_in(sessions):
    """A signed-in desktop or console on the local seat; SSH sessions have no seat."""
    return any(session.get('seat') == 'seat0' and str(session.get('class', '')).startswith('user')
               for session in sessions)


def sessions():
    result = subprocess.run(['loginctl', 'list-sessions', '--json=short'], capture_output=True, text=True, timeout=5, check=True)
    return json.loads(result.stdout or '[]')


def read_private(path):
    """Read a file in the sharing account's home as root without following a link anywhere
    below the root folder, so the account cannot point root at another file."""
    path = Path(path)
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        file_descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
    finally:
        os.close(descriptor)
    with os.fdopen(file_descriptor, 'rb') as stream:
        return stream.read()


def copy_identity(name, target=STATE):
    """The sharing account's Sunshine identity and paired devices, refreshed before each start."""
    source = Path(pwd.getpwnam(name).pw_dir) / '.config/sunshine'
    account = pwd.getpwnam(ACCOUNT)
    for relative in SUNSHINE_FILES:
        data = read_private(source / relative)
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = path.with_name(path.name + '.new')
        temporary.write_bytes(data)
        temporary.chmod(0o600)
        os.chown(temporary, account.pw_uid, account.pw_gid)
        temporary.replace(path)
    settings = {**SETTINGS, 'file_state': target / 'sunshine_state.json', 'credentials_file': target / 'sunshine_state.json',
                'cert': target / 'credentials/cacert.pem', 'pkey': target / 'credentials/cakey.pem',
                'file_apps': target / 'apps.json', 'log_path': target / 'sunshine.log',
                'sunshine_name': os.uname().nodename}
    remote.write(target / 'sunshine.conf', ''.join(f'{key} = {value}\n' for key, value in settings.items()), 0o600)
    remote.write(target / 'apps.json', json.dumps({'env': {}, 'apps': [{'name': 'Desktop', 'image-path': 'desktop.png'}]}) + '\n', 0o600)
    for path in [target, *target.rglob('*')]:
        os.chown(path, account.pw_uid, account.pw_gid)


def paired_devices(name):
    try:
        state = json.loads(read_private(Path(pwd.getpwnam(name).pw_dir) / '.config/sunshine/sunshine_state.json'))
    except (OSError, ValueError):
        return 0
    return len(state.get('root', {}).get('named_devices', []))


def enable(name):
    remote.account(name)
    if owner() != name:
        raise RuntimeError(tr('Remote access belongs to another desktop user'))
    if not remote.capture_ready(name):
        raise RuntimeError(tr('Run Sharing Setup first.'))
    if not paired_devices(name):
        raise RuntimeError(tr('Pair a device with your sharing first; the login screen accepts the same devices.'))
    print(tr('The login screen can then be streamed by the devices paired with your sharing, by anyone holding them.'))
    print(tr('Signing in still needs an account password. Sharing stops the moment someone signs in.'))
    remote.confirmed()
    try:
        pwd.getpwnam(ACCOUNT)
    except KeyError:
        remote.run(['useradd', '--system', '--no-create-home', '--home-dir', str(STATE), '--shell', '/usr/bin/nologin',
                    '--comment', 'Eitr login screen sharing', '--groups', ','.join([remote.SHARING_GROUP, 'video', 'render']), ACCOUNT])
    try:
        STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
        copy_identity(name)
        remote.save('login-screen', {'user': name})
        remote.run(['systemctl', 'enable', '--now', UNIT])
    except Exception:
        disable(name, ask=False)
        raise


def disable(name=None, ask=True):
    """Stop and remove everything the switch added; always allowed."""
    if name:
        remote.account(name)
    if ask:
        remote.confirmed()
    subprocess.run(['systemctl', 'disable', '--now', UNIT], capture_output=True, check=False)
    try:
        pwd.getpwnam(ACCOUNT)
        remote.run(['userdel', ACCOUNT])
    except KeyError:
        pass
    shutil.rmtree(STATE, ignore_errors=True)
    (remote.STATE / 'login-screen.json').unlink(missing_ok=True)
    STATUS.unlink(missing_ok=True)


def user_sunshine_running():
    """The sharing account's own Sunshine still holds the ports after sign-out."""
    result = subprocess.run(['pgrep', '-x', 'sunshine'], capture_output=True, text=True, check=False)
    account = pwd.getpwnam(ACCOUNT).pw_uid
    return any(os.stat(f'/proc/{pid}').st_uid != account for pid in result.stdout.split() if Path(f'/proc/{pid}').exists())


class Runner:
    """Starts Sunshine while nobody is signed in and stops it as soon as someone is."""

    def __init__(self, name):
        self.name = name
        self.child = None
        self.wake = threading.Event()
        self.pause = 0
        self.next_start = 0.0
        self.started = 0.0

    def publish(self):
        """For diagnostics: whether the login screen is being shared right now (root only)."""
        remote.write(STATUS, json.dumps({'streaming': self.child is not None}) + '\n', 0o644)

    def start(self):
        if user_sunshine_running():
            return
        copy_identity(self.name)
        subprocess.run(['setfacl', '-m', f'u:{ACCOUNT}:rw', '/dev/uinput'], check=False)
        remote.sharing(self.name, True, owner='login-screen')
        self.started = time.monotonic()
        self.child = subprocess.Popen(['/usr/bin/sunshine', str(STATE / 'sunshine.conf')], cwd=STATE,
                                      user=ACCOUNT, group=ACCOUNT, extra_groups=[remote.SHARING_GROUP, 'video', 'render'],
                                      env={'HOME': str(STATE), 'PATH': '/usr/bin'}, stdin=subprocess.DEVNULL)
        self.publish()

    def stop(self):
        if self.child is None:
            return
        self.child.terminate()
        try:
            self.child.wait(STOP_SECONDS)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait()
        self.child = None
        remote.sharing(self.name, False, owner='login-screen')
        subprocess.run(['setfacl', '-x', f'u:{ACCOUNT}', '/dev/uinput'], check=False)
        self.publish()

    def watch(self):
        """Wake at once on logind's session signals; the loop still checks every few seconds."""
        monitor = subprocess.Popen(['gdbus', 'monitor', '--system', '--dest', 'org.freedesktop.login1',
                                    '--object-path', '/org/freedesktop/login1'], stdout=subprocess.PIPE, text=True)
        for line in monitor.stdout:
            if 'Session' in line:
                self.wake.set()

    def step(self, current_sessions, now=None):
        now = time.monotonic() if now is None else now
        if user_signed_in(current_sessions):
            self.stop()
            self.pause = 0
            return
        if self.child is not None and self.child.poll() is not None:
            # A Sunshine that ran a while before exiting starts over with a short pause.
            previous = 0 if now - self.started > 60 else self.pause
            self.pause = min(LONGEST_PAUSE, max(3, previous * 2))
            self.next_start = now + self.pause
            print(f'Sunshine exited with {self.child.returncode}; trying again in {self.pause} s', flush=True)
            self.stop()
        if self.child is None and now >= self.next_start:
            self.start()

    def run(self):
        signal.signal(signal.SIGTERM, lambda *_: (self.stop(), os._exit(0)))
        threading.Thread(target=self.watch, daemon=True).start()
        self.publish()
        while True:
            try:
                self.step(sessions())
            except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as error:
                print(error, flush=True)
                self.stop()
            self.wake.wait(3)
            self.wake.clear()


def run_service(_name=None):
    from eitr_policy import require
    require('remote_access')
    previous = remote.journal('login-screen')
    if not previous:
        raise RuntimeError(tr('Share the Login Screen is off.'))
    Runner(previous['user']).run()


def dispatch(action, name):
    operations = {'on': enable, 'off': disable, 'run': run_service}
    operations[action](name)
