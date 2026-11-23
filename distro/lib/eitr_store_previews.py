"""Batch reads and local publication for Discover theme previews."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile

from eitr_paths import cache
from eitr_plugin_install import COMMIT, normalized_url, read_state
from eitr_theme_preview import MAX_PREVIEW_BYTES

CATALOG_LIMIT = 240000


def publish_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(payload, handle)
            handle.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def discover_path(channel):
    return cache(f'eitr/catalog-previews/discover-{channel}.json')


def discover_result(channel, rows):
    result = {'items': rows}
    if len(json.dumps(result)) < CATALOG_LIMIT:
        publish_json(discover_path(channel), result)
    return result


def cached_discover(channel):
    try:
        return read_state(discover_path(channel), CATALOG_LIMIT)
    except (OSError, ValueError):
        pass
    try:
        return legacy_discover(channel)
    except (OSError, ValueError, KeyError, TypeError):
        return {'items': []}


def legacy_discover(channel):
    """Show already-published cards from releases with revision-keyed artwork."""
    from eitr_community import validate_index as validate_community
    from eitr_theme_packages import relative, validate_index

    directory = cache('eitr/catalog-previews')
    if channel == 'official':
        listing = read_state(directory / 'index.json', CATALOG_LIMIT)
        rows = [dict(row, commit=listing['commit']) for row in validate_index(listing['themes'])]
    else:
        listing = validate_community(read_state(cache('eitr/community-index.json'), 1024 * 1024))
        rows = []
        for source in listing['themes']:
            try:
                row = read_state(directory / ('community-' + source['id'] + '.json'), CATALOG_LIMIT)
                if all(row.get(field) == value for field, value in source.items()):
                    rows.append(dict(row, kind='official' if source.get('official') else 'community'))
            except (OSError, ValueError):
                continue
    items = []
    for row in rows:
        revision = row.pop('commit', '')
        path = row.get('preview')
        if path and COMMIT.fullmatch(revision):
            suffix = Path(relative(path)).suffix.lower()
            target = directory / (hashlib.sha256((revision + path).encode()).hexdigest() + suffix)
            if target.is_file():
                row['previewUrl'] = target.as_uri()
        items.append(row)
    result = {'items': items}
    return result if len(json.dumps(result)) < CATALOG_LIMIT else {'items': []}


def repository_path(backend, url):
    return backend.cache / hashlib.sha256(normalized_url(url).encode()).hexdigest()


def preview_target(blob, suffix):
    # Keep theme card assets separate from other artwork validation classes.
    return cache('eitr/catalog-previews/theme-cards') / (blob + suffix.lower())


def fetch_missing(repository, url, blobs, **options):
    from eitr_plugin_install import git
    blobs = sorted(set(blobs))
    if not blobs:
        return
    if any(not COMMIT.fullmatch(blob) for blob in blobs):
        raise ValueError('Invalid artwork object ID')
    available = git(repository, 'cat-file', '--batch-check', lazy_fetch=False,
                    input_text='\n'.join(blobs) + '\n', **options)
    missing = [blob for blob, entry in zip(blobs, available.splitlines(), strict=True)
               if entry == blob + ' missing']
    if missing:
        git(repository, 'fetch', '--no-tags', '--no-write-fetch-head', '--no-auto-maintenance',
            '--no-recurse-submodules', '--filter=blob:none', '--stdin', '--', url,
            input_text='\n'.join(missing) + '\n', timeout=20, **options)


def preview_blob(repository, blob, target, **options):
    from eitr_plugin_install import git
    from PIL import Image
    if not target.is_file():
        if int(git(repository, 'cat-file', '-s', blob, **options)) > MAX_PREVIEW_BYTES:
            raise ValueError('Artwork exceeds size limit')
        payload = git(repository, 'cat-file', 'blob', blob, binary=True, **options)
        if len(payload) > MAX_PREVIEW_BYTES:
            raise ValueError('Artwork exceeds size limit')
        with Image.open(io.BytesIO(payload)) as image:
            if image.format != 'PNG' or max(image.size) > 2048:
                raise ValueError('Invalid artwork')
            image.verify()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent) as directory:
            temporary = Path(directory) / target.name
            temporary.write_bytes(payload)
            temporary.replace(target)
    return {'image': target.as_uri(), 'size': target.stat().st_size}


def theme_previews(repository, revision, url, rows, **options):
    from eitr_plugin_install import git
    paths = {row['preview'] for row in rows if row.get('preview')}
    if not paths:
        return rows
    contents = git(repository, '--literal-pathspecs', 'ls-tree', '-rz', revision, '--',
                   *sorted(paths), lazy_fetch=False, **options)
    targets = {}
    for record in contents.split('\0'):
        if not record:
            continue
        entry, path = record.split('\t', 1)
        mode, kind, blob = entry.split()
        if mode == '100644' and kind == 'blob' and path in paths and COMMIT.fullmatch(blob):
            targets[path] = blob, preview_target(blob, Path(path).suffix)
    fetch_missing(repository, url, (blob for blob, target in targets.values() if not target.is_file()), **options)
    for row in rows:
        entry = targets.get(row.get('preview'))
        if entry:
            try:
                row['previewUrl'] = preview_blob(repository, *entry, lazy_fetch=False, **options)['image']
            except (OSError, ValueError, SyntaxError, subprocess.SubprocessError):
                continue
    return rows
