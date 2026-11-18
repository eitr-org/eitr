#!/usr/bin/env python3
"""Run Eitr's cleaning mode controller from either an installed tree or a checkout."""
from pathlib import Path
import sys

for parent in Path(__file__).resolve().parents:
    for relative in ("lib", "distro/lib"):
        library = parent / relative
        if (library / "eitr_clean.py").is_file():
            sys.path.insert(0, str(library))
            break
    else:
        continue
    break

from eitr_clean import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
