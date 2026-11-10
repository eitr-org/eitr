"""Bounded system package declarations and review facts shared by both frontends."""
import re
import subprocess

from eitr_i18n import tr

REPOSITORIES = {'core', 'extra', 'multilib', 'eitr'}


def names(value, limit=32):
    if (not isinstance(value, list) or len(value) > limit
            or any(not isinstance(name, str) or len(name) > 128
                   or not re.fullmatch(r'[a-zA-Z0-9@_+][a-zA-Z0-9@_.+\-]*', name) for name in value)
            or len(value) != len(set(value))):
        raise ValueError(tr('Invalid plugin package list'))
    return value


def query(*arguments):
    return subprocess.run(['/usr/bin/pacman', *arguments], capture_output=True, text=True,
                          env={'LC_ALL': 'C', 'PATH': '/usr/bin'}, timeout=30, check=False)


def repository(name):
    names([name])
    for repo in sorted(REPOSITORIES):
        result = query('-Si', repo + '/' + name)
        if result.returncode == 0:
            return repo
    raise ValueError(tr('Package is unavailable in official Arch or Eitr repositories: {name}', name=name))


def review(spec):
    result = []
    for name in names(spec.get('packages', [])):
        repo = repository(name)
        result.append(dict(name=name, repository=repo, installed=query('-Q', name).returncode == 0))
    return result


def review_lines(spec):
    packages = review(spec)
    if not packages:
        return []
    return [tr('System packages'), tr('Missing packages require the administrator password.')] + [
        tr('{name} · already installed', name=package['name']) if package['installed'] else
        tr('{name} · will be installed', name=package['name']) for package in packages]


def ownership():
    import json
    from eitr_paths import state
    path = state('eitr/plugin-package-installs.json')
    value = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(value, dict):
        raise ValueError(tr('Invalid plugin package list'))
    for packages in value.values():
        names(packages, limit=4096)
    return path, value


def save_ownership(path, value):
    import json
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.plugin-packages-')
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        from pathlib import Path
        Path(temporary).unlink(missing_ok=True)


def owned(plugin_id, previous=()):
    return list(dict.fromkeys([*previous, *ownership()[1].get(plugin_id, [])]))


def forget(plugin_id):
    path, value = ownership()
    if plugin_id in value:
        del value[plugin_id]
        save_ownership(path, value)


def install(spec, previous=()):
    plugin_id = spec.get('id')
    previous = owned(plugin_id, previous) if plugin_id else previous
    packages = review(spec)
    missing = [package['name'] for package in packages if not package['installed']]
    if missing:
        root('install', missing)
    caused = list(dict.fromkeys([*previous, *missing]))
    if plugin_id and caused:
        path, value = ownership()
        value[plugin_id] = names(caused, limit=4096)
        save_ownership(path, value)
    return caused


def removable(caused, retained=()):
    result = []
    for name in names(list(caused), limit=4096):
        if name in retained:
            continue
        info = query('-Qi', name)
        fields = dict(line.split(':', 1) for line in info.stdout.splitlines() if ':' in line)
        fields = {key.strip(): value.strip() for key, value in fields.items()}
        if (info.returncode == 0 and fields.get('Required By') == 'None'
                and fields.get('Optional For') == 'None'
                and fields.get('Install Reason') == 'Installed as a dependency for another package'):
            result.append(name)
    return result


def root(action, packages):
    import json
    names(packages, limit=4096)
    try:
        for offset in range(0, len(packages), 32):
            subprocess.run(['/usr/bin/pkexec', '/usr/lib/eitr/eitr-system', 'plugin-packages-' + action],
                           input=json.dumps(packages[offset:offset + 32]), text=True,
                           capture_output=True, check=True, timeout=240)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(tr('System package operation failed or was cancelled.')) from error
