"""Follow the curated realm wallpaper order without applying desktop settings."""
from pathlib import Path
import runpy

RENAMES = {
    'svartalfheim': {'01-cavern-city': '01-feasting-hall'},
    'asgard': {'03-cloud-fortress': '01-radiant-citadel',
               '04-storm-bridge': '03-storm-bridge'},
}


def main():
    curation = Path(__file__).with_name('20261108120000-eitr-wallpaper-curation.py')
    runpy.run_path(str(curation))['main'](RENAMES)


if __name__ == '__main__':
    main()
