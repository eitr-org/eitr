"""Explicit root-helper profile operations. Never imported for validation writes."""
import json
import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

import eitr_profile as profiles
from eitr_i18n import tr


def run(command, **options):
    return subprocess.run(command, check=True, **options)


def write(path, value, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.profile-')
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
            os.fchmod(stream.fileno(), mode)
            os.fchown(stream.fileno(), 0, 0)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


PENDING = 'var/lib/eitr/profile-flatpaks.json'


def flatpak_work(profile, catalog):
    remotes = []
    additions = profile.get('add', {})
    if additions.get('flathub'):
        remotes.append({'name': 'flathub', 'url': 'https://dl.flathub.org/repo/flathub.flatpakrepo',
                        'apps': additions['flathub']})
    for name in additions.get('recipes', []):
        item = catalog[name]
        if item['source'] == 'flatpak':
            remotes.extend(dict(remote, apps=[]) for remote in item.get('runtime_remotes', []))
            remotes.append({'name': item['remote'], 'url': item['url'], 'apps': item['packages']})
    return remotes


def run_as_user(username, home, command, runner):
    runner(['runuser', '-u', username, '--', 'env', '-i', f'HOME={home}', f'USER={username}',
            'PATH=/usr/local/bin:/usr/bin', 'LANG=en_US.UTF-8', 'EITR_NO_SESSION=1', *command])


def install_flatpaks(remotes, user):
    for remote in remotes:
        user(['flatpak', 'remote-add', '--user', '--if-not-exists', remote['name'], remote['url']])
        if remote['apps']:
            user(['flatpak', 'install', '--user', '-y', remote['name'], *remote['apps']])


def finish_flatpaks(root=Path('/'), runner=run):
    """Consume only a private root-owned queue; failures retain it for next boot."""
    path = root / PENDING
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor) as stream:
        metadata = os.fstat(stream.fileno())
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or metadata.st_gid != 0
                or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1
                or metadata.st_size > 1048576):
            raise ValueError('Invalid pending Flatpak file ownership, mode or size')
        pending = json.load(stream, object_pairs_hook=profiles.pairs_unique)
    if not isinstance(pending, dict) or set(pending) != {'user', 'remotes'}:
        raise ValueError('Invalid pending Flatpak record')
    username = pending['user']
    if not isinstance(username, str) or not username or username.startswith('-'):
        raise ValueError('Invalid desktop user')
    account = pwd.getpwnam(username)
    if not 1000 <= account.pw_uid < 65534 or Path(account.pw_shell).name in ('nologin', 'false'):
        raise ValueError('A regular desktop user is required')
    remotes = pending['remotes']
    if not isinstance(remotes, list) or not remotes:
        raise ValueError('Invalid pending Flatpak remotes')
    for remote in remotes:
        if not isinstance(remote, dict) or set(remote) != {'name', 'url', 'apps'}:
            raise ValueError('Invalid pending Flatpak remote')
        if not isinstance(remote['name'], str) or not profiles.PACKAGE.fullmatch(remote['name']):
            raise ValueError('Invalid Flatpak remote name')
        if not isinstance(remote['url'], str) or any(character.isspace() for character in remote['url']):
            raise ValueError('Invalid Flatpak remote URL')
        url = urlsplit(remote['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('Invalid Flatpak remote URL')
        if not isinstance(remote['apps'], list) or any(
                not isinstance(app, str) or not profiles.APP_ID.fullmatch(app) for app in remote['apps']):
            raise ValueError('Invalid Flatpak application ID')
    def user(command):
        run_as_user(username, account.pw_dir, command, runner)
    try:
        install_flatpaks(remotes, user)
    except subprocess.CalledProcessError as error:
        # Usually no network yet (WiFi connects after login): the timer tries again.
        print(f'Organization profile Flatpaks not installed yet; will retry: {error}', file=sys.stderr)
        return False
    path.unlink()
    return True


def stop_plugins(username, account, code, runner, root):
    """The user's own plugin tool stops what the new policy no longer allows; files are kept."""
    runtime = f'/run/user/{account.pw_uid}'
    session = ([f'XDG_RUNTIME_DIR={runtime}', f'DBUS_SESSION_BUS_ADDRESS=unix:path={runtime}/bus']
               if (root / runtime.lstrip('/') / 'bus').exists() else [])
    try:
        runner(['runuser', '-u', username, '--', 'env', '-i', f'HOME={account.pw_dir}', f'USER={username}',
                'PATH=/usr/local/bin:/usr/bin', *session, 'python3',
                str(code / 'walker/scripts/actions/install/plugins.py'), 'enforce'])
    except subprocess.CalledProcessError as error:
        print(tr('Installed plugins could not be checked against the new policy: {error}', error=error), file=sys.stderr)


def execute(profile, drive, username, channel_set, runner=run, root=Path('/'), installer=False):
    """Called only after root-owned staging, complete validation and review."""
    account = pwd.getpwnam(username)
    if account.pw_uid < 1000:
        raise ValueError(tr('A regular desktop user is required'))
    home = Path(account.pw_dir)
    code = profiles.data_root()
    if code.name == 'distro':
        code = code.parent
    def user(command):
        run_as_user(username, home, command, runner)
    (root / 'etc/eitr').mkdir(parents=True, exist_ok=True, mode=0o755)
    excluded = sorted(profiles.removals(profile))
    installed = subprocess.run(['pacman', '-Qq'], capture_output=True, text=True, check=True).stdout.split()
    removing = sorted(set(excluded) & set(installed))
    if removing:
        runner(['pacman', '-R', '--print', '--noconfirm', '--', *removing])
    if profile.get('policies', {}).get('remote_access') is False and not installer:
        if (root / 'var/lib/eitr/remote-access/sunshine.json').exists():
            import eitr_remote
            eitr_remote.sharing(username, False)
        if (root / f'run/user/{account.pw_uid}/bus').exists():
            runner(['runuser', '-u', username, '--', 'env', f'XDG_RUNTIME_DIR=/run/user/{account.pw_uid}',
                    f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{account.pw_uid}/bus',
                    'systemctl', '--user', 'disable', '--now', 'eitr-sunshine.service'])
        if 'tailscale' in installed:
            runner(['systemctl', 'disable', '--now', 'tailscaled.service'])
    policies = profile.get('policies', {})
    write((root / 'etc/eitr/policies.json'), policies)
    write((root / 'etc/eitr/profile.json'), profile)
    if policies.get('plugins', True) is not True and not installer:
        stop_plugins(username, account, code, runner, root)
    # Pacman's dependency resolver must fail rather than silently reintroduce an excluded app.
    conf = (root / 'etc/pacman.conf')
    content = conf.read_text()
    marker = 'Include = /etc/eitr/profile-pacman.conf'
    if marker not in content:
        if '[options]' not in content:
            raise ValueError(tr('pacman.conf has no options section'))
        conf.write_text(content.replace('[options]', '[options]\n' + marker, 1))
    exclusion = (root / 'etc/eitr/profile-pacman.conf')
    exclusion.write_text('IgnorePkg = ' + ' '.join(excluded) + '\n' if excluded else '')
    exclusion.chmod(0o644)
    if removing:
        # No -Rdd, -Rc or -Rs: pacman must refuse broken dependencies.
        runner(['pacman', '-R', '--noconfirm', '--', *removing])
    defaults = profile.get('defaults', {})
    repository = defaults.get('repository')
    if repository:
        key = profiles.stick_file(drive, repository['key']['file'])
        metadata = subprocess.check_output(['gpg', '--batch', '--with-colons', '--show-keys', str(key)], text=True)
        fingerprint = next(line.split(':')[9] for line in metadata.splitlines() if line.startswith('fpr:'))
        runner(['pacman-key', '--add', str(key)])
        runner(['pacman-key', '--lsign-key', fingerprint])
        conf = root / 'etc/pacman.conf'
        content = conf.read_text()
        section = f"[{repository['name']}]"
        if section not in content:
            with conf.open('a') as stream:
                stream.write(f"\n{section}\nSigLevel = Required DatabaseOptional\nServer = {repository['server']}\n")
    additions = profile.get('add', {})
    catalog = profiles.recipes()
    packages = list(additions.get('packages', []))
    for name in additions.get('recipes', []):
        item = catalog[name]
        if item['source'] == 'pacman':
            packages.extend(item['packages'])
            packages.extend(item.get('provider_defaults', {}).values())
    if packages:
        runner(['pacman', '-Syu', '--needed', '--noconfirm', '--', *dict.fromkeys(packages)])
    if additions.get('files'):
        runner(['pacman', '-U', '--needed', '--noconfirm', '--',
                *(str(profiles.stick_file(drive, entry['file'])) for entry in additions['files'])])
    work = flatpak_work(profile, catalog)
    if installer and work:
        write(root / PENDING, {'user': username, 'remotes': work}, mode=0o600)
        runner(['systemctl', 'enable', 'eitr-profile-flatpaks.timer'])
    elif work:
        install_flatpaks(work, user)
    if 'theme' in defaults:
        user(['dbus-run-session', '--', 'bash', str(code / 'walker/scripts/actions/style/apply.sh'), defaults['theme']])
    if 'wallpaper' in defaults:
        target = (root / 'etc/eitr/profile-wallpaper')
        shutil.copyfile(profiles.stick_file(drive, defaults['wallpaper']['file']), target)
        target.chmod(0o644)
        user(['python3', str(code / 'walker/scripts/actions/wallpaper/transition.py'), 'apply', str(target)])
    if 'browser' in defaults:
        desktop = defaults['browser'] + '.desktop'
        for mime in ('text/html', 'x-scheme-handler/http', 'x-scheme-handler/https'):
            user(['xdg-mime', 'default', desktop, mime])
    channel = policies.get('update_channel', defaults.get('update_channel'))
    if channel:
        channel_set(channel)
    setup = profile.get('setup')
    if setup:
        digest = setup['sha256']
        marker = (root / 'var/lib/eitr/profile-setup') / digest
        if not marker.exists():
            marker.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            marker.write_text('started\n')
            runner(['/bin/bash', str(profiles.stick_file(drive, setup['file']))], cwd=str(drive))
            marker.write_text('completed\n')
        elif marker.read_text().strip() != 'completed':
            print(tr('The setup script {value} did not finish when it last ran; it is not run again. '
                     'Change the script to allow another attempt.', value=setup['file']), file=sys.stderr)


def apply(drive, channel_set, installer=False, username=None, root=Path('/')):
    if os.geteuid() != 0:
        raise ValueError(tr('Profile application requires eitr-system as root'))
    username = username or os.environ.get('SUDO_USER')
    if not username or pwd.getpwnam(username).pw_uid < 1000:
        raise ValueError(tr('Run profile apply as the desktop user through sudo'))
    with tempfile.TemporaryDirectory(prefix='eitr-profile-', dir=root / 'run') as temporary:
        profile = profiles.snapshot(drive, temporary)
        profiles.preflight_packages(profile, temporary)
        profiles.preflight_flatpaks(profile)
        conf = root / 'etc/pacman.conf'
        content = conf.read_text()
        if '[options]' not in content:
            raise ValueError(tr('pacman.conf has no options section'))
        repository = profile.get('defaults', {}).get('repository')
        if repository and f"[{repository['name']}]" in content:
            expected = f"[{repository['name']}]\nSigLevel = Required DatabaseOptional\nServer = {repository['server']}"
            if expected not in content:
                raise ValueError(tr('Repository name already exists with different settings'))
        print(profiles.summary(profile, installer=installer), flush=True)
        if not installer and input(tr('Type APPLY PROFILE to make these system changes: ')) != 'APPLY PROFILE':
            raise ValueError(tr('Cancelled; nothing was changed'))
        execute(profile, Path(temporary), username, channel_set, root=root, installer=installer)
