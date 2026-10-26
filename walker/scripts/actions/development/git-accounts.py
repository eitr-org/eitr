#!/usr/bin/env python3
"""Explicit Git identities, folder rules and isolated GitHub/GitLab logins."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break
from eitr_terminal import wait_for_escape
from eitr_paths import code, config, state, read_settings
from eitr_i18n import mark as menu_mark, tr
from eitr_forms import Terminal
from eitr_wizard import Step, collect as collect_setup

ui = Terminal()

PROVIDERS = {'github': ('GitHub', 'github.com', 'gh', 'GH_CONFIG_DIR'),
             'gitlab': ('GitLab', 'gitlab.com', 'glab', 'GLAB_CONFIG_DIR')}
BEGIN = '# BEGIN EITR GIT ACCOUNTS\n'
END = '# END EITR GIT ACCOUNTS\n'


def root():
    return config('eitr/git-accounts')


def settings_path():
    return config('eitr/git-accounts.json')


def clean(value):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError(tr('Empty values and control characters are not allowed'))
    return value.strip()


def folder(value):
    result = Path(clean(value)).expanduser().resolve()
    if not result.is_dir() or any(c in str(result) for c in '*?[]\\'):
        raise ValueError(tr('Choose an existing folder without Git glob characters'))
    return str(result)


def safe_path(path):
    path = Path(path)
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(tr('Refusing a symlinked configuration path: {item}', item=f'{item}'))
    if path.exists() and (not path.is_file() or path.stat().st_uid != os.getuid()):
        raise ValueError(tr('Not a user-owned regular file: {path}', path=f'{path}'))


def private_key(path):
    path = Path(clean(str(path))).expanduser().absolute()
    safe_path(path)
    if not path.is_file() or path.stat().st_mode & 0o077:
        raise ValueError(tr('Choose a user-owned private key with permission 600 or stricter'))
    return str(path)


def validate(model):
    if model.get('version') != 1 or not isinstance(model.get('accounts'), dict) or not isinstance(model.get('folders'), list):
        raise ValueError(tr('Invalid Git accounts settings'))
    for identifier, account in model['accounts'].items():
        if not re.fullmatch(r'[a-f0-9]{32}', identifier) or account.get('provider') not in PROVIDERS:
            raise ValueError(tr('Invalid account or provider'))
        for key in ('label', 'name', 'email'):
            clean(account[key])
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.-]*', account['host']):
            raise ValueError(tr('Enter a hostname, not a URL, port or shell option'))
        if account.get('key'):
            if not Path(clean(account['key'])).is_absolute():
                raise ValueError(tr('SSH key references must be absolute paths'))
    if model.get('default') is not None and model['default'] not in model['accounts']:
        raise ValueError('Unknown default account')
    seen = set()
    for rule in model['folders']:
        value = rule['path']
        if not Path(value).is_absolute() or any(c in value for c in '*?[]\\\n\r'):
            raise ValueError(tr('Invalid folder rule'))
        if value in seen or rule['account'] not in model['accounts']:
            raise ValueError(tr('Duplicate folder or unknown account'))
        seen.add(value)


def load():
    model = read_settings(settings_path(), {'accounts': {}, 'folders': [], 'default': None})
    validate(model)
    return model


def selected(model, directory):
    directory = Path(directory).resolve()
    matches = [rule for rule in model['folders'] if directory.is_relative_to(Path(rule['path']))]
    return max(matches, key=lambda row: len(Path(row['path']).parts))['account'] if matches else model.get('default')


def quoted(value):
    return json.dumps(str(value), ensure_ascii=False)


def atomic(path, text, mode=0o600):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            os.fchmod(output.fileno(), mode)
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def managed_block():
    return BEGIN + '[include]\n\tpath = ' + quoted(root() / 'active.gitconfig') + '\n' + END


def global_text(original, enabled):
    if BEGIN in original or END in original:
        if original.count(BEGIN) != 1 or original.count(END) != 1:
            raise ValueError(tr('Malformed EITR include block; review ~/.gitconfig manually'))
        start, finish = original.index(BEGIN), original.index(END) + len(END)
        if finish <= start or original[start:finish] != managed_block():
            raise ValueError(tr('EITR include block was edited; review it manually'))
        return original[:start] + (managed_block() if enabled else '') + original[finish:]
    if not enabled:
        return original
    return original + ('\n' if original and not original.endswith('\n') else '') + managed_block()


def profile(account, identifier):
    text = '[user]\n\tname = ' + quoted(account['name']) + '\n\temail = ' + quoted(account['email']) + '\n'
    if account.get('key'):
        command = 'eitr-run walker/scripts/actions/development/git-accounts.py ssh ' + identifier
        # Git would otherwise probe this wrapper with -G, fail, and drop ports and protocol v2.
        text += '[core]\n\tsshCommand = ' + quoted(command) + '\n[ssh]\n\tvariant = ssh\n'
    else:
        # A folder without a configured key must not inherit the default's key.
        text += '[core]\n\tsshCommand = ssh\n'
    return text


def describe(model, identifier):
    """One line saying where Git uses this account."""
    places = [rule['path'].replace(str(Path.home()), '~') for rule in model['folders'] if rule['account'] == identifier]
    scope = ['default everywhere else' if model.get('default') == identifier else '']
    scope += ['only in ' + ', '.join(places)] if places else []
    scope = [part for part in scope if part] or ['not used yet']
    key = 'SSH key' if model['accounts'][identifier].get('key') else 'no SSH key'
    return ' · '.join([*scope, key])


def preview(model):
    print(ui.title(tr('Git will use')))
    accounts = sorted(model['accounts'].items(), key=lambda pair: pair[1]['label'].casefold())
    for identifier, account in accounts:
        print(f"  {ui.bold(account['label'])}  {account['name']} <{account['email']}>")
        print('    ' + ui.dim(describe(model, identifier)))
    if not model.get('default'):
        print('  ' + ui.dim(tr('Outside folder rules: your existing Git configuration')))
    print(ui.dim(tr('\n  Repository settings still win. Remotes, keys and CLI logins are not changed.')))


def apply(model):
    """Back up precisely the files changed, then atomically replace each one."""
    if os.geteuid() == 0 or os.environ.get('GIT_CONFIG_GLOBAL'):
        raise ValueError(tr('Run as your desktop user without GIT_CONFIG_GLOBAL'))
    lock = root() / '.lock'
    safe_path(lock)
    lock.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with lock.open('a') as output:
        os.chmod(lock, 0o600)
        fcntl.flock(output, fcntl.LOCK_EX)
        _apply(model)


def _apply(model):
    if os.geteuid() == 0 or os.environ.get('GIT_CONFIG_GLOBAL'):
        raise ValueError(tr('Run as your desktop user without GIT_CONFIG_GLOBAL'))
    validate(model)
    current = read_settings(settings_path())
    if current.get('revision') != model.get('revision'):
        raise ValueError(tr('Accounts changed in another window; reopen setup before saving'))
    global_file = Path.home() / '.gitconfig'
    active = root() / 'active.gitconfig'
    files = (global_file, active, settings_path())
    for path in files:
        safe_path(path)
    original = global_file.read_text() if global_file.exists() else ''
    enabled = bool(model.get('default') or model['folders'])
    replacement = global_text(original, enabled)
    transaction = state('eitr/git-account-backups') / str(time.time_ns())
    safe_path(transaction / 'manifest.json')
    transaction.mkdir(parents=True, mode=0o700)
    os.chmod(transaction.parent, 0o700)
    before = []
    for index, path in enumerate(files):
        data = path.read_bytes() if path.exists() else None
        mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
        before.append((path, data, mode))
        if data is not None:
            shutil.copy2(path, transaction / str(index))
            os.chmod(transaction / str(index), 0o600)
    atomic(transaction / 'manifest.json', json.dumps({'version': 1, 'files': [
        {'path': str(path), 'backup': str(index) if data is not None else None, 'mode': mode}
        for index, (path, data, mode) in enumerate(before)]}, indent=2) + '\n')
    generation = root() / 'generations' / transaction.name
    generation.mkdir(parents=True, mode=0o700)
    os.chmod(root(), 0o700)
    lines = []
    for identifier, account in model['accounts'].items():
        atomic(generation / f'{identifier}.gitconfig', profile(account, identifier))
    if model.get('default'):
        lines.append('[include]\n\tpath = ' + quoted(generation / f"{model['default']}.gitconfig") + '\n')
    for rule in sorted(model['folders'], key=lambda row: (len(Path(row['path']).parts), row['path'])):
        lines.append('[includeIf ' + quoted('gitdir:' + rule['path'].rstrip('/') + '/') + ']\n\tpath = '
                     + quoted(generation / f"{rule['account']}.gitconfig") + '\n')
    # Verify Git accepts the generated includes before changing any active file.
    candidate = generation / 'index.gitconfig'
    atomic(candidate, ''.join(lines))
    subprocess.run(['git', 'config', '--file', str(candidate), '--includes', '--list'],
                   check=True, capture_output=True, text=True)
    for path, data, _ in before:
        if (path.read_bytes() if path.exists() else None) != data:
            raise ValueError(tr('Configuration changed during preview: {path}', path=f'{path}'))
    try:
        saved = dict(model, revision=transaction.name)
        atomic(settings_path(), json.dumps(saved, ensure_ascii=False, indent=2) + '\n')
        atomic(active, '[include]\n\tpath = ' + quoted(candidate) + '\n')
        atomic(global_file, replacement, before[0][2])
    except Exception:
        for path, data, mode in before:
            if data is None:
                path.unlink(missing_ok=True)
            else:
                atomic(path, data.decode(), mode)
        raise
    model['revision'] = transaction.name
    print(ui.dim(tr('  Backup of the previous settings: {transaction}', transaction=f'{transaction}')))


def confirm(model):
    preview(model)
    if ui.ask(tr('Save these settings?'), 'Y/n').casefold() in ('', 'y', 'yes'):
        apply(model)
        print(ui.ok(tr('Saved.')))
        return True
    print(ui.dim(tr('Cancelled. Nothing was saved.')))
    return False


def cli_environment(identifier, account):
    provider = account['provider']
    environment = dict(os.environ)
    for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'GH_ENTERPRISE_TOKEN', 'GITHUB_ENTERPRISE_TOKEN',
                'GITLAB_TOKEN', 'GITLAB_ACCESS_TOKEN', 'OAUTH_TOKEN', 'CI_JOB_TOKEN',
                'GH_HOST', 'GITLAB_HOST', 'GITLAB_URI', 'GL_HOST', 'GLAB_CONFIG_DIR', 'GH_CONFIG_DIR'):
        environment.pop(key, None)
    directory = root() / 'cli' / identifier
    safe_path(directory / 'config.yml')
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    environment[PROVIDERS[provider][3]] = str(directory)
    environment['GH_HOST' if provider == 'github' else 'GITLAB_HOST'] = account['host']
    environment['GLAB_ENABLE_CI_AUTOLOGIN'] = 'false'
    return environment


def login(identifier, account):
    command = PROVIDERS[account['provider']][2]
    if not shutil.which(command):
        raise ValueError(tr('{command} is not installed; use Walker → Install → Pacman', command=f'{command}'))
    print(ui.title(tr('Log {label} in to {command}', label=f"{account['label']}", command=f'{command}')))
    print(tr('  This login belongs only to this account, not your global CLI account.'))
    print(ui.dim(tr('  The token is stored in a private, unencrypted profile file, so accounts on the')))
    print(ui.dim(tr('  same host never share a keyring entry. Never share that directory.')))
    if ui.ask(tr('Continue?'), 'y/N').casefold() not in ('y', 'yes'):
        print(ui.dim(tr('Cancelled.')))
        return
    args = [command, 'auth', 'login', '--hostname', account['host'], '--git-protocol', 'ssh', '--insecure-storage']
    if command == 'gh':
        args.append('--skip-ssh-key')
    subprocess.run(args, env=cli_environment(identifier, account), check=True)
    for path in (root() / 'cli' / identifier).rglob('*'):
        if path.is_file() and not path.is_symlink():
            os.chmod(path, 0o600)


def ssh_args(identifier, account, arguments):
    """Keep unrelated hosts unchanged; resolve existing aliases without connecting."""
    result = subprocess.run(['ssh', '-G', *arguments], check=True, capture_output=True, text=True)
    values = dict(line.split(' ', 1) for line in result.stdout.splitlines() if ' ' in line)
    if values.get('hostname') != account['host'] or not account.get('key'):
        return ['ssh', *arguments]
    if values.get('proxycommand', 'none') != 'none' or values.get('proxyjump', 'none') != 'none':
        raise ValueError(tr('This host uses an SSH proxy; retain a repository-local core.sshCommand for that advanced setup'))
    return ['ssh', '-F', '/dev/null', '-i', private_key(account['key']), '-o', 'IdentitiesOnly=yes',
            '-o', 'Hostname=' + account['host'], '-o', 'User=' + values.get('user', 'git'),
            '-o', 'Port=' + values.get('port', '22'), *arguments]


def git_values(path, pattern):
    """Raw key/value pairs from one Git config file, without following its includes."""
    result = subprocess.run(['git', 'config', '--file', str(path), '--get-regexp', pattern],
                            capture_output=True, text=True)
    return [line.split(' ', 1) for line in result.stdout.splitlines() if ' ' in line]


def ssh_route(alias):
    """Host and key an SSH alias resolves to, without connecting."""
    result = subprocess.run(['ssh', '-G', alias], capture_output=True, text=True)
    values = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition(' ')
        values.setdefault(key, value)
    key = Path(values.get('identityfile', '')).expanduser() if values.get('identityfile') else None
    usable = key and key.is_file() and not key.stat().st_mode & 0o077
    return values.get('hostname', alias), str(key) if usable else ''


def identity(path):
    values = dict(git_values(path, r'^user\.(name|email)$'))
    alias = ''
    for name, _ in git_values(path, r'^url\..*\.insteadof$'):
        base = name[len('url.'):-len('.insteadof')]
        if base.startswith('git@') and ':' in base:
            alias = base[len('git@'):].split(':', 1)[0]
    host, key = ssh_route(alias) if alias else ('github.com', '')
    return values.get('user.name'), values.get('user.email'), host, key


def existing_setup():
    """Identities configured by hand: the default and per-folder includeIf rules."""
    found = {'default': None, 'folders': [], 'skipped': []}
    # Git reads the XDG file first, so ~/.gitconfig's identity wins.
    for path in (config('git/config'), Path.home() / '.gitconfig'):
        if not path.is_file():
            continue
        name, email, host, key = identity(path)
        if name and email:
            found['default'] = {'name': name, 'email': email, 'host': host, 'key': key}
        for condition, target in git_values(path, r'^includeif\..*\.path$'):
            pattern = condition[len('includeif.'):-len('.path')]
            kind, _, location = pattern.partition(':')
            included = Path(target).expanduser()
            included = included if included.is_absolute() else path.parent / included
            if kind not in ('gitdir', 'gitdir/i') or root() in included.parents:
                continue
            directory = Path(re.sub(r'/(\*\*)?/?$', '', location)).expanduser()
            if any(c in str(directory) for c in '*?[') or not directory.is_dir() or not included.is_file():
                found['skipped'].append(pattern)
                continue
            name, email, host, key = identity(included)
            if name and email:
                found['folders'].append({'path': str(directory.resolve()), 'name': name, 'email': email,
                                         'host': host, 'key': key})
    return found


def import_setup(model, found):
    """Add accounts, the default and folder rules matching an existing manual setup."""
    def account_for(entry, label):
        provider = 'gitlab' if 'gitlab' in entry['host'] else 'github'
        for identifier, account in model['accounts'].items():
            if (account['name'], account['email'], account['host']) == (entry['name'], entry['email'], entry['host']):
                if entry['key'] and not account.get('key'):
                    account['key'] = entry['key']
                return identifier
        identifier = uuid.uuid4().hex
        model['accounts'][identifier] = {'provider': provider, 'label': label, 'name': entry['name'],
                                         'email': entry['email'], 'host': entry['host'], 'key': entry['key']}
        return identifier
    for entry in found['folders']:
        identifier = account_for(entry, Path(entry['path']).name.capitalize())
        model['folders'] = [row for row in model['folders'] if row['path'] != entry['path']]
        model['folders'].append({'path': entry['path'], 'account': identifier})
    if found['default'] and not model.get('default'):
        model['default'] = account_for(found['default'], 'Default')
    return model


def show_existing(found):
    if not found['default'] and not found['folders']:
        print(ui.title(tr('Nothing to import')))
        print(tr('  No Git identity configured outside EITR was found.'))
        return False
    print(ui.title(tr('Found in your Git configuration')))
    if found['default']:
        entry = found['default']
        print(f"  {ui.bold(tr('Default'))}  {entry['name']} <{entry['email']}>")
    for entry in found['folders']:
        key = ' · key ' + entry['key'].replace(str(Path.home()), '~') if entry['key'] else ''
        place = entry['path'].replace(str(Path.home()), '~')
        print(f"  {ui.bold(place)}  {entry['name']} <{entry['email']}>")
        print('    ' + ui.dim(tr('via {host}{key}', host=f"{entry['host']}", key=f'{key}')))
    for pattern in found['skipped']:
        print('  ' + ui.dim(tr('Skipped {pattern}: only plain existing folders can be imported.', pattern=f'{pattern}')))
    print(ui.dim(tr('\n  Your files stay unchanged; the imported rules take precedence from now on.')))
    return True


# Walker side: account rows, an action list per account, confirmations and notifications.

def walker(options, placeholder):
    """Choose with Walker's dmenu; None when dismissed."""
    result = subprocess.run([str(code('walker/bin/walker')), '--dmenu', '--placeholder', placeholder,
                             '--width', '600', '--minheight', '100'],
                            input=''.join(option + '\n' for option in options), text=True, capture_output=True)
    answer = result.stdout.strip()
    return answer if result.returncode == 0 and answer in options else None


def approved(question):
    return walker([tr('Cancel'), tr('Confirm')], question) == tr('Confirm')


def notify(title, body=''):
    subprocess.run(['notify-send', '--app-name=Git Accounts', title, body], check=False)


def in_terminal(*arguments):
    """Open a task terminal for a form that needs typing."""
    presenter = code('walker/scripts/actions/task-terminal.py')
    subprocess.Popen([str(code('walker/bin/menu-path/kitty')), '--class', 'eitr-git-accounts', '-e', 'python3', str(presenter),
                      'python3', str(Path(__file__).resolve()), *arguments], start_new_session=True)


def scope(model, identifier):
    """Short label for menu rows: Default, the folder names, or Not used yet."""
    places = [Path(rule['path']).name for rule in model['folders'] if rule['account'] == identifier]
    parts = (['Default'] if model.get('default') == identifier else []) + places
    return ' · '.join(parts) or 'Not used yet'


def rows():
    """Account rows for the Walker menu."""
    model = load()
    accounts = sorted(model['accounts'].items(), key=lambda pair: pair[1]['label'].casefold())
    return [{'id': identifier, 'label': account['label'], 'provider': account['provider'],
             'detail': scope(model, identifier), 'isDefault': model.get('default') == identifier,
             'folders': [Path(rule['path']).name for rule in model['folders'] if rule['account'] == identifier]} for identifier, account in accounts]


def project_folders():
    """Likely project folders: ~/Development and the folders directly inside it."""
    base = Path.home() / 'Development'
    found = [base] if base.is_dir() else []
    if base.is_dir():
        found += sorted((path for path in base.iterdir() if path.is_dir() and not path.name.startswith('.')),
                        key=lambda path: path.name.casefold())
    return [str(path) for path in found]


def short(path):
    return str(path).replace(str(Path.home()), '~', 1)


def save(model, message):
    apply(model)
    notify(message)


ACTION_HINTS = {
    menu_mark('Add Folder'): menu_mark('Repositories inside it use this account'),
    menu_mark('Create SSH Key'): menu_mark('New Ed25519 key with a passphrase'),
    menu_mark('Edit Name and Email'): menu_mark('Commit author shown in history'),
    menu_mark('Log In to CLI'): menu_mark('gh or glab for this account only'),
    menu_mark('Make Default'): menu_mark('Use it in folders without their own account'),
    menu_mark('Remove Account'): menu_mark('Keys stay on disk'),
    menu_mark('Remove Folder'): menu_mark('Stop using it in a folder'),
    menu_mark('Set Existing SSH Key'): menu_mark('Choose a key from ~/.ssh'),
    menu_mark('Show Public Key'): menu_mark('Print and copy it for GitHub or GitLab'),
    menu_mark('Stop Using as Default'): menu_mark('Keep it only for its folders'),
    menu_mark('Test Connection'): menu_mark('Check that the provider accepts the key'),
}
ACTION_ICONS = {'Add Folder': '󰉗', 'Create SSH Key': '󰌆', 'Edit Name and Email': '󰏫', 'Log In to CLI': '󰍂',
                'Make Default': '󰄬', 'Remove Account': '󰆴', 'Remove Folder': '󰉘', 'Set Existing SSH Key': '󰌋',
                'Show Public Key': '󰌌', 'Stop Using as Default': '󰜺', 'Test Connection': '󰖩'}
TERMINAL_ACTIONS = {'Show Public Key': 'show-key', 'Create SSH Key': 'create-key',
                    'Edit Name and Email': 'edit', 'Log In to CLI': 'login'}


def account_actions(model, identifier):
    account = model['accounts'][identifier]
    actions = ['Add Folder', 'Create SSH Key', 'Edit Name and Email', 'Log In to CLI', 'Remove Account',
               'Set Existing SSH Key']
    actions.append('Stop Using as Default' if model.get('default') == identifier else 'Make Default')
    if any(rule['account'] == identifier for rule in model['folders']):
        actions.append('Remove Folder')
    if account.get('key'):
        actions += ['Show Public Key', 'Test Connection']
    return sorted(actions, key=str.casefold)


def action_rows(identifier):
    """Submenu rows for one account; an unknown account (removed meanwhile) has none."""
    model = load()
    if identifier not in model['accounts']:
        return []
    return [{'label': name, 'hint': ACTION_HINTS[name], 'icon': ACTION_ICONS[name]}
            for name in account_actions(model, identifier)]


def perform(identifier, choice):
    model = copy.deepcopy(load())
    account = model['accounts'][identifier]
    label = account['label']
    if choice not in account_actions(model, identifier):
        raise ValueError(tr('{choice} is not available for {label}', choice=f'{choice}', label=f'{label}'))
    if choice in TERMINAL_ACTIONS:
        in_terminal(TERMINAL_ACTIONS[choice], identifier)
    elif choice == 'Make Default' and approved(tr("Use {label} in every folder without its own account?", label=label)):
        model['default'] = identifier
        save(model, tr("{label} is now the default account", label=label))
    elif choice == 'Stop Using as Default' and approved(tr("Stop using {label} outside its folders?", label=label)):
        model['default'] = None
        save(model, tr("{label} is no longer the default account", label=label))
    elif choice == 'Add Folder':
        options = [short(path) for path in project_folders()] + [tr('Other folder…')]
        picked = walker(options, tr("Folder whose repositories use {label}", label=label))
        if picked == tr('Other folder…'):
            in_terminal('add-folder', identifier)
        elif picked and approved(tr("Use {label} for repositories in {picked}?", label=label, picked=picked)):
            path = folder(picked)
            model['folders'] = [row for row in model['folders'] if row['path'] != path]
            model['folders'].append({'path': path, 'account': identifier})
            save(model, tr("{label} now applies to {picked}", label=label, picked=picked))
    elif choice == 'Remove Folder':
        options = [short(rule['path']) for rule in model['folders'] if rule['account'] == identifier]
        picked = walker(options, tr("Folder to stop using {label} in", label=label))
        if picked and approved(tr("Stop using {label} in {picked}?", label=label, picked=picked)):
            path = str(Path(picked).expanduser())
            model['folders'] = [row for row in model['folders'] if row['path'] != path]
            save(model, tr("{label} no longer applies to {picked}", label=label, picked=picked))
    elif choice == 'Set Existing SSH Key':
        directory = Path.home() / '.ssh'
        keys = sorted(short(path.with_suffix('')) for path in directory.glob('*.pub') if path.with_suffix('').is_file())
        picked = walker(keys, tr("Private key for {label}", label=label))
        if picked and approved(tr("Use {picked} for {label}?", picked=picked, label=label)):
            account['key'] = private_key(Path(picked).expanduser())
            save(model, tr("{label} now uses {picked}", label=label, picked=picked))
    elif choice == 'Test Connection':
        result = subprocess.run(ssh_args(identifier, account, ['-T', '-o', 'BatchMode=yes', 'git@' + account['host']]),
                                capture_output=True, text=True, timeout=30)
        answer = (result.stderr + result.stdout).strip().splitlines()
        greeting = next((line for line in answer if line.startswith(('Hi ', 'Welcome'))), '')
        notify(f'{label}: connected' if greeting else f'{label}: connection failed',
               greeting or (answer[-1] if answer else f'ssh exited {result.returncode}'))
    elif choice == 'Remove Account' and approved(tr("Remove {label} and its folder rules? Keys stay on disk.", label=label)):
        del model['accounts'][identifier]
        model['folders'] = [row for row in model['folders'] if row['account'] != identifier]
        if model.get('default') == identifier:
            model['default'] = None
        save(model, tr("{label} was removed", label=label))


# Terminal side: the forms that need typing.

def public_key(account):
    return subprocess.run(['ssh-keygen', '-y', '-f', private_key(account['key'])], check=True,
                          capture_output=True, text=True).stdout.strip()


def keys_page(account):
    suffix = '/settings/keys' if account['provider'] == 'github' else '/-/user_settings/ssh_keys'
    return 'https://' + account['host'] + suffix


def show_key(identifier):
    account = load()['accounts'][identifier]
    key = public_key(account)
    print(ui.title(tr('{label} public key', label=f"{account['label']}")))
    print(f'\n{key}\n')
    copied = subprocess.run(['wl-copy'], input=key, text=True, check=False).returncode == 0 if shutil.which('wl-copy') else False
    print(ui.ok(tr('Copied to the clipboard.')) if copied else ui.dim(tr('Select the line above to copy it.')))
    print(tr('  Add it at {bold}, signed in as the {label} account.', bold=f'{ui.bold(keys_page(account))}', label=f"{account['label']}"))
    print(ui.dim(tr('  This is the public half; never share the private key file.')))


def add_form(model):
    answers = collect_setup(tr('Add a Git account'), [
        Step('provider', tr('Provider'), options=[('GitHub', 'github'), ('GitLab', 'gitlab')]),
        Step('label', tr('Account name'), validator=clean),
        Step('name', tr('Author name'), question=tr('Commit author name'), validator=clean),
        Step('email', tr('Author email'), question=tr('Commit author email'), validator=clean),
        Step('host', tr('Hostname'), default=lambda values: PROVIDERS[values.get('provider', 'github')][1],
             validator=lambda value: bool(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.-]*', value))),
        Step('key', tr('SSH key'), question=tr('Private SSH key'), optional=True, validator=private_key),
        Step('default', tr('Default account'), question=tr('Use it in every folder without its own account?'), default=not model.get('default'),
             options=[(tr('Yes'), True), (tr('No'), False)]),
        Step('folder', tr('Folder'), question=tr('Folder whose repositories use only this account'), optional=True, validator=folder),
    ])
    identifier = uuid.uuid4().hex
    model['accounts'][identifier] = {key: answers[key] for key in ('provider', 'label', 'name', 'email', 'host', 'key')}
    if answers['key']:
        model['accounts'][identifier]['key'] = private_key(answers['key'])
    if answers['default']:
        model['default'] = identifier
    if answers['folder']:
        path = folder(answers['folder'])
        model['folders'] = [row for row in model['folders'] if row['path'] != path] + [{'path': path, 'account': identifier}]
    apply(model)
    return True


def edit_form(model, identifier):
    account = model['accounts'][identifier]
    answers = collect_setup(tr('Edit {label}', label=account['label']), [
        Step(key, tr(short), question=tr(label), default=account[key], validator=clean)
        for key, short, label in (('label', 'Account name', 'Account name'), ('name', 'Author name', 'Commit author name'), ('email', 'Author email', 'Commit author email'))
    ])
    account.update(answers)
    apply(model)


def create_key(model, identifier):
    account = model['accounts'][identifier]
    destination = Path.home() / '.ssh' / ('eitr-' + identifier)
    if destination.exists() or destination.is_symlink():
        raise ValueError(tr('{key_path} already exists; use Set Existing SSH Key', key_path=f'{short(destination)}'))
    destination.parent.mkdir(mode=0o700, exist_ok=True)
    print(ui.title(tr('New SSH key for {label}', label=f"{account['label']}")))
    print(ui.dim(tr('  Choose a passphrase. The key is never copied into backups.\n')))
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-f', str(destination), '-C', 'EITR ' + account['label']],
                   check=True)
    account['key'] = private_key(destination)
    apply(model)
    print(ui.ok(tr('{label} now uses {key_path}.', label=f"{account['label']}", key_path=f'{short(destination)}')))
    show_key(identifier)


def folder_form(model, identifier):
    account = model['accounts'][identifier]
    print(ui.title(tr('Folder for {label}', label=f"{account['label']}")))
    path = folder(ui.ask(tr('Folder path'), hint=tr('Repositories inside it use only this account')))
    model['folders'] = [row for row in model['folders'] if row['path'] != path] + [{'path': path, 'account': identifier}]
    confirm(model)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['rows', 'actions', 'do', 'add', 'import', 'show-key', 'create-key',
                                           'edit', 'login', 'add-folder', 'cli', 'ssh'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise ValueError(tr('Run as your desktop user, not root'))
    if args.action == 'ssh':
        identifier, *arguments = args.arguments
        return subprocess.call(ssh_args(identifier, load()['accounts'][identifier], arguments))
    if args.action == 'cli':
        model = load()
        identifier = selected(model, Path.cwd())
        if not identifier:
            raise ValueError(tr('No default or folder account selected'))
        account = model['accounts'][identifier]
        return subprocess.call([PROVIDERS[account['provider']][2], *args.arguments], env=cli_environment(identifier, account))
    if args.action == 'rows':
        print(json.dumps(rows()))
        return 0
    if args.action == 'actions':
        print(json.dumps(action_rows(args.arguments[0]) if args.arguments else []))
        return 0
    if args.action == 'do':
        identifier, choice = args.arguments
        try:
            perform(identifier, choice)
        except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
            # Walker actions have no terminal, so report failures as notifications.
            notify(tr('Git Accounts'), str(error))
            return 1
        return 0
    model = copy.deepcopy(load())
    identifier = args.arguments[0] if args.arguments else None
    if identifier is not None and identifier not in model['accounts']:
        raise ValueError('Unknown account')
    if args.action == 'add':
        add_form(model)
    elif args.action == 'import':
        found = existing_setup()
        if show_existing(found):
            confirm(import_setup(model, found))
    elif args.action == 'show-key':
        show_key(identifier)
    elif args.action == 'create-key':
        create_key(model, identifier)
    elif args.action == 'edit':
        edit_form(model, identifier)
    elif args.action == 'login':
        login(identifier, model['accounts'][identifier])
    elif args.action == 'add-folder':
        folder_form(model, identifier)
    # Task terminals close after success; keep the outcome readable first.
    wait_for_escape()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f'\n\033[1;31m✗\033[0m {error}', file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print(tr('\nCancelled.'))
        sys.exit(0)
