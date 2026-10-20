#!/usr/bin/env python3
"""Walker's Factory Reset: two separate warnings, then a typed confirmation.
The root-owned helper validates everything again before changing anything."""
import eitr_bootstrap
from eitr_i18n import mark, tr
import shutil
import socket
import subprocess
import sys
import textwrap

HELPER = "/usr/lib/eitr/eitr-factory-reset"
CONFIRMATION = "RESET MY COMPUTER"

FIRST_WARNINGS = {
    "everything": [
        mark('ERASE EVERYTHING returns this computer to how it was at its first login.'),
        mark('Deleted: every app installed since, every changed setting, accounts added later and ALL files in the home folders (documents, downloads, pictures, projects).'),
        mark("Kept: the disk encryption passphrase and each remaining account's password."),
    ],
    "keep-files": [
        mark('KEEP MY FILES returns the system, apps and settings to how they were at the first login, and keeps the files in your home folder.'),
        mark('Removed: apps installed since, system settings and accounts added later (their home folders stay).'),
        mark('Your current personal settings, the hidden files such as ~/.config and ~/.ssh, move into the folder "Settings before reset <date>" in your home folder, so nothing in it is deleted.'),
        mark("Kept: the disk encryption passphrase and each remaining account's password."),
    ],
}

SECOND_WARNING = [
    mark('Second warning: this resets the computer named "{host}".'),
    mark('Save your work and close your apps now. The computer restarts as soon as the reset is ready; anything changed after this point is lost. Keep a copy of important files on an external drive: a reset is not a backup, and it is not secure erasure either.'),
]


def show(paragraphs, **values):
    width = min(80, shutil.get_terminal_size().columns - 1)
    for paragraph in paragraphs:
        print("\n" + textwrap.fill(tr(paragraph, **values), width))
    print()


def helper(*args):
    subprocess.run(["sudo", HELPER, *args], check=True)


def cancelled():
    print(tr('Cancelled; nothing was changed.'))


def reset(mode):
    show(FIRST_WARNINGS[mode])
    if input(tr('Continue?') + ' [y/N]: ').strip().lower() not in ("y", "yes"):
        cancelled()
        return
    helper("status")
    show(SECOND_WARNING, host=socket.gethostname())
    typed = input(tr('Type {CONFIRMATION} to reset this computer (anything else cancels): ', CONFIRMATION=f'{CONFIRMATION}'))
    if typed != CONFIRMATION:
        cancelled()
        return
    helper("reset", "--mode", mode, "--confirm", typed)


def main(action):
    if action == "status":
        helper("status")
    elif action in FIRST_WARNINGS:
        reset(action)
    else:
        raise ValueError('Unknown factory reset action')


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
