"""The offline default assistant: Ollama run by a per-user service, bound to 127.0.0.1."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

from eitr_i18n import tr
from eitr_paths import code, config, data, read_settings, state, write_settings

IDENTIFIER = 'local'
MODEL = 'qwen3:4b'  # Apache-2.0; qwen2.5:3b is under a non-commercial research licence
HOST = '127.0.0.1:11434'
URL = 'http://' + HOST
UNIT = 'eitr-ollama.service'
TIMEOUT = 180
START_TIMEOUT = 20
# Ollama keeps one manifest per model tag; its layers name the blobs it needs.
MANIFEST = Path('manifests/registry.ollama.ai/library/qwen3/4b')
DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')


def binary():
    found = shutil.which('ollama')
    return Path(found) if found else None


def unit_path():
    return config('systemd/user') / UNIT


def models():
    return data('eitr/ollama')


def record_path():
    """Whether setup installed the Ollama package, so removal only takes back its own install."""
    return state('eitr/local-assistant.json')


def model_present(folder=None):
    folder = folder or models()
    try:
        manifest = json.loads((folder / MANIFEST).read_text())
        layers = [manifest['config'], *manifest['layers']]
        digests = [layer['digest'] for layer in layers]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return all(isinstance(digest, str) and DIGEST.match(digest)
               and (folder / 'blobs' / digest.replace(':', '-')).is_file() for digest in digests)


def installed():
    return binary() is not None and unit_path().is_file() and model_present()


def present():
    """Anything setup leaves behind, complete or not, that removal can clean up."""
    return unit_path().exists() or models().exists() or record_path().exists()


def unit_content(executable, folder):
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$') + '"'
    return ('[Unit]\nDescription=Eitr local assistant (Ollama)\n\n[Service]\nType=exec\n'
            'ExecStart=' + quote(str(executable)) + ' serve\n'
            'Environment=' + quote('OLLAMA_HOST=' + HOST) + '\n'
            'Environment=' + quote('OLLAMA_MODELS=' + str(folder)) + '\n'
            'NoNewPrivileges=yes\nRestart=on-failure\nRestartSec=5\n')


def systemctl(*arguments):
    return subprocess.run(['systemctl', '--user', *arguments], capture_output=True, text=True,
                          timeout=60, check=False)


def opener():
    # The service is on this machine; a proxy from the environment must never see a prompt.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def responding():
    try:
        with opener().open(URL + '/api/version', timeout=2) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


def ensure_running(wait=START_TIMEOUT):
    if not unit_path().is_file():
        raise ValueError(tr('The local assistant is not set up.'))
    active = systemctl('is-active', '--quiet', UNIT).returncode == 0
    if responding():
        if active:
            return
        # Another server (the package's system service, or one started by hand) owns the
        # port; its models and settings are not this assistant's.
        raise ValueError(tr('Another Ollama server is already using {host}. Stop it, then try again.', host=HOST))
    systemctl('start', UNIT)
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if responding():
            return
        time.sleep(0.25)
    raise ValueError(tr('The local assistant service did not start. Check it with: systemctl --user status {unit}', unit=UNIT))


def ask(question, *, response_format=None, timeout=TIMEOUT):
    """One non-streaming answer from the local model; JSON-constrained when the caller needs it."""
    if not installed():
        raise ValueError(tr('The local assistant is not set up.'))
    ensure_running()
    # Qwen3 reasons aloud by default; one-shot answers skip it (faster, plain text or JSON).
    body = {'model': MODEL, 'prompt': question, 'stream': False, 'think': False}
    if response_format == 'json':
        body['format'] = 'json'
        body['options'] = {'temperature': 0}
    request = urllib.request.Request(URL + '/api/generate', data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with opener().open(request, timeout=timeout) as response:
            payload = json.loads(response.read(16 * 1024 * 1024))
    except TimeoutError:
        raise ValueError(tr('The local assistant timed out.')) from None
    except urllib.error.HTTPError as error:
        with error:
            try:
                reason = json.loads(error.read(4096)).get('error')
            except (OSError, ValueError, AttributeError):
                reason = None
        raise ValueError(tr('The local assistant could not answer: {reason}',
                            reason=reason if isinstance(reason, str) and reason else error.reason)) from None
    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise ValueError(tr('The local assistant timed out.')) from None
        raise ValueError(tr('The local assistant is unavailable.')) from None
    except (OSError, ValueError):
        raise ValueError(tr('The local assistant could not complete the request.')) from None
    answer = payload.get('response') if isinstance(payload, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError(tr('The assistant returned no answer.'))
    return answer


def environment():
    return dict(os.environ, OLLAMA_HOST=HOST)


def launch(arguments):
    """The terminal session SUPER + Alt + A opens; a prompt from the caller is answered first."""
    from eitr_terminal import wait_for_escape
    executable = binary()
    try:
        if not installed():
            raise ValueError(tr('The local assistant is not set up. Choose it in Development > Default Assistant.'))
        ensure_running()
    except ValueError as error:
        print(error, file=sys.stderr)
        # The shortcut's terminal would otherwise close before the reason can be read.
        if sys.stdin.isatty():
            try:
                wait_for_escape()
            except (EOFError, KeyboardInterrupt):
                pass
        return 1
    print(tr('Local assistant ({model}) runs only on this PC. Type /bye to close.', model=MODEL), flush=True)
    if arguments:
        subprocess.run([str(executable), 'run', MODEL, '--', ' '.join(arguments)], env=environment(), check=False)
    os.execve(str(executable), [str(executable), 'run', MODEL], environment())
    return 0


def explain():
    print(tr('Local assistant (offline, experimental)'))
    print()
    for line in (tr('It downloads Ollama (Arch package ollama, about 15 MB) and a language model ({model}, about 2.5 GB) once.', model=MODEL),
                 tr('It runs only on this PC: your requests never leave it, and no account is needed.'),
                 tr('It is noticeably less reliable than the cloud assistants, especially with unusual phrasing.'),
                 tr('You can remove it later from Development > Default Assistant.')):
        print('  • ' + line)
    print()


def setup(confirm):
    """Install, start and pull, then make it the default. CONFIRM asks the single question."""
    from eitr_assistants import set_default
    explain()
    if not confirm(tr('Set up the local assistant?')):
        print(tr('Nothing changed.'))
        return 0
    if binary() is None:
        result = subprocess.run([sys.executable, str(code('walker/scripts/actions/install/software.py')),
                                 'recipe', 'tools', 'ollama'], check=False)
        if result.returncode or binary() is None:
            print(tr('Ollama could not be installed. Your default assistant is unchanged.'), file=sys.stderr)
            return result.returncode or 1
        write_settings(record_path(), {'installed_package': True})
    models().mkdir(parents=True, exist_ok=True)
    unit_path().parent.mkdir(parents=True, exist_ok=True)
    unit_path().write_text(unit_content(binary(), models()))
    try:
        if systemctl('daemon-reload').returncode:
            raise ValueError(tr('The user service could not be loaded.'))
        ensure_running()
        print(tr('Downloading {model}…', model=MODEL), flush=True)
        if subprocess.run([str(binary()), 'pull', MODEL], env=environment(), check=False).returncode or not model_present():
            raise ValueError(tr('The model download did not finish. Run setup again to resume it.'))
        set_default(IDENTIFIER)
    except ValueError as error:
        print(error, file=sys.stderr)
        print(tr('Your default assistant is unchanged.'), file=sys.stderr)
        return 1
    print(tr('The local assistant is ready and is now your default assistant.'))
    return 0


def folder_size(folder):
    try:
        return sum(path.stat().st_size for path in folder.rglob('*') if path.is_file() and not path.is_symlink())
    except OSError:
        return 0


def remove(confirm):
    """Stop the service, delete the unit and models, reset a local default, then the package Eitr installed."""
    try:
        record = read_settings(record_path())
    except (OSError, ValueError):
        record = {}
    package = record.get('installed_package') is True and binary() is not None
    print(tr('Remove the local assistant'))
    print()
    print('  • ' + tr('Stops and deletes its background service ({unit}).', unit=UNIT))
    folder = models()
    shown = '~/' + str(folder.relative_to(Path.home())) if folder.is_relative_to(Path.home()) else str(folder)
    print('  • ' + tr('Deletes the downloaded models ({size} GB) in {folder}.',
                      size=f'{folder_size(folder) / 1e9:.1f}', folder=shown))
    if package:
        print('  • ' + tr('Uninstalls the Ollama package that setup installed (asks for your password).'))
    print()
    if not confirm(tr('Remove the local assistant?')):
        print(tr('Nothing changed.'))
        return 0
    if unit_path().exists():
        systemctl('disable', '--now', UNIT)
        unit_path().unlink()
        systemctl('daemon-reload')
    if folder.is_symlink():
        folder.unlink()
    elif folder.exists():
        shutil.rmtree(folder)
    try:
        if read_settings(config('eitr/ai.json')).get('assistant') == IDENTIFIER:
            write_settings(config('eitr/ai.json'), {'assistant': ''})
    except (OSError, ValueError):
        pass
    if package:
        result = subprocess.run([sys.executable, str(code('walker/scripts/actions/install/software.py')),
                                 'recipe-remove', 'tools', 'ollama'], check=False)
        if result.returncode:
            print(tr('The Ollama package is still installed; remove it with: sudo pacman -R ollama'), file=sys.stderr)
            return result.returncode
    record_path().unlink(missing_ok=True)
    print(tr('The local assistant was removed.'))
    return 0
