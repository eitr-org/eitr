#!/usr/bin/env python3
"""Generate or verify a data-only theme catalog, including wallpaper thumbnails."""
import argparse
import json
import io
from PIL import Image, ImageOps
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distro/lib'))
from eitr_theme_packages import catalog


def generate(root, check=False):
    rows = catalog(root)
    expected = set()
    for row in rows:
        row['wallpapers'] = []
        for source in sorted((root / row['folder'] / 'backgrounds').iterdir()):
            if source.suffix.lower() not in {'.jpg', '.png'}:
                continue
            target = root / 'thumbnails' / row['id'] / (source.stem + '.jpg')
            if target in expected:
                raise ValueError('Wallpaper stems must be unique: ' + source.stem)
            expected.add(target)
            with Image.open(source) as original:
                image = ImageOps.exif_transpose(original).convert('RGB')
                image = image.resize((480, max(1, round(image.height * 480 / image.width))), Image.Resampling.LANCZOS)
                for quality in (80, 70, 60, 45, 30, 15):
                    output = io.BytesIO()
                    image.save(output, 'JPEG', quality=quality, optimize=True, progressive=False)
                    if output.tell() < 48 * 1024:
                        break
                else:
                    raise ValueError('Thumbnail exceeds size budget: ' + str(source))
            if check:
                if not target.is_file() or target.is_symlink() or target.read_bytes() != output.getvalue():
                    raise ValueError('Thumbnail missing or stale: ' + str(target))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(output.getvalue())
            row['wallpapers'].append(dict(path=source.relative_to(root).as_posix(),
                                          thumbnail=target.relative_to(root).as_posix(), size=source.stat().st_size))
    extra = {asset for asset in (root / 'thumbnails').rglob('*') if asset.is_file() or asset.is_symlink()} - expected
    if check and extra:
        raise ValueError('Stale thumbnails: ' + ', '.join(str(asset) for asset in sorted(extra)))
    for asset in extra:
        asset.unlink()
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--check', action='store_true')
    arguments = parser.parse_args()
    try:
        output = json.dumps(generate(arguments.repo, arguments.check), indent=2, ensure_ascii=False) + '\n'
        path = arguments.repo / 'eitr-catalog.json'
        if arguments.check:
            if not path.is_file() or path.read_text() != output:
                raise ValueError('Catalog is stale; regenerate eitr-catalog.json')
        else:
            path.write_text(output)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
