"""Explicit root-helper profile operations. Never imported for validation writes."""
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile

import eitr_profile as profiles
from eitr_i18n import tr


def run(command, **options):
    return subprocess.run(command, check=True, **options)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.profile-')
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
            os.fchmod(stream.fileno(), 0o644)
            os.fchown(stream.fileno(), 0, 0)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


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
        runner(['runuser', '-u', username, '--', 'env', '-i', f'HOME={home}', f'USER={username}',
                'PATH=/usr/local/bin:/usr/bin', 'LANG=en_US.UTF-8', 'EITR_NO_SESSION=1', *command])
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
    flatpaks = additions.get('flathub', [])
    if flatpaks:
        user(['flatpak', 'remote-add', '--user', '--if-not-exists', 'flathub', 'https://dl.flathub.org/repo/flathub.flatpakrepo'])
        user(['flatpak', 'install', '--user', '-y', 'flathub', *flatpaks])
    for name in additions.get('recipes', []):
        item = catalog[name]
        if item['source'] == 'flatpak':
            for remote in [*item.get('runtime_remotes', []), {'name': item['remote'], 'url': item['url']}]:
                user(['flatpak', 'remote-add', '--user', '--if-not-exists', remote['name'], remote['url']])
            user(['flatpak', 'install', '--user', '-y', item['remote'], *item['packages']])
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
        print(profiles.summary(profile), flush=True)
        if not installer and input(tr('Type APPLY PROFILE to make these system changes: ')) != 'APPLY PROFILE':
            raise ValueError(tr('Cancelled; nothing was changed'))
        execute(profile, Path(temporary), username, channel_set, root=root, installer=installer)
