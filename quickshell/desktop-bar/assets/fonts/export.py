#!/usr/bin/env python3
"""Convert the website's Fontsource WOFF subsets to desktop TTF assets."""
import argparse
from pathlib import Path
import shutil
import tempfile

from fontTools.merge import Merger
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fontsource', type=Path, help='website/node_modules/@fontsource')
    args = parser.parse_args()
    target = Path(__file__).resolve().parent
    for family, stem, weights in [('cinzel', 'Cinzel', [500, 700]),
                                  ('cormorant-garamond', 'CormorantGaramond', [500])]:
        shutil.copyfile(args.fontsource / family / 'LICENSE', target / (stem + '-OFL.txt'))
        for weight in weights:
            with tempfile.TemporaryDirectory() as directory:
                subsets = []
                for subset in ('latin', 'latin-ext'):
                    font = TTFont(args.fontsource / family / 'files' / f'{family}-{subset}-{weight}-normal.woff')
                    font.flavor = None
                    destination = Path(directory) / (subset + '.ttf')
                    font.save(destination)
                    subsets.append(str(destination))
                font = Merger().merge(subsets)
                font.save(target / f'{stem}-{weight}.ttf')


if __name__ == '__main__':
    main()
