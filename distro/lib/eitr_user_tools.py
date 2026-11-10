"""Per-user tools Eitr installs by default with their official installers.

At login, in the background, each tool that is neither recorded nor present runs its
vendor's install script (URL in installers.json). Success, or finding the tool already
installed, is recorded once, so a tool the person later removes is never reinstalled.
A failure (offline, for example) records nothing and retries at the next login.
"""
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from eitr_paths import code, read_settings, state, write_settings

# Tool id → the command it installs and the variable that sets its installer's target folder.
# Every tool goes to ~/.local/bin, which Eitr's shell profile already puts on PATH.
TOOLS = {
    'herdr': {'command': 'herdr', 'folder_variable': 'HERDR_INSTALL_DIR'},
}
TIMEOUT = 300


def record():
    return state('eitr/user-tools.json')


def installed(tool):
    command = TOOLS[tool]['command']
    return bool(shutil.which(command)) or (Path.home() / '.local/bin' / command).is_file()


def installer_url(tool):
    software = code('walker/scripts/actions/install/software.py')
    return subprocess.run([sys.executable, str(software), 'installer', tool], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()


def run_installer(tool):
    url = installer_url(tool)
    if not url.startswith('https://'):
        raise ValueError(f'{tool}: installer must be an https URL')
    with tempfile.TemporaryDirectory(prefix='eitr-user-tool-') as directory:
        script = Path(directory) / 'install.sh'
        subprocess.run(['curl', '--proto', '=https', '--proto-redir', '=https', '--tlsv1.2', '-fsSL', url, '-o', str(script)],
                       check=True, timeout=60, stdin=subprocess.DEVNULL, capture_output=True)
        subprocess.run(['sh', str(script)], check=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL, capture_output=True,
                       env={**os.environ, TOOLS[tool]['folder_variable']: str(Path.home() / '.local/bin')})


def ensure(*, runner=run_installer):
    """Install every unrecorded, missing tool once; returns the tools installed now."""
    done = []
    record().parent.mkdir(parents=True, exist_ok=True)
    # Two sessions logging in together must not run the same installer twice.
    with record().with_suffix('.lock').open('w') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return done
        recorded = read_settings(record()).get('tools', {})
        for tool in TOOLS:
            if tool in recorded:
                continue
            if not installed(tool):
                try:
                    runner(tool)
                except (OSError, ValueError, subprocess.SubprocessError):
                    continue
                if not installed(tool):
                    continue
                done.append(tool)
            recorded = {**recorded, tool: 'installed'}
            write_settings(record(), {'tools': recorded})
    return done


def start():
    """Start ensure() in the background so login never waits for the network."""
    recorded = read_settings(record()).get('tools', {})
    if all(tool in recorded for tool in TOOLS):
        return
    subprocess.Popen([sys.executable, str(Path(__file__).resolve())], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


if __name__ == '__main__':
    try:
        ensure()
    except (OSError, ValueError):
        pass
