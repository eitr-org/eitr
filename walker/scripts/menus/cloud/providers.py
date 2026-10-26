#!/usr/bin/env python3
"""Explicit vendor authentication in isolated Eitr account directories."""
import argparse
import configparser
import fcntl
from contextlib import contextmanager
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
from eitr_terminal import wait_for_escape
from eitr_paths import code, config
from eitr_wizard import Step, collect as collect_setup
from eitr_i18n import tr
from eitr_forms import Terminal

sys.path.insert(0, str(code("walker/scripts/actions/install")))
from software import confirm

PROVIDERS = json.loads(Path(__file__).with_name("providers.json").read_text())
SCRIPT = code("walker/scripts/menus/cloud/providers.py")


@contextmanager
def account_lock(directory, exclusive=False):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(descriptor, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError(tr('Account is in use')) from error
        yield descriptor
    finally:
        os.close(descriptor)


def delete_account(provider, name):
    directory = account_path(provider, name)
    with account_lock(directory, exclusive=True) as descriptor:
        if Path.cwd().resolve().is_relative_to(directory.resolve()):
            raise ValueError(tr('Account is in use'))
        message = tr('Delete {provider} account {account}? The provider’s sign-in for this account on this computer will be removed. The remote account itself is not affected.',
                     provider=PROVIDERS[provider]['name'], account=name)
        if not confirm(message):
            return False
        account_path(provider, name)
        if any(path.is_symlink() for path in directory.rglob('*')):
            raise ValueError(tr('Account directories cannot be symbolic links'))
        parent_descriptor = os.open(directory.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            current = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
            locked = os.fstat(descriptor)
            if (current.st_dev, current.st_ino) != (locked.st_dev, locked.st_ino):
                raise ValueError(tr('Unknown account'))
            shutil.rmtree(name, dir_fd=parent_descriptor)
        finally:
            os.close(parent_descriptor)
    return True


def report(provider, name, view):
    directory = account_path(provider, name)
    with account_lock(directory):
        cli = cli_path(provider)
        if not cli:
            raise ValueError(tr('CLI unavailable'))
        selected = selection(provider, name)
        context = selected.get('context', name)
        flags = scoped_arguments(provider, context) if provider != 'vercel' or 'context' in selected else []
        if view not in VIEWS[provider]:
            raise ValueError(tr('Unknown account'))
        arguments = list(VIEWS[provider][view][2])
        values = environment(directory)
        values['PATH'] = str(Path(cli).parent) + os.pathsep + values.get('PATH', os.defpath)

        def execute(command):
            return subprocess.run([cli, *command, *flags], cwd=directory, env=values,
                                  capture_output=True, text=True, check=False)

        output = ''
        failed = False
        if provider == 'oracle' and view != 'Compartments':
            profile = directory / '.oci/config'
            if any(parent.is_symlink() for parent in (profile, *profile.parents)):
                raise ValueError(tr('Account directories cannot be symbolic links'))
            profiles = configparser.ConfigParser(interpolation=None)
            profiles.read(profile)
            tenancy = profiles.get(context, 'tenancy')
            if not re.fullmatch(r'ocid1\.tenancy\.[a-zA-Z0-9._-]+', tenancy):
                raise ValueError(tr('Unknown account'))
            arguments += ['--compartment-id', tenancy]
            if view == 'Buckets':
                namespace = execute(['os', 'ns', 'get'])
                if namespace.returncode:
                    failed = True
                    output = namespace.stdout + namespace.stderr
                    output += '\n' + tr('Command failed (exit {status})', status=str(namespace.returncode))
                else:
                    namespace_data = json.loads(namespace.stdout)
                    if not isinstance(namespace_data, dict) or 'data' not in namespace_data:
                        raise ValueError(tr('Unknown account'))
                    namespace_value = namespace_data['data']
                    arguments += ['--namespace', validate_value(namespace_value)]
        if not failed:
            result = execute(arguments)
            output = result.stdout + result.stderr
            if result.returncode:
                output += '\n' + tr('Command failed (exit {status})', status=str(result.returncode))
        context_label = PROVIDERS[provider]['name'] + ' / ' + name + ' / ' + context
        if selected.get('region'):
            context_label += ' / ' + selected['region']
        output = VIEWS[provider][view][0] + '\n' + tr('Context: {context}', context=context_label) + '\n\n' + output
        subprocess.run(['bash', '-c', 'source "$1"; cloud_report', 'cloud-report',
                        str(code('walker/scripts/menus/cloud/terminal-helpers.sh'))],
                       input=output, text=True, check=True)


VIEWS = {
    'cloudflare': {
        'Account': (tr('Account'), tr('Account details'), ['whoami']),
        'R2 Buckets': (tr('R2 Buckets'), tr('Object storage buckets'), ['r2', 'bucket', 'list']),
        'D1 Databases': (tr('D1 Databases'), tr('SQL databases'), ['d1', 'list']),
        'KV Namespaces': (tr('KV Namespaces'), tr('Key-value namespaces'), ['kv', 'namespace', 'list']),
        'Pages Projects': (tr('Pages Projects'), tr('Website projects'), ['pages', 'project', 'list']),
        'Queues': (tr('Queues'), tr('Message queues'), ['queues', 'list']),
    },
    'digitalocean': {
        'Droplets': (tr('Droplets'), tr('Compute instances'), ['compute', 'droplet', 'list']),
        'Apps': (tr('Apps'), tr('Applications'), ['apps', 'list']),
        'Databases': (tr('Databases'), tr('Managed databases'), ['databases', 'list']),
        'Kubernetes': (tr('Kubernetes'), tr('Kubernetes clusters'), ['kubernetes', 'cluster', 'list']),
        'Volumes': (tr('Volumes'), tr('Storage volumes'), ['compute', 'volume', 'list']),
        'Domains': (tr('Domains'), tr('DNS domains'), ['compute', 'domain', 'list']),
        'Load Balancers': (tr('Load Balancers'), tr('Load balancers'), ['compute', 'load-balancer', 'list']),
        'Balance': (tr('Balance'), tr('Account balance'), ['balance', 'get']),
    },
    'hetzner': {
        'Servers': (tr('Servers'), tr('Compute instances'), ['server', 'list']),
        'Volumes': (tr('Volumes'), tr('Storage volumes'), ['volume', 'list']),
        'Networks': (tr('Networks'), tr('Virtual networks'), ['network', 'list']),
        'Firewalls': (tr('Firewalls'), tr('Network firewalls'), ['firewall', 'list']),
        'Load Balancers': (tr('Load Balancers'), tr('Load balancers'), ['load-balancer', 'list']),
        'Primary IPs': (tr('Primary IPs'), tr('Public IP addresses'), ['primary-ip', 'list']),
        'Snapshots': (tr('Snapshots'), tr('Server snapshots'), ['image', 'list', '--type', 'snapshot']),
    },
    'oracle': {
        'Compartments': (tr('Compartments'), tr('Resource compartments'), ['iam', 'compartment', 'list', '--all']),
        'Instances': (tr('Instances'), tr('Compute instances'), ['compute', 'instance', 'list', '--all']),
        'Buckets': (tr('Buckets'), tr('Object storage buckets'), ['os', 'bucket', 'list']),
        'VCNs': (tr('VCNs'), tr('Virtual networks'), ['network', 'vcn', 'list', '--all']),
    },
    'vercel': {
        'Projects': (tr('Projects'), tr('Application projects'), ['project', 'ls']),
        'Deployments': (tr('Deployments'), tr('Application deployments'), ['ls']),
        'Domains': (tr('Domains'), tr('DNS domains'), ['domains', 'ls']),
    },
    'netlify': {
        'Status': (tr('Status'), tr('Sign-in and site status'), ['status']),
        'Sites': (tr('Sites'), tr('Websites'), ['sites:list']),
    },
    'ibm': {
        'Account': (tr('Account'), tr('Account details'), ['account', 'show']),
        'Target': (tr('Target'), tr('Account and region'), ['target']),
        'Resource Groups': (tr('Resource Groups'), tr('Resource groups'), ['resource', 'groups']),
        'Service Instances': (tr('Service Instances'), tr('Provisioned services'), ['resource', 'service-instances']),
    },
}


VIEW_ICONS = {
    'Account': "\U000f0004",
    'R2 Buckets': "\U000f04df",
    'D1 Databases': "\U000f01bc",
    'KV Namespaces': "\U000f01bc",
    'Pages Projects': "\U000f024b",
    'Queues': "\U000f0279",
    'Droplets': "\U000f0379",
    'Apps': "\U000f0614",
    'Databases': "\U000f01bc",
    'Kubernetes': "\U000f0868",
    'Volumes': "\U000f02ca",
    'Domains': "\U000f0443",
    'Load Balancers': "\U000f05d1",
    'Balance': "\U000f0114",
    'Servers': "\U000f0379",
    'Networks': "\U000f059f",
    'Firewalls': "\U000f0498",
    'Primary IPs': "\U000f0a5f",
    'Snapshots': "\U000f0100",
    'Compartments': "\U000f0253",
    'Instances': "\U000f0379",
    'Buckets': "\U000f04df",
    'VCNs': "\U000f059f",
    'Projects': "\U000f024b",
    'Deployments': "\U000f14de",
    'Status': "\U000f015f",
    'Sites': "\U000f01e7",
    'Target': "\U000f04fe",
    'Resource Groups': "\U000f0253",
    'Service Instances': "\U000f0379",
}
ACCOUNT_ICON = "\U000f0004"
ADD_ICON = "\U000f0415"


def account_root(provider):
    if provider not in PROVIDERS:
        raise ValueError(tr('Unknown account'))
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
    rows = []
    for name in accounts(provider):
        rows.append((name, info['name'] + ' / ' + selection(provider, name).get('context', name), shlex.join(['python3', str(SCRIPT), provider, 'open', name]), shlex.join(['python3', str(SCRIPT), provider, 'delete', name]), ACCOUNT_ICON))
    rows.append((tr('Add {provider} Account', provider=info['name']), tr('Name it, then sign in'),
                 terminal(provider, 'add'), '', ADD_ICON))
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


def run_account(provider, name, action, answers=None):
    with account_lock(account_path(provider, name)):
        return run_account_locked(provider, name, action, answers)


def run_account_locked(provider, name, action, answers=None):
    answers = answers or {}
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
            region = answers.get('region') or ask_value(tr('Region'))
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
                values['context'] = answers.get('scope') or ask_value(tr('Scope'))
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
            target = collect_setup(tr('Context'), [Step('account', tr('Account'), validator=validate_value),
                                                  Step('region', tr('Region'), validator=validate_value)])
            account, region = target['account'], target['region']
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
    wait_for_escape()


def account_entries(provider, name):
    account_path(provider, name)
    choices = {
        tr('Open Console'): [str(code('walker/bin/app-launch')), 'xdg-open', PROVIDERS[provider]['console']],
        tr('Sign In'): shlex.split(terminal(provider, 'login', name)),
        tr('CLI Help'): shlex.split(terminal(provider, 'help', name)),
        tr('Delete Account'): ['python3', str(SCRIPT), provider, 'delete', name],
    }
    if provider in ('digitalocean', 'hetzner', 'oracle', 'ibm'):
        choices[tr('List Accounts')] = shlex.split(terminal(provider, 'list', name))
    if provider != 'cloudflare':
        choices[tr('Switch Account')] = shlex.split(terminal(provider, 'switch', name))
    if provider == 'ibm':
        choices[tr('Sign In with API Key')] = shlex.split(terminal(provider, 'apikey', name))
    presentation = {
        tr('Open Console'): ("\U000f01e7", tr('Open the web console')),
        tr('Sign In'): ("\U000f0342", tr('Sign in to this account')),
        tr('CLI Help'): ("\U000f02d6", tr('CLI commands and options')),
        tr('Delete Account'): ("\U000f01b4", tr('Remove local sign-in')),
        tr('List Accounts'): (ACCOUNT_ICON, tr('Available accounts')),
        tr('Switch Account'): ("\U000f0019", tr('Select an account')),
        tr('Sign In with API Key'): ("\U000f0306", tr('Sign in with an API key')),
    }
    for title, (label, description, arguments) in VIEWS[provider].items():
        presentation[label] = (VIEW_ICONS[title], description)
        choices[label] = shlex.split(terminal(provider, 'view', name)) + [title]
    active = selection(provider, name)
    context = ' / '.join(filter(None, [name, active.get('context'), active.get('region')]))
    rows = []
    for label in sorted(choices, key=str.casefold):
        icon, description = presentation[label]
        rows.append({'Text': label, 'Subtext': context + ' — ' + description, 'Icon': icon,
                     'Actions': {'open': shlex.join(choices[label])}})
    return rows


def open_account(provider, name):
    account_path(provider, name)
    import navigation
    navigation.select(provider, name)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('provider', choices=PROVIDERS)
    parser.add_argument('action', choices=('entries', 'add', 'open', 'login', 'help', 'list', 'switch', 'apikey', 'delete', 'view'))
    parser.add_argument('name', nargs='?')
    parser.add_argument('view', nargs='?')
    args = parser.parse_args()
    if args.action == 'entries':
        for row in entries(args.provider):
            print('\t'.join(row))
    elif args.action == 'add':
        steps = [Step('name', tr('Name'), validator=lambda value: account_path(args.provider, value))]
        if args.provider == 'oracle':
            steps.append(Step('region', tr('Region'), validator=validate_value))
        if args.provider == 'vercel':
            steps.append(Step('scope', tr('Scope'), validator=validate_value))
        answers = collect_setup(PROVIDERS[args.provider]['name'], steps)
        name = answers['name']
        directory = account_path(args.provider, name)
        if not ensure_cli(args.provider):
            return
        missing_parents = []
        parent = directory.parent
        while not parent.exists():
            missing_parents.append(parent)
            parent = parent.parent
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        try:
            run_account(args.provider, name, 'login', answers)
            if not (directory / 'selection.json').is_file():
                raise ValueError(tr('Unknown account'))
        except BaseException:
            shutil.rmtree(directory)
            for parent in missing_parents:
                parent.rmdir()
            raise
    elif args.action == 'delete':
        delete_account(args.provider, args.name)
    elif args.action == 'view':
        report(args.provider, args.name, args.view)
    elif args.action == 'open':
        open_account(args.provider, args.name)
    else:
        run_account(args.provider, args.name, args.action)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, configparser.Error, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
