"""Follow the approved fjord wallpaper order without applying desktop settings."""
from pathlib import Path
import runpy

RENAMES = {
    'eitr': {'01-rune-seal': '03-rune-seal',
             '02-gates-of-yggdrasil': '01-aurora-fjord',
             '03-primordial-drop': '01-aurora-fjord'},
    'eitr-light': {'01-gates-of-yggdrasil': '02-gates-of-yggdrasil',
                   '02-rune-seal': '03-rune-seal',
                   '03-primordial-drop': '04-primordial-drop'},
}


def main():
    curation = Path(__file__).with_name('20261108120000-eitr-wallpaper-curation.py')
    runpy.run_path(str(curation))['main'](RENAMES)


if __name__ == '__main__':
    main()
