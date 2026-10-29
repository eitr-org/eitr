#!/usr/bin/env python3
"""Shared entrypoint for the Focus preset, menus and strip."""
from pathlib import Path
import sys

for parent in Path(__file__).resolve().parents:
    for relative in ('lib', 'distro/lib'):
        library = parent / relative
        if (library / 'eitr_focus.py').is_file():
            sys.path.insert(0, str(library))
            break
    else:
        continue
    break

from eitr_focus import main

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
