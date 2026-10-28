#!/usr/bin/env python3
"""Rebuild batch 09 Eitr exports from checked native masters; preserve previews."""
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[4]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def checked_source(record, prefix='native'):
    source = ROOT / record[prefix + '_source']
    if hashlib.sha256(source.read_bytes()).hexdigest() != record[prefix + '_sha256']:
        raise ValueError('Native artwork changed: ' + str(source.relative_to(ROOT)))
    with Image.open(source) as image:
        if list(image.size) != record[prefix + '_size']:
            raise ValueError('Native artwork dimensions changed: ' + str(source.relative_to(ROOT)))
    return source


def main():
    batch = json.loads((ROOT / 'themes/artwork-batch-09.json').read_text())
    specification = importlib.util.spec_from_file_location(
        'ultrawide', ROOT / 'tools/export-wallpapers-ultrawide.py')
    ultrawide = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(ultrawide)
    records_path = ROOT / 'themes/artwork-4k.json'
    records = json.loads(records_path.read_text())
    exports = {record['file']: record for record in records['images']}
    wide_path = ROOT / 'themes/artwork-ultrawide.json'
    wide_records = json.loads(wide_path.read_text())
    wide_exports = {record['file']: record for record in wide_records['images']}
    for record in batch['images']:
        if record.get('status') == 'removed':
            continue
        source = checked_source(record)
        wide_source = (checked_source(record, 'ultrawide_native')
                       if 'ultrawide_native_source' in record else source)
        output = ROOT / record['file']
        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            fitted = ImageOps.fit(image.convert('RGB'), (3840, 2160),
                                  method=Image.Resampling.LANCZOS,
                                  centering=tuple(record.get('centering', [0.5, 0.5])))
            fitted.save(output, quality=92, subsampling=0, optimize=True)
        exports[record['file']] = {
            'file': record['file'], 'source': record['native_source'],
            'source_size': record['native_size'], 'source_sha256': record['native_sha256'],
            'centering': record.get('centering', [0.5, 0.5]), 'output_size': [3840, 2160]}
        wide_record = {
            'file': record['ultrawide_file'], 'wallpaper': record['file'],
            'source': {'file': wide_source.relative_to(ROOT).as_posix()},
            'framing': 'crop', 'centering': record.get('ultrawide_centering', [0.5, 0.5])}
        ultrawide.export(wide_record)
        wide_exports[wide_record['file']] = wide_record
        print(record['file'], flush=True)
    records['images'] = [exports[name] for name in sorted(exports)]
    wide_records['images'] = [wide_exports[name] for name in sorted(wide_exports)]
    write_json(records_path, records)
    write_json(wide_path, wide_records)


if __name__ == '__main__':
    main()
