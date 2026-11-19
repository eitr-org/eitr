"""Bounded system package declarations and review facts shared by both frontends."""
import re
import subprocess

from eitr_i18n import tr

REPOSITORIES = {'core', 'extra', 'multilib', 'eitr'}
# Most packages one cleanup may remove (a plugin's packages and what they pulled in).
REMOVE_LIMIT = 256


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


DEPENDENCY = 'Installed as a dependency for another package'


def facts(packages):
    """`pacman -Qi` facts per installed package: install reason and who requires or optionally
    uses it. Packages that are not installed are absent."""
    packages = list(packages)
    if not packages:
        return {}
    result, current = {}, None
    for line in query('-Qi', '--', *packages).stdout.splitlines():
        key, separator, value = line.partition(':')
        if not separator:
            continue
        key, value = key.strip(), value.strip()
        if key == 'Name':
            current = result.setdefault(value, {})
        elif current is not None and key in ('Required By', 'Optional For'):
            current[key] = set() if value == 'None' else set(value.split())
        elif current is not None and key == 'Install Reason':
            current[key] = value
    return result


def closed(plan, retained=()):
    """The largest part of `plan` that can go without touching anything else: every package was
    installed as a dependency, is not retained, and only packages inside the part require or
    optionally use it. pacman -Rs ignores optional use; this keeps what another app may use."""
    plan, known = set(plan) - set(retained), facts(plan)
    changed = True
    while changed:
        changed = False
        for name in sorted(plan):
            fact = known.get(name)
            if (fact is None or fact.get('Install Reason') != DEPENDENCY
                    or (fact.get('Required By', set()) | fact.get('Optional For', set())) - plan):
                plan.discard(name)
                changed = True
    return plan


def removable(caused, retained=()):
    """What removing a plugin may clean up: the packages it installed and the dependencies they
    pulled in, as long as nothing else requires or optionally uses them (shown to the person
    in full before anything is removed)."""
    seeds = [name for name in names(list(caused), limit=4096) if name not in retained]
    plan = set(seeds)
    installed = [name for name in seeds if name in facts(seeds)]
    # Together first: a dependency reached through two of the plugin's packages is only
    # unneeded when both go, so a preview of each alone leaves it behind.
    groups = ([installed] if len(installed) > 1 else []) + [[name] for name in installed]
    for group in groups:
        preview = query('-Rsp', '--print-format', '%n', '--', *group)
        if preview.returncode == 0:
            plan.update(line.strip() for line in preview.stdout.splitlines() if line.strip())
    kept = closed(plan, retained)
    return [name for name in seeds if name in kept] + sorted(kept - set(seeds))


def root(action, packages):
    import json
    names(packages, limit=4096)
    try:
        # A cleanup goes in one call: root rechecks it as a whole, dependencies included.
        size = REMOVE_LIMIT if action == 'remove' else 32
        for offset in range(0, len(packages), size):
            subprocess.run(['/usr/bin/pkexec', '/usr/lib/eitr/eitr-system', 'plugin-packages-' + action],
                           input=json.dumps(packages[offset:offset + size]), text=True,
                           capture_output=True, check=True, timeout=240)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(tr('System package operation failed or was cancelled.')) from error
