#!/usr/bin/env python3
"""Build the community index and optionally verify package contents without execution."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distro/lib'))
from eitr_community import build, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--verify', action='store_true')
    arguments = parser.parse_args()
    try:
        index = build(arguments.repo)
        output = json.dumps(index, indent=2, ensure_ascii=False) + '\n'
        path = arguments.repo / 'index.json'
        if arguments.check:
            if not path.is_file() or path.read_text() != output:
                raise ValueError('Community index is stale; regenerate index.json')
        else:
            path.write_text(output)
        if arguments.verify:
            verify(index)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
