"""Machine-local assistant accounts; Default leaves the CLI environment untouched."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from eitr_i18n import tr, mark
from eitr_paths import code, config, data, read_settings, write_settings

# Checked against CLI help and vendor docs: Claude config directory reference,
# Codex environment variables, Gemini bundled configuration.md, Grok settings,
# and `copilot help environment`. agy --help/reference exposes no config override.
CONFIGURATION = {
    'claude': ('CLAUDE_CONFIG_DIR', '.claude', []),
    'codex': ('CODEX_HOME', '.codex', ['login']),
    'gemini': ('GEMINI_CLI_HOME', '.gemini', []),
    'grok': ('GROK_HOME', '.grok', []),
    'copilot': ('COPILOT_HOME', '.copilot', ['login']),
    'agy': (None, '.gemini/antigravity-cli', []),
    # OPENCODE_CONFIG_DIR does not isolate the shared auth.json.
    'opencode': (None, '.config/opencode', []),
    'pi': ('PI_CODING_AGENT_DIR', '.pi/agent', []),
}
DEFAULT = 'default'


def load(identifier):
    if identifier not in CONFIGURATION:
        raise ValueError('Unsupported assistant')
    value = read_settings(config('eitr/ai-accounts.json')).get(identifier, {})
    if not isinstance(value, dict):
        raise ValueError('Invalid account settings')
    accounts = value.get('accounts', {})
    if not isinstance(accounts, dict) or any(not re.fullmatch(r'[0-9a-f]{32}', key)
            or not valid_label(label) for key, label in accounts.items()):
        raise ValueError('Invalid account settings')
    return value


def valid_label(label):
    return isinstance(label, str) and 0 < len(label.strip()) <= 80 and not any(ord(character) < 32 or ord(character) == 127 for character in label)


def rows(identifier):
    value = load(identifier)
    selected = value.get('selected', DEFAULT)
    accounts = value.get('accounts', {}) if CONFIGURATION[identifier][0] else {}
    if selected not in accounts:
        selected = DEFAULT
    return [{'id': DEFAULT, 'label': tr('Default'), 'current': selected == DEFAULT},
            *[{'id': key, 'label': label, 'current': selected == key}
              for key, label in sorted(accounts.items(), key=lambda account: account[1].casefold())]]


def folder(identifier, account):
    if identifier not in CONFIGURATION or not re.fullmatch(r'[0-9a-f]{32}', account):
        raise ValueError('Invalid account')
    return data('eitr/ai-accounts') / identifier / account


def environment(identifier, base=None, account=None):
    result = dict(os.environ if base is None else base)
    variable = CONFIGURATION.get(identifier, (None,))[0]
    if variable:
        if account is None:
            account = next(row['id'] for row in rows(identifier) if row['current'])
        if account != DEFAULT:
            if account not in load(identifier).get('accounts', {}):
                raise ValueError('Unknown account')
            result[variable] = str(folder(identifier, account))
            if identifier == 'grok':
                result.pop('GROK_AUTH_PATH', None)
    return result


def config_folder(identifier, account=None):
    variable, relative, _ = CONFIGURATION[identifier]
    env = environment(identifier, account=account)
    root = Path(env[variable]) if variable and env.get(variable) else Path.home() / relative
    # Gemini's override is a home containing .gemini, unlike the other CLIs.
    return root / '.gemini' if identifier == 'gemini' and env.get(variable) else root


def save(identifier, value):
    path = config('eitr/ai-accounts.json')
    write_settings(path, {identifier: value})
    path.chmod(0o600)


def switch(identifier, account):
    if account not in {row['id'] for row in rows(identifier)}:
        raise ValueError('Unknown account')
    value = load(identifier)
    value['selected'] = account
    save(identifier, value)


def add(identifier, label):
    from eitr_assistants import executable
    variable, _, login = CONFIGURATION[identifier]
    if not variable or not valid_label(label):
        raise ValueError('Unsupported account or invalid name')
    binary = executable(identifier)
    if binary is None:
        raise ValueError(tr('Choose an installed assistant.'))
    account = uuid.uuid4().hex
    path = folder(identifier, account)
    for directory in (path.parent.parent, path.parent, path):
        if directory.is_symlink():
            raise ValueError('Unsafe account folder')
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory.chmod(0o700)
    value = load(identifier)
    value.setdefault('accounts', {})[account] = label.strip()
    save(identifier, value)
    env = environment(identifier, account=account)
    env['PATH'] = str(binary.parent) + os.pathsep + env.get('PATH', '')
    env['BROWSER'] = str(code('walker/scripts/actions/ai-private-browser.py'))
    # A cancelled login retains the account so the user can retry by opening it.
    result = subprocess.run([str(binary), *login], env=env, check=False)
    return result.returncode


def delete(identifier, account):
    value = load(identifier)
    if account == DEFAULT or account not in value.get('accounts', {}):
        raise ValueError('Cannot remove this account')
    path = folder(identifier, account)
    if path.is_symlink() or path.parent.is_symlink() or path.parent.parent.is_symlink():
        raise ValueError('Unsafe account folder')
    if path.exists():
        shutil.rmtree(path)
    del value['accounts'][account]
    if value.get('selected') == account:
        value['selected'] = DEFAULT
    save(identifier, value)


def menu(identifier):
    return {'accounts': rows(identifier), 'supported': bool(CONFIGURATION[identifier][0])}


def main(arguments):
    action, identifier, *rest = arguments
    if action == 'list':
        print(json.dumps(menu(identifier)))
    elif action == 'switch':
        switch(identifier, rest[0])
    elif action == 'add':
        from eitr_wizard import Step, collect
        values = collect(tr('Add Account…'), [Step('name', mark('Account name'), validator=valid_label,
                         description=mark('Choose a label for this account.'))])
        return add(identifier, values['name'])
    elif action == 'delete':
        from eitr_terminal import read_key
        if not sys.stdin.isatty():
            return 1
        print(tr('Remove this account and its local configuration?'))
        print(tr('Press Enter to confirm; Esc to cancel.'))
        if read_key() not in ('\r', '\n'):
            return 1
        delete(identifier, rest[0])
    else:
        return 2
    return 0
