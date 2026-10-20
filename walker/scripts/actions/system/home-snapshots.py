#!/usr/bin/env python3
"""Walker's Home Folder Snapshots: show whether they are on, then switch after a yes."""
import eitr_bootstrap
from eitr_i18n import mark, tr
import getpass
from pathlib import Path
import subprocess
import sys

HELPER = "/usr/lib/eitr/eitr-home-snapshots"

EXPLANATION = {
    True: mark('Turning them off DELETES every home snapshot; files you have now are not touched.'),
    False: mark('Turning them on keeps a snapshot of the home folders every hour for a day and one a day for a week, deleting the oldest when the disk is 80% full. Caches, Downloads, VM disks and games are left out; they are prepared at the next start, before you log in. Restore with Snapshots > Restore a File or Folder.'),
}


def main():
    if not Path(HELPER).is_file():
        raise RuntimeError(tr('The root-owned Eitr helper is not installed; update the eitr-desktop package.'))
    active = subprocess.run([HELPER, "status"]).returncode == 0
    print("\n" + tr(EXPLANATION[active]))
    answer = input((tr('Turn home snapshots off?') if active else tr('Turn home snapshots on?')) + ' [y/N]: ').strip().lower()
    if answer not in ("y", "yes"):
        print(tr('Nothing was changed.'))
        return
    command = ["sudo", HELPER, "off"] if active else ["sudo", HELPER, "on", getpass.getuser()]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
    except (EOFError, KeyboardInterrupt):
        sys.exit("Nothing was changed.")
