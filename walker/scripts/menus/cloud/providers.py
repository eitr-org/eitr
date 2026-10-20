#!/usr/bin/env python3
"""Explicit vendor authentication in isolated Eitr account directories."""
import argparse
import configparser
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

for parent in Path(__file__).resolve().parents:
    library = parent / "lib"
    if not (library / "eitr_paths.py").is_file():
        library = parent / "distro/lib"
    if (library / "eitr_paths.py").is_file():
        sys.path.insert(0, str(library))
        break
from eitr_paths import code, config
from eitr_i18n import tr
from eitr_forms import Terminal

PROVIDERS = json.loads(Path(__file__).with_name("providers.json").read_text())
SCRIPT = code("walker/scripts/menus/cloud/providers.py")


def account_root(provider):
    return config("eitr/cloud-accounts") / provider


def account_path(provider, name):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", name):
        raise ValueError(tr('Use lowercase letters, digits and dashes'))
    path = account_root(provider) / name
    if any(ancestor.is_symlink() for ancestor in (path, *path.parents)):
        raise ValueError(tr('Account directories cannot be symbolic links'))
    return path


def accounts(provider):
    directory = account_root(provider)
    if any(ancestor.is_symlink() for ancestor in (directory, *directory.parents)):
        raise ValueError(tr('Account directories cannot be symbolic links'))
    if not directory.exists():
        return []
    return sorted(path.name for path in directory.iterdir()
                  if path.is_dir() and not path.is_symlink()
                  and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", path.name))


def environment(directory):
    # Do not inherit credentials, provider overrides, or shell startup files.
    allowed = ('PATH', 'LANG', 'LC_ALL', 'LC_MESSAGES', 'TERM', 'COLORTERM',
               'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS')
    values = {key: os.environ[key] for key in allowed if key in os.environ}
    values.update(HOME=str(directory), XDG_CONFIG_HOME=str(directory / '.config'),
                  XDG_DATA_HOME=str(directory / '.local/share'),
                  XDG_STATE_HOME=str(directory / '.local/state'),
                  XDG_CACHE_HOME=str(directory / '.cache'))
    return values


def terminal(provider, action, name=None):
    arguments = ['python3', str(SCRIPT), provider, action]
    if name:
        arguments.append(name)
    return shlex.join(['kitty', '--class', 'eitr-cloud', '-e', 'python3',
                       str(code('walker/scripts/actions/task-terminal.py')), *arguments])


def entries(provider):
    info = PROVIDERS[provider]
    rows = [(tr('Add {provider} Account', provider=info['name']), tr('Name it, then sign in'),
             terminal(provider, 'add'))]
    for name in accounts(provider):
        rows.append((name, info['name'] + ' / ' + selection(provider, name).get('context', name), shlex.join(['python3', str(SCRIPT), provider, 'open', name])))
    return rows


def cli_path(provider):
    executable = PROVIDERS[provider]['cli']
    found = shutil.which(executable)
    if found:
        return found
    candidates = [Path.home() / 'bin' / executable, Path.home() / '.local/bin' / executable]
    if provider in ('vercel', 'netlify'):
        candidates.extend(sorted((Path.home() / '.nvm/versions/node').glob('*/bin/' + executable),
                                 reverse=True))
    return next((str(path) for path in candidates if path.is_file() and os.access(path, os.X_OK)), None)


def ensure_cli(provider):
    if cli_path(provider):
        return True
    info = PROVIDERS[provider]
    if Terminal().confirm(tr('Install {package} now?', package=info['cli'])):
        if info['source'] == 'pacman':
            sys.path.insert(0, str(code('walker/scripts/actions/install')))
            import software
            software.install('pacman', [info['package']])
        else:
            subprocess.run(['bash', str(code('walker/scripts/actions/install/development.sh')),
                            provider], check=True)
    return bool(cli_path(provider))


def selection(provider, name):
    path = account_path(provider, name) / 'selection.json'
    if path.is_symlink():
        raise ValueError(tr('Account directories cannot be symbolic links'))
    values = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(values, dict):
        raise ValueError(tr('Unknown account'))
    for value in values.values():
        validate_value(value)
    return values


def validate_value(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.@/-]{0,127}', value):
        raise ValueError(tr('Use letters, digits, dots, dashes, slashes or @'))
    return value


def ask_value(label):
    return validate_value(Terminal().ask(label))


def scoped_arguments(provider, context):
    if provider in ('digitalocean', 'hetzner'):
        return ['--context', context]
    if provider == 'oracle':
        return ['--profile', context, '--auth', 'security_token']
    if provider == 'vercel':
        return ['--scope', context]
    return []


def run_account(provider, name, action):
    directory = account_path(provider, name)
    if not directory.is_dir():
        raise ValueError(tr('Unknown account'))
    if not ensure_cli(provider):
        return
    values = selection(provider, name)
    context = values.get('context', name)
    cli = cli_path(provider)

    def execute(arguments):
        values = environment(directory)
        values['PATH'] = str(Path(cli).parent) + os.pathsep + values.get('PATH', os.defpath)
        subprocess.run([cli, *arguments], cwd=directory, env=values, check=True)

    print(tr('Context: {context}', context=PROVIDERS[provider]['name'] + ' / ' + name + ' / ' + context))
    if action == 'login':
        if provider == 'oracle':
            region = ask_value(tr('Region'))
            execute(['session', 'authenticate', '--profile-name', context, '--region', region])
            values['region'] = region
        else:
            arguments = {
                'cloudflare': ['login'],
                'digitalocean': ['auth', 'init', '--context', context],
                'hetzner': ['context', 'create', context],
                'vercel': ['login'], 'netlify': ['login'], 'ibm': ['login', '--sso'],
            }
            execute(arguments[provider])
            if provider == 'vercel':
                values['context'] = ask_value(tr('Scope'))
    elif action == 'apikey' and provider == 'ibm':
        execute(['login', '--apikey'])
    elif action == 'list':
        if provider == 'oracle':
            profiles = configparser.ConfigParser(interpolation=None)
            profiles.read(directory / '.oci/config')
            print('\n'.join(['DEFAULT', *profiles.sections()]) if profiles.defaults() else '\n'.join(profiles.sections()))
        else:
            execute({'digitalocean': ['auth', 'list'], 'hetzner': ['context', 'list'],
                     'ibm': ['target']}[provider])
    elif action == 'switch':
        if provider == 'ibm':
            account = ask_value(tr('Account'))
            region = ask_value(tr('Region'))
            execute(['target', '-c', account, '-r', region])
            values.update(context=account, region=region)
        elif provider in ('vercel', 'netlify'):
            execute(['switch'])
            values['context'] = ask_value(tr('Scope') if provider == 'vercel' else tr('Account'))
        else:
            values['context'] = ask_value(tr('Profile') if provider == 'oracle' else tr('Context'))
    elif action == 'help':
        execute([*scoped_arguments(provider, context), '--help'])
    else:
        raise ValueError('Unsupported provider action')
    if action in ('login', 'switch', 'apikey'):
        values.setdefault('context', context)
        path = directory / 'selection.json'
        with path.open('w') as handle:
            os.chmod(path, 0o600)
            json.dump(values, handle)
    print(tr('Context: {context}', context=values.get('context', context) + ' / ' + values.get('region', '')))
    input(tr('\nPress Enter to close.'))


def open_account(provider, name):
    account_path(provider, name)
    choices = {
        tr('Open Console'): ['xdg-open', PROVIDERS[provider]['console']],
        tr('Sign In'): shlex.split(terminal(provider, 'login', name)),
        tr('CLI Help'): shlex.split(terminal(provider, 'help', name)),
    }
    if provider in ('digitalocean', 'hetzner', 'oracle', 'ibm'):
        choices[tr('List Accounts')] = shlex.split(terminal(provider, 'list', name))
    if provider != 'cloudflare':
        choices[tr('Switch Account')] = shlex.split(terminal(provider, 'switch', name))
    if provider == 'ibm':
        choices[tr('Sign In with API Key')] = shlex.split(terminal(provider, 'apikey', name))
    while True:
        active = selection(provider, name)
        context = active.get('context', name)
        detail = context + (' / ' + active['region'] if active.get('region') else '')
        result = subprocess.run([str(code('walker/bin/walker-dmenu')), '--dmenu', '--no-sort',
                                 '--prompt', PROVIDERS[provider]['name'] + ' / ' + name + ' / ' + detail],
                                input='\n'.join(sorted(choices)) + '\n', capture_output=True, text=True, check=False)
        if result.returncode or result.stdout.strip() not in choices:
            return
        subprocess.run(choices[result.stdout.strip()], check=True)
        if result.stdout.strip() == tr('Open Console'):
            return



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('provider', choices=PROVIDERS)
    parser.add_argument('action', choices=('entries', 'add', 'open', 'login', 'help', 'list', 'switch', 'apikey'))
    parser.add_argument('name', nargs='?')
    args = parser.parse_args()
    if args.action == 'entries':
        for row in entries(args.provider):
            print('\t'.join(row))
    elif args.action == 'add':
        name = Terminal().ask(tr('Name'))
        directory = account_path(args.provider, name)
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        run_account(args.provider, name, 'login')
    elif args.action == 'open':
        open_account(args.provider, args.name)
    else:
        run_account(args.provider, args.name, args.action)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
