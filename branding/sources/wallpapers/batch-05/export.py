#!/usr/bin/env python3
"""Rebuild batch 05 wallpaper exports and previews from the recorded native PNGs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]


def load_exporter(name):
    specification = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    batch = json.loads((ROOT / 'themes/artwork-batch-05.json').read_text())
    four_k = load_exporter('export-wallpapers-4k')
    ultrawide = load_exporter('export-wallpapers-ultrawide')
    records_path = ROOT / 'themes/artwork-4k.json'
    records = json.loads(records_path.read_text())
    exports = {record['file']: record for record in records['images']}
    wide_path = ROOT / 'themes/artwork-ultrawide.json'
    wide_records = json.loads(wide_path.read_text())
    wide_exports = {record['file']: record for record in wide_records['images']}
    for image in batch['images']:
        native = ROOT / image['native_source']
        if hashlib.sha256(native.read_bytes()).hexdigest() != image['native_sha256']:
            raise ValueError('Native source differs from the recorded artwork: ' + image['native_source'])
        temporary_source = (ROOT / image['file']).with_suffix('.png')
        shutil.copy2(native, temporary_source)
        record = four_k.export(temporary_source)
        record.pop('converted_from', None)
        if record['file'] != image['file']:
            raise ValueError('Export filename differs from the batch manifest')
        exports[image['file']] = dict(record, source=image['native_source'])
        wide_source = image.get('ultrawide_native_source', image['native_source'])
        wide_digest = image.get('ultrawide_native_sha256', image['native_sha256'])
        if hashlib.sha256((ROOT / wide_source).read_bytes()).hexdigest() != wide_digest:
            raise ValueError('Ultrawide source differs from the recorded artwork: ' + wide_source)
        wide_record = {'file': image['ultrawide_file'], 'wallpaper': image['file'],
                       'source': {'file': wide_source}, 'framing': 'crop',
                       'centering': image.get('ultrawide_centering', [0.5, 0.5])}
        ultrawide.export(wide_record)
        wide_exports[wide_record['file']] = wide_record
        print(image['file'], flush=True)
    records['images'] = [record for name, record in sorted(exports.items()) if (ROOT / name).is_file()]
    wide_records['images'] = [record for name, record in sorted(wide_exports.items()) if (ROOT / name).is_file()]
    write_json(records_path, records)
    write_json(wide_path, wide_records)
    for theme, source in batch['previews'].items():
        with Image.open(ROOT / source) as image:
            image.resize((1280, 720), Image.Resampling.LANCZOS).save(ROOT / 'themes' / theme / 'preview.png', optimize=True)


if __name__ == '__main__':
    main()
