#!/usr/bin/env python3
"""Machine-local state for the first-login Welcome panel.

The panel opens automatically only for users whose desktop was set up by the
Eitr installer (which records ``installed-paths`` in the same state directory),
or who asked to see it again at the next login. Existing desktops restored from
this repository never have that record, so they are not interrupted.
"""
import eitr_bootstrap
from eitr_i18n import tr

import json
import os
from pathlib import Path
import sys


def state_dir():
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(base) / "eitr"


def paths():
    directory = state_dir()
    return {
        "installed": directory / "installed-paths",
        "dismissed": directory / "welcome-dismissed",
        "pending": directory / "welcome-pending",
    }


def status():
    files = paths()
    dismissed = files["dismissed"].exists()
    pending = files["pending"].exists()
    eligible = pending or files["installed"].exists()
    return {"show": eligible and not dismissed, "dismissed": dismissed, "pending": pending}


def mark(name):
    """Record ``dismissed`` or ``pending``; the two choices replace each other."""
    files = paths()
    other = "pending" if name == "dismissed" else "dismissed"
    files[name].parent.mkdir(parents=True, exist_ok=True)
    files[name].touch()
    files[other].unlink(missing_ok=True)
    return status()


COMMANDS = {
    "status": status,
    "dismiss": lambda: mark("dismissed"),
    "remind": lambda: mark("pending"),
}


def main(argv):
    if len(argv) != 1 or argv[0] not in COMMANDS:
        print('usage: welcome-state.py status|dismiss|remind', file=sys.stderr)
        return 2
    try:
        result = COMMANDS[argv[0]]()
    except OSError as error:
        print('welcome-state.py: {error}'.format(error=f'{error}'), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
