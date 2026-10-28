#!/usr/bin/env python3
"""Crop shipped wallpapers to 16:9 and Lanczos-export 3840×2160, without restoring deleted files.

Painted wallpapers ship as JPEG (quality 92, no chroma subsampling): visually the
same as PNG at about a fifth of the size. Procedural ones listed in the manifest
keep their lossless PNG, since JPEG blurs flat line art.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import tempfile

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SIZE = (3840, 2160)
MANIFEST = ROOT / 'themes/artwork-4k.json'
JPEG_QUALITY = 92


def export(path, lossless=frozenset()):
    original = path.stat()
    with Image.open(path) as image:
        relative = path.relative_to(ROOT).as_posix()
        fit = image.size != SIZE
        to_jpeg = path.suffix.lower() == '.png' and relative not in lossless
        if not fit and not to_jpeg:
            return None
        target = path.with_suffix('.jpg') if to_jpeg else path
        record = {'file': target.relative_to(ROOT).as_posix()}
        if to_jpeg:
            record['converted_from'] = relative
        if fit:
            centering = (0.85, 0.5) if path.parent.parent.name == 'eitr' else (0.5, 0.5)
            record.update({'source_size': list(image.size),
                           'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                           'centering': list(centering), 'output_size': list(SIZE)})
            output = ImageOps.fit(image, SIZE, method=Image.Resampling.LANCZOS, centering=centering)
        else:
            output = image.copy()
        descriptor, temporary = tempfile.mkstemp(prefix='.4k-', suffix=target.suffix, dir=path.parent)
        os.close(descriptor)
        try:
            if target.suffix.lower() in ('.jpg', '.jpeg'):
                output.convert('RGB').save(temporary, quality=JPEG_QUALITY, subsampling=0, optimize=True)
            else:
                output.save(temporary)
            try:
                current = path.stat()
            except FileNotFoundError:
                return None
            if (current.st_mtime_ns, current.st_size) != (original.st_mtime_ns, original.st_size):
                raise RuntimeError(f'Wallpaper changed during export; kept owner version: {relative}')
            os.chmod(temporary, original.st_mode & 0o777)
            os.replace(temporary, target)
            if target != path:
                path.unlink()
            return record
        finally:
            Path(temporary).unlink(missing_ok=True)


def main():
    previous = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    records = {record['file']: record for record in previous.get('images', [])}
    lossless = frozenset(previous.get('procedural', {}))
    paths = sorted(path for path in (ROOT / 'themes').glob('*/backgrounds/*')
                   if not path.name.startswith('.') and path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'))
    with ThreadPoolExecutor(max_workers=2) as workers:
        for record in workers.map(lambda path: export(path, lossless), paths):
            if record:
                # A converted wallpaper keeps its crop record under the new name.
                earlier = records.pop(record.pop('converted_from', record['file']), {})
                records[record['file']] = {**earlier, **record}
                print(record['file'], flush=True)
    records = {name: record for name, record in records.items() if (ROOT / name).is_file()}
    MANIFEST.write_text(json.dumps({
        'resolution': list(SIZE),
        'processing': 'Crop to fill 16:9, then Lanczos resample; painted wallpapers saved as JPEG quality 92 without chroma subsampling. Not native 4K generation. Norse subjects use right-biased framing.',
        'images': [records[name] for name in sorted(records)],
        'procedural': previous.get('procedural', {}),
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
