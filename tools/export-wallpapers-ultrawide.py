#!/usr/bin/env python3
"""Export each theme's 21:9 wallpapers to themes/<theme>/backgrounds-ultrawide/.

Ultrawide monitors show these instead of the 16:9 4K files, which were cropped
from the same originals (walker/scripts/actions/wallpaper/transition.py picks
the version per monitor). themes/artwork-ultrawide.json names each source: a file
in the checkout, cropped to fill 21:9 and Lanczos-resampled to 3440x1440 JPEG, or
"final" when the exported file itself is the master (its 21:9 original is no longer
kept), which this script leaves alone. Crops fill the canvas without stretching
the artwork or padding the sides.
"""
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'themes/artwork-ultrawide.json'
SIZE = (3440, 1440)


def source_image(source):
    return Image.open(ROOT / source['file'])


def export(record):
    output = ROOT / record['file']
    with source_image(record['source']) as image:
        centering = tuple(record.get('centering', (0.5, 0.5)))
        framing = record.get('framing', 'crop')
        if framing != 'crop':
            raise ValueError('Unknown wallpaper framing: ' + framing)
        fitted = ImageOps.fit(image.convert('RGB'), SIZE, method=Image.Resampling.LANCZOS, centering=centering)
    output.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(output, quality=90, subsampling=0, optimize=True)


def main():
    manifest = json.loads(MANIFEST.read_text())
    for record in manifest['images']:
        if 'final' in record['source']:
            continue
        export(record)
        print(record['file'], flush=True)


if __name__ == '__main__':
    main()
