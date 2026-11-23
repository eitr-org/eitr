"""Bounded update previews from local Git objects."""
import json
import re
import subprocess

from eitr_i18n import tr
from eitr_plugin_manifest import identifier, printable, unique_object

MAX_METADATA = 65536
VISIBLE_COMMITS = 8
STATE_LIMIT = 4 * 1024 * 1024


def local_git(repository, *args):
    from eitr_plugin_install import git
    try:
        return git(repository, *args, lazy_fetch=False, timeout=3)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(tr('Check for updates again')) from error


def object_text(repository, revision, *show_args, read=local_git):
    if int(read(repository, 'cat-file', '-s', revision)) > MAX_METADATA:
        raise ValueError(tr('Update metadata exceeds size limit'))
    return read(repository, 'show', *show_args)


def git_manifest(repository, revision, folder, filename, *, read=local_git):
    path = f'{folder}/{filename}' if folder else filename
    spec = revision + ':' + path
    mode = read(repository, 'ls-tree', revision, '--', ':(top,literal)' + path)
    if not mode.startswith(('100644 blob ', '100755 blob ')):
        raise ValueError(tr('Check for updates again'))
    payload = object_text(repository, spec, spec, read=read)
    try:
        value = json.loads(payload, object_pairs_hook=unique_object)
    except (ValueError, RecursionError) as error:
        raise ValueError(tr('Check for updates again')) from error
    if not isinstance(value, dict) or not isinstance(value.get('version'), str):
        raise ValueError(tr('Check for updates again'))
    return value


def history(repository, base, target, folder, count):
    from eitr_plugin_install import COMMIT
    if not all(isinstance(revision, str) and COMMIT.fullmatch(revision) for revision in (base, target)):
        raise ValueError(tr('Check for updates again'))
    scope = ['--', ':(top,literal)' + folder] if folder else []
    revisions = local_git(repository, 'rev-list', '--max-count=' + str(VISIBLE_COMMITS),
                          base + '..' + target, *scope).splitlines()
    if len(revisions) != min(count, VISIBLE_COMMITS):
        raise ValueError(tr('Check for updates again'))
    commits = []
    for revision in revisions:
        line = object_text(repository, revision, '-s', '--no-notes', '--format=%cs%x00%s', revision)
        date, _, subject = line.partition('\0')
        commits.append(dict(date=date, subject=printable(subject)[:240]))
    return dict(commits=commits, more=max(0, count - len(commits)))


def versions(before, after):
    return dict(before=printable(before)[:256], after=printable(after)[:256])


def permissions(before, after):
    additions = {}
    for field in ('capabilities', 'packages'):
        values = after.get(field, [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError(tr('Check for updates again'))
        additions[field] = sorted(set(values) - set(before.get(field, [])))
    hooks = after.get('hooks', {})
    if not isinstance(hooks, dict):
        raise ValueError(tr('Check for updates again'))
    if any(not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', hook) for hook in hooks):
        raise ValueError(tr('Check for updates again'))
    if any(len(values) > 64 or any(len(value) > 128 for value in values) for values in additions.values()):
        raise ValueError(tr('Update metadata exceeds size limit'))
    return dict(**additions, service='service' in after and before.get('service') != after['service'],
                hooks=sorted(hook for hook in hooks if before.get('hooks', {}).get(hook) != hooks[hook]))


def plugin_changes(backend, plugin_id):
    identifier(plugin_id)
    record = backend.records(limit=STATE_LIMIT).get(plugin_id, {})
    checked = backend.update_counts(limit=STATE_LIMIT).get(plugin_id, {})
    count = checked.get('count') if isinstance(checked, dict) else None
    if type(count) is not int or count <= 0 or checked.get('commit') != record.get('commit') or record.get('bundled'):
        raise ValueError(tr('Check for updates again'))
    root, folder = backend.root(plugin_id, record=record), record.get('path', '')
    base, target = checked['commit'], checked.get('target')
    result = history(root, base, target, folder, count)
    before, after = (git_manifest(root, revision, folder, 'eitr-plugin.json') for revision in (base, target))
    if before.get('id') != plugin_id or after.get('id') != plugin_id:
        raise ValueError(tr('Check for updates again'))
    return dict(**result, **versions(before['version'], after['version']), permissions=permissions(before, after))


def theme_changes(backend, theme_id):
    identifier(theme_id)
    snapshot = backend.checked_updates.get(theme_id)
    if not snapshot:
        raise ValueError(tr('Check for updates again'))
    repository, source, target, count, version = snapshot
    if backend.source(theme_id) != source:
        raise ValueError(tr('Check for updates again'))
    from eitr_theme_packages import manifest
    result = history(repository, source['commit'], target, source['folder'], count)
    return dict(**result, **versions(manifest(backend.folder / theme_id)['version'], version))
