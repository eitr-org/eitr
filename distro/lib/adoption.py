"""Explicit, journaled adoption of package code without discarding user edits."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import time

from eitr_paths import config, read_settings, state, write_settings
from layout import Layout
from migrations import mark_all as mark_all_migrations

# Units eitr-desktop installs in /usr/lib/systemd/user; tests keep this in sync.
PACKAGED_UNITS = ('eitr-crash-help.service', 'eitr-sunshine.service', 'elephant.service', 'nightlight-auto.service', 'nightlight-auto.timer')
SYSTEM_UNITS = Path('/usr/lib/systemd/user')

PREFERENCES = [
    'quickshell/desktop-bar/bar-settings.json',
    'quickshell/desktop-bar/workspace-style.json',
    'quickshell/desktop-bar/notification-settings.json',
    'quickshell/desktop-bar/obs-recording.json',
    'eitr/cursor.json', 'eitr/font.json', 'eitr/style.json', 'eitr/cloud-contexts.json', 'eitr/terminal.json',
]


def identity(path):
    if path.is_symlink():
        return {'digest': 'link:' + hashlib.sha256(os.readlink(path).encode()).hexdigest(), 'mode': 0o777}
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f'Not a regular legacy file: {path}')
    return {'digest': 'file:' + hashlib.sha256(path.read_bytes()).hexdigest(),
            'mode': stat.S_IMODE(path.stat().st_mode)}


def check_parents(path, boundary):
    """Never move/write through an ancestor link, including an XDG root."""
    if not path.is_relative_to(boundary):
        raise ValueError(f'Path escapes the user root: {path}')
    for parent in [path.parent, *path.parent.parents]:
        if parent.is_symlink():
            raise ValueError(f'User path has a symlinked parent: {parent}')
        if parent == boundary:
            return
    raise ValueError('Invalid adoption boundary')


def legacy_target(relative):
    if relative.startswith('HOME_FILES/'):
        return Path.home() / relative.removeprefix('HOME_FILES/'), Path.home()
    return config(relative), config()


def component(relative):
    if relative.startswith('quickshell/'):
        return '/'.join(relative.split('/')[:2])
    if relative.startswith('HOME_FILES/'):
        return 'shell' if relative == 'HOME_FILES/.zshrc' else 'home-integration'
    return relative.split('/')[0]


def plan(defaults, archive=(), keep=()):
    manifest = json.loads((defaults.share / 'legacy-layout.json').read_text()) if defaults.repo is None else json.loads((defaults.repo / 'distro/legacy-layout.json').read_text())
    rules = defaults.share / 'layout-manifest.json' if defaults.repo is None else defaults.repo / 'distro/layout-manifest.json'
    layout = Layout(defaults.repo or defaults.share, rules) if rules.is_file() else None
    archived, kept = set(archive), set(keep)
    if archived & kept:
        raise ValueError('A component cannot be both archived and overridden')
    actions, blocked = [], {}
    for relative, expected in sorted(manifest['files'].items()):
        if expected['class'] not in {'C', 'D'}:
            continue
        target, boundary = legacy_target(relative)
        check_parents(target, boundary)
        current = identity(target)
        if current is None:
            continue
        group = component(relative)
        changed = current != {key: expected[key] for key in ('digest', 'mode')}
        # Tests and docs never run, so an outdated copy is backed up without a decision.
        runtime = layout is None or classify_runtime(layout, relative)
        if changed and runtime and group not in archived | kept:
            blocked.setdefault(group, []).append(str(target))
        native_override = relative.startswith(('elephant/menus/', 'walker/config.toml', 'hypr/', 'kitty/')) or relative == 'HOME_FILES/.zshrc'
        if group in kept and not native_override:
            override_relative = relative if not relative.startswith('HOME_FILES/') else 'home/' + relative.removeprefix('HOME_FILES/')
            override = config('eitr/overrides') / override_relative
            check_parents(override, config())
            if override.exists() or override.is_symlink():
                raise ValueError(f'Override already exists: {override}')
        else:
            override = target if group in kept else None
        actions.append({'source': str(target), 'identity': current,
                        'override': str(override) if override else None})
    for group, paths in retired_references(manifest, kept).items():
        blocked.setdefault(group, []).extend(paths)
    for relative in PREFERENCES:
        target = config(relative)
        check_parents(target, config())
        if target.exists():
            read_settings(target)  # Validate every schema before the first write.
    return actions, blocked


def classify_runtime(layout, relative):
    try:
        return layout.classify(relative)['runtime']
    except ValueError:
        return True


def retired_references(manifest, kept):
    """Kept legacy code must not call into home code that adoption retires."""
    retired = {'/'.join(relative.split('/')[:2]) for relative, expected in manifest['files'].items()
               if expected['class'] in {'C', 'D'} and not relative.startswith('HOME_FILES/')
               and component(relative) not in kept and '/' in relative}
    problems = {}
    for relative, expected in sorted(manifest['files'].items()):
        if expected['class'] not in {'C', 'D'} or component(relative) not in kept:
            continue
        target = legacy_target(relative)[0]
        if not target.is_file() or target.is_symlink() or target.stat().st_size > 1_000_000:
            continue
        try:
            text = target.read_text()
        except UnicodeDecodeError:
            continue
        for prefix in sorted(retired):
            if '.config/' + prefix in text:
                problems.setdefault(component(relative), []).append(
                    f'{target} uses ~/.config/{prefix}, which adoption retires; keep {component(prefix)} too or archive this component')
    return problems


def extra_files(defaults, keep=()):
    """Files a user added inside retired code folders: kept, but reported."""
    manifest = json.loads((defaults.share / 'legacy-layout.json').read_text()) if defaults.repo is None else json.loads((defaults.repo / 'distro/legacy-layout.json').read_text())
    rules = defaults.share / 'layout-manifest.json' if defaults.repo is None else defaults.repo / 'distro/layout-manifest.json'
    layout = Layout(defaults.repo or defaults.share, rules) if rules.is_file() else None
    known = set(manifest['files'])
    folders = {str(Path(relative).parent) for relative, expected in manifest['files'].items()
               if expected['class'] in {'C', 'D'} and not relative.startswith('HOME_FILES/')
               and '/' in relative and component(relative) not in set(keep)}
    extras = []
    for folder in sorted(folders):
        directory = config(folder)
        if not directory.is_dir() or directory.is_symlink():
            continue
        for path in sorted(directory.iterdir()):
            relative = f'{folder}/{path.name}'
            if relative in known or not (path.is_file() or path.is_symlink()) or path.name == '__pycache__':
                continue
            try:
                kind = layout.classify(relative)['class'] if layout else 'C'
            except ValueError:
                kind = 'C'
            if kind in {'C', 'D'}:
                extras.append(path)
    return extras


def unit_copies():
    """Old user copies of packaged units, which would override the package's."""
    units = config('systemd/user')
    copies = [units / name for name in PACKAGED_UNITS
              if (units / name).is_file() and not (units / name).is_symlink()]
    links = [link for link in sorted(units.glob('*.wants/*'))
             if link.is_symlink() and Path(os.readlink(link)) in copies]
    return copies, links


def legacy_target_boundary(path):
    return config() if path.is_relative_to(config()) else Path.home()


def remove_empty_parents(path, boundary):
    """Retired code leaves no empty directory trees behind; undo recreates them."""
    for parent in path.parents:
        if parent == boundary or not parent.is_relative_to(boundary):
            return
        try:
            parent.rmdir()
        except OSError:
            return


def private_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as output:
        os.chmod(temporary, 0o600)
        json.dump(value, output, indent=2)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


def copy_preserving(source, destination):
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if source.is_symlink():
        destination.symlink_to(os.readlink(source))
    else:
        shutil.copy2(source, destination)


def adopt(defaults, dry_run=True, archive=(), keep=(), seed=None):
    marker = state('eitr/layout.json')
    transactions = state('eitr/layout-backups')
    for journal in transactions.glob('*/journal.json'):
        if json.loads(journal.read_text()).get('status') == 'pending':
            raise ValueError(f'Interrupted adoption; undo {journal.parent.name} before retrying')
    if marker.exists() and json.loads(marker.read_text()).get('version') == 2:
        print('Layout already adopted; no files changed.')
        return 0
    if marker.exists():
        raise ValueError('Unsupported layout state; adoption cannot replace it')
    actions, blocked = plan(defaults, archive, keep)
    for group, paths in blocked.items():
        print(f'blocked {group}: choose --archive-component or --keep-component')
        for path in paths:
            print('  ' + path)
    if blocked:
        return 1
    for action in actions:
        print(('override' if action['override'] else 'archive') + ' ' + action['source'])
    copies, links = unit_copies()
    for path in copies:
        print(f'replace {path}: an old copy of a packaged user unit; the package unit takes over')
    for path in extra_files(defaults, keep):
        print(f'kept {path}: not a shipped file, so nothing runs it after adoption')
    if dry_run:
        print(f'Would retire {len(actions)} legacy files; no changes made.')
        return 0
    # Native loaders replace their legacy file in one rename: Hyprland, kitty and
    # zsh watch or read these paths, and a missing file would break a live session.
    loaders = {str(item.target): item.source for item in defaults.files()}
    transaction = transactions / f'{time.time_ns()}'
    transaction.mkdir(mode=0o700, parents=True)
    journal = {'version': 1, 'status': 'pending', 'actions': [], 'created': []}
    journal_path = transaction / 'journal.json'
    private_json(journal_path, journal)
    try:
        for index, action in enumerate(actions):
            source = Path(action['source'])
            if identity(source) != action['identity']:
                raise ValueError(f'Legacy file changed since preflight: {source}')
            backup = transaction / 'files' / str(index)
            copy_preserving(source, backup)
            record = {**action, 'backup': str(backup), 'removed': False}
            journal['actions'].append(record)
            private_json(journal_path, journal)
            if action['override'] and action['override'] != action['source']:
                copy_preserving(source, Path(action['override']))
                journal['created'].append({'path': action['override'], 'identity': identity(Path(action['override']))})
                private_json(journal_path, journal)
            if action['override'] != action['source']:
                loader = loaders.get(str(source))
                if loader is not None and not source.is_symlink():
                    temporary = source.with_name('.' + source.name + '.eitr-adopt')
                    shutil.copy2(loader, temporary)
                    os.replace(temporary, source)
                    journal['created'].append({'path': str(source), 'identity': identity(source)})
                else:
                    source.unlink()
                    remove_empty_parents(source, legacy_target_boundary(source))
                record['removed'] = True
                private_json(journal_path, journal)
        for relative in PREFERENCES:
            target = config(relative)
            if target.exists():
                backup = transaction / 'preferences' / relative
                copy_preserving(target, backup)
                journal['actions'].append({'source': str(target), 'backup': str(backup),
                                          'removed': True, 'identity': identity(target), 'override': None})
                private_json(journal_path, journal)
                write_settings(target, {})
                journal['actions'][-1]['after'] = identity(target)
                private_json(journal_path, journal)
        for link in links:
            backup = transaction / 'units' / link.parent.name / link.name
            copy_preserving(link, backup)
            journal['actions'].append({'source': str(link), 'backup': str(backup), 'removed': True,
                                       'identity': identity(link), 'override': None})
            temporary = link.with_name('.' + link.name + '.eitr-adopt')
            temporary.symlink_to(SYSTEM_UNITS / link.name)
            os.replace(temporary, link)
            journal['created'].append({'path': str(link), 'identity': identity(link)})
            private_json(journal_path, journal)
        for unit in copies:
            backup = transaction / 'units' / unit.name
            copy_preserving(unit, backup)
            journal['actions'].append({'source': str(unit), 'backup': str(backup), 'removed': True,
                                       'identity': identity(unit), 'override': None})
            unit.unlink()
            private_json(journal_path, journal)
        if copies:
            # Reload unit definitions only; running services are not restarted.
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=False, capture_output=True)
        # Native loaders/preferences are seeded only after all retirements succeed.
        before = {str(item.target) for item in defaults.files() if item.target.exists() or item.target.is_symlink()}
        for item in defaults.files():
            if str(item.target) not in before:
                journal['created'].append({'path': str(item.target), 'identity': identity(item.source)})
        private_json(journal_path, journal)
        if seed is None:
            raise ValueError('Adoption requires the preference seed callback')
        seed_state = state('eitr/user-defaults-state.json')
        check_parents(seed_state, state())
        seed_identity = identity(seed_state)
        if seed_identity is not None:
            backup = transaction / 'seed-state.json'
            copy_preserving(seed_state, backup)
            journal['actions'].append({'source': str(seed_state), 'backup': str(backup),
                                      'identity': seed_identity, 'override': None})
        else:
            journal['created'].append({'path': str(seed_state), 'identity': None})
        private_json(journal_path, journal)
        result = seed()
        if seed_identity is not None:
            journal['actions'][-1]['after'] = identity(seed_state)
        else:
            journal['created'][-1]['identity'] = identity(seed_state)
        private_json(journal_path, journal)
        if result:
            raise ValueError('Preference seeding failed; undo the adoption transaction')
        mark_all_migrations()
        private_json(marker, {'version': 2, 'transaction': transaction.name})
        journal['status'] = 'complete'
        private_json(journal_path, journal)
        print('Adopted package code. Activate at the next session; no services restarted.')
        return 0
    except Exception:
        print(f'Adoption interrupted. Run eitr-config undo-layout {transaction.name}.')
        raise


def undo(transaction_id):
    if not transaction_id.isdigit():
        raise ValueError('Invalid adoption transaction ID')
    transaction = state('eitr/layout-backups') / transaction_id
    journal = json.loads((transaction / 'journal.json').read_text())
    if journal.get('status') == 'undone':
        print('Already undone; no changes made.')
        return 0
    # Validate the entire rollback before removing or restoring any file.
    created = {entry['path']: entry['identity'] for entry in journal['created']}
    for entry in reversed(journal['created']):
        target = Path(entry['path'])
        boundary = state() if target.is_relative_to(state()) else config() if target.is_relative_to(config()) else Path.home()
        check_parents(target, boundary)
        if identity(target) not in (None, entry['identity']):
            raise ValueError(f'New file was edited after adoption; keep it aside first: {target}')
    for action in reversed(journal['actions']):
        source, backup = Path(action['source']), Path(action['backup'])
        boundary = state() if source.is_relative_to(state()) else config() if source.is_relative_to(config()) else Path.home()
        check_parents(source, boundary)
        if not backup.is_relative_to(transaction):
            raise ValueError('Backup escapes adoption transaction')
        if not backup.exists() and not backup.is_symlink():
            raise ValueError('Missing adoption backup')
        if identity(backup) != action['identity']:
            raise ValueError('Adoption backup content changed')
        if source.exists() or source.is_symlink():
            if identity(source) not in (action['identity'], action.get('after'), created.get(str(source))):
                raise ValueError(f'Restore would overwrite an edited file: {source}')
    for entry in reversed(journal['created']):
        target = Path(entry['path'])
        if target.exists() or target.is_symlink():
            target.unlink()
    for action in reversed(journal['actions']):
        source, backup = Path(action['source']), Path(action['backup'])
        if source.exists() or source.is_symlink():
            source.unlink()
        source.parent.mkdir(parents=True, exist_ok=True)
        copy_preserving(backup, source)
    journal['status'] = 'undone'
    private_json(transaction / 'journal.json', journal)
    marker = state('eitr/layout.json')
    if marker.exists() and json.loads(marker.read_text()).get('transaction') == transaction_id:
        marker.unlink()
    print('Legacy files restored; no services restarted.')
    return 0
