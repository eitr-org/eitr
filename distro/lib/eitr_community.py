"""Community metadata validation and data-only sparse verification."""
import json
from pathlib import Path
import tempfile

from eitr_plugin_install import repository_url, git, COMMIT
from eitr_plugin_manifest import identifier, string, unique_object, manifest as plugin_manifest
from eitr_theme_packages import relative, validate as theme_validate, MAX_BYTES, MAX_FILES

SPDX_IDS = frozenset(json.loads(Path(__file__).with_name("spdx-license-ids.json").read_text()))


def entry(value, kind):
    required = {'id', 'repository', 'folder', 'maintainer', 'license', 'description'}
    if kind == 'plugins':
        required.add('commit')
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError('Invalid community fields')
    identifier(value['id'])
    repository_url(value['repository'])
    relative(value['folder'])
    string(value['maintainer'], 128)
    string(value['description'], 72)
    # SPDX identifiers, not license expressions or arbitrary prose.
    if not isinstance(value['license'], str) or value['license'].lower() not in SPDX_IDS:
        raise ValueError('Expected an SPDX license ID')
    if kind == 'plugins' and (not isinstance(value['commit'], str) or not COMMIT.fullmatch(value['commit'])):
        raise ValueError('Plugins require a full commit SHA')
    return value


def validate_index(value):
    if not isinstance(value, dict) or set(value) != {'schemaVersion', 'themes', 'plugins', 'removed'} or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1:
        raise ValueError('Invalid community index')
    for kind in ('themes', 'plugins'):
        rows = value[kind]
        if not isinstance(rows, list) or len(rows) > 1000:
            raise ValueError('Invalid community entries')
        ids = set()
        for row in rows:
            entry(row, kind)
            if row['id'] in ids:
                raise ValueError('Duplicate community ID')
            ids.add(row['id'])
    removed = value['removed']
    if not isinstance(removed, list) or len(removed) > 2000:
        raise ValueError('Invalid removed entries')
    removed_ids = set()
    for row in removed:
        if not isinstance(row, dict) or set(row) != {'kind', 'id', 'reason'} or row['kind'] not in ('themes', 'plugins'):
            raise ValueError('Invalid removed entry')
        identifier(row['id'])
        string(row['reason'], 256)
        identity = (row['kind'], row['id'])
        if identity in removed_ids:
            raise ValueError('Duplicate removed entry')
        removed_ids.add(identity)
        if any(item['id'] == row['id'] for item in value[row['kind']]):
            raise ValueError('Removed item is still listed')
    return value


def build(root):
    result = dict(schemaVersion=1, themes=[], plugins=[], removed=json.loads((root / 'removed.json').read_text(), object_pairs_hook=unique_object))
    for kind in ('themes', 'plugins'):
        for path in sorted((root / kind).glob('*.json')):
            if path.is_symlink() or path.stat().st_size > 65536:
                raise ValueError('Invalid entry file')
            row = entry(json.loads(path.read_text(), object_pairs_hook=unique_object), kind)
            if row['id'] != path.stem:
                raise ValueError('Entry ID must match filename')
            result[kind].append(row)
    return validate_index(result)


def fetch(row, kind, destination):
    """Materialize regular blobs only; never run repository hooks or filters."""
    repository_url(row['repository'])
    repository = destination / 'repository'
    git(None, 'clone', '--template=', '--filter=blob:none', '--sparse', '--no-checkout', '--no-recurse-submodules', '--', row['repository'], str(repository))
    revision = row.get('commit', 'HEAD')
    if kind == 'plugins':
        git(repository, 'fetch', '--filter=blob:none', '--no-recurse-submodules', '--', row['repository'], revision)
    revision = git(repository, 'rev-parse', revision + '^{commit}')
    tree = git(repository, 'ls-tree', '-rz', revision + ':' + row['folder'])
    files = [record for record in tree.split('\0') if record]
    if len(files) > MAX_FILES:
        raise ValueError('Community package exceeds file limit')
    target = destination / 'package'
    target.mkdir()
    total = 0
    for record in files:
        header, filename = record.split('\t', 1)
        mode, object_kind, blob = header.split()
        relative(filename)
        if object_kind != 'blob' or mode not in ('100644', '100755') or kind == 'themes' and mode != '100644':
            raise ValueError('Links and submodules are refused')
        total += int(git(repository, 'cat-file', '-s', blob))
        if total > MAX_BYTES:
            raise ValueError('Community package exceeds size limit')
        output = target / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(git(repository, 'cat-file', 'blob', blob, binary=True))
        output.chmod(0o755 if mode == '100755' else 0o644)
    spec = theme_validate(target)[0] if kind == 'themes' else plugin_manifest(target)
    if spec['id'] != row['id']:
        raise ValueError('Package ID differs from entry')
    return target, spec, revision


def verify(index):
    for kind in ('themes', 'plugins'):
        for row in index[kind]:
            with tempfile.TemporaryDirectory(prefix='eitr-community-') as directory:
                fetch(row, kind, Path(directory))
