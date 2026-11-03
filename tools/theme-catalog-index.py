#!/usr/bin/env python3
"""Generate or verify a data-only theme catalog, including palette swatches."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distro/lib'))
from eitr_theme_packages import catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--check', action='store_true')
    arguments = parser.parse_args()
    try:
        output = json.dumps(catalog(arguments.repo), indent=2, ensure_ascii=False) + '\n'
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
