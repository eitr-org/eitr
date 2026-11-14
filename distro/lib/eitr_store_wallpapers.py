"""Verified wallpaper discovery details and the Store backend adapter."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from eitr_paths import cache
from eitr_wallpaper_packages import Wallpapers
from eitr_plugin_manifest import unique_object
from eitr_community import validate_index, fetch


def index_rows():
    index = validate_index(json.loads(cache('eitr/community-index.json').read_text(), object_pairs_hook=unique_object))
    return {row['id']: row for row in index.get('wallpapers', [])}


def snapshot_path(row):
    identity = json.dumps(row, sort_keys=True)
    return cache('eitr/catalog-previews/wallpapers') / hashlib.sha256(identity.encode()).hexdigest()


def detail(item_id):
    row = index_rows()[item_id]
    destination = snapshot_path(row)
    metadata = destination / 'detail.json'
    if metadata.exists():
        return json.loads(metadata.read_text())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        stage = Path(directory)
        package, spec, revision = fetch(row, 'wallpapers', stage)
        images = []
        for name in spec['images']:
            images.append(dict(path=name, imageUrl=(destination / 'package' / name).as_uri(), size=(package / name).stat().st_size))
        result = dict(row, name=spec['name'], commit=revision, wallpapers=images,
                      previewUrl=images[0]['imageUrl'], size=sum(image['size'] for image in images))
        (stage / 'detail.json').write_text(json.dumps(result))
        # Remove the sparse Git clone: only validated data is retained for Qt.
        shutil.rmtree(stage / 'repository')
        Path(directory).rename(destination)
    return result


def dispatch(name, args):
    from eitr_store_content import community
    backend = Wallpapers()
    if name == 'installed':
        return {'items': backend.installed()}
    if name == 'index':
        return community(name, args)
    if name == 'install':
        rows = index_rows()
        selected = []
        for item_id in args['ids']:
            row = rows[item_id]
            metadata = snapshot_path(row) / 'detail.json'
            # A detail review pins the exact verified revision, even if HEAD moves.
            if metadata.exists():
                row = dict(row, commit=json.loads(metadata.read_text())['commit'])
            selected.append(row)
        return {'result': backend.install(selected)}
    if name in {'remove', 'apply'}:
        return {'result': getattr(backend, name)(args['id'])}
    if name == 'detail':
        return {'item': detail(args['id'])}
    if name in {'preview', 'artwork'}:
        item = detail(args['id'])
        if name == 'preview':
            return {'image': item['previewUrl']}
        asset = next(asset for asset in item['wallpapers'] if asset['path'] == args.get('path'))
        return {'image': asset['imageUrl'], 'size': asset['size']}
    raise ValueError('Unsupported wallpaper action')
