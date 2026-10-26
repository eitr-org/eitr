#!/usr/bin/env python3
"""Confirm mirror maintenance; privileged writes belong to eitr-system."""
import eitr_bootstrap
from eitr_i18n import tr
from eitr_terminal import read_line_or_escape, wait_for_escape
import json
import subprocess
import sys

HELPER = "/usr/lib/eitr/eitr-system"


def main():
    try:
        status = json.loads(subprocess.check_output([HELPER, "mirrors-status"], text=True))
    except (OSError, ValueError, subprocess.CalledProcessError):
        # Without a readable status there is simply no backup to offer.
        status = {}
    print(tr("Choose recent HTTPS mirrors by download speed. The previous list is backed up; worldwide mirrors remain as fallbacks."))
    restore = sys.argv[1:] == ["restore"]
    if restore and not status.get("backup_available"):
        print(tr("No previous mirrorlist is available."))
        wait_for_escape()
        return
    if not restore and status.get("backup_available"):
        print(tr("To restore the previous list, type restore and press Enter instead."))
    answer = read_line_or_escape(tr("Press Enter to continue or Esc to cancel: "))
    if answer is None:
        return
    if answer == "restore" and status.get("backup_available"):
        restore = True
    elif answer != "":
        return
    subprocess.run(["sudo", HELPER, "mirrors-restore" if restore else "mirrors-rank"], check=True)
    wait_for_escape()


if __name__ == "__main__":
    main()
