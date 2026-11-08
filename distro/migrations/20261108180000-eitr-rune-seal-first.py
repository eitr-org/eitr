"""Eitr's Rune Seal becomes the first (default) wallpaper and the Gates the second."""
from pathlib import Path
import runpy

SWAP = {'eitr': {'01-gates-of-yggdrasil': '02-gates-of-yggdrasil',
                 '02-rune-seal': '01-rune-seal'}}


def main():
    curation = Path(__file__).with_name('20261108120000-eitr-wallpaper-curation.py')
    runpy.run_path(str(curation))['main'](SWAP)


if __name__ == '__main__':
    main()
