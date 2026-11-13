"""Git account model, validation, existing-setup import and managed Git include text."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break
from eitr_paths import config, read_settings
from eitr_i18n import mark as menu_mark, tr


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
             'searchActions': [{'label': name, 'hint': ACTION_HINTS[name], 'icon': ACTION_ICONS[name]}
                               for name in account_actions(model, identifier)],
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


def public_key(account):
    return subprocess.run(['ssh-keygen', '-y', '-f', private_key(account['key'])], check=True,
                          capture_output=True, text=True).stdout.strip()


def keys_page(account):
    suffix = '/settings/keys' if account['provider'] == 'github' else '/-/user_settings/ssh_keys'
    return 'https://' + account['host'] + suffix
