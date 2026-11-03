#!/usr/bin/env python3
"""Generate trusted app integrations from Eitr palettes and integration metadata."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme_files import *  # noqa: F403

if __name__ == "__main__":
    sys.exit(main())
