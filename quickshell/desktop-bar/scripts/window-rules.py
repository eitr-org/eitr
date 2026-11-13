#!/usr/bin/env python3
"""Settings window rules editor CLI."""
import sys
import subprocess
import eitr_bootstrap
from eitr_window_rules import main

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
