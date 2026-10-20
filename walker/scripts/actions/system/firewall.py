#!/usr/bin/env python3
"""Walker's Firewall: show whether it is on, then switch it only after a yes."""
import eitr_bootstrap
from eitr_i18n import mark, tr
from pathlib import Path
import subprocess
import sys

HELPER = "/usr/lib/eitr/eitr-system"

EXPLANATION = {
    True: mark('Turning it off lets every incoming connection reach the apps listening for it.'),
    False: mark('Turning it on refuses incoming connections except replies to this computer and the sharing apps (KDE Connect, LocalSend); SSH stays reachable when it is enabled.'),
}


def main():
    if not Path(HELPER).is_file():
        raise RuntimeError(tr('The root-owned Eitr helper is not installed; update the eitr-desktop package.'))
    status = subprocess.run([HELPER, "firewall-status"])
    active = status.returncode == 0
    print("\n" + tr(EXPLANATION[active]))
    answer = input((tr('Turn the firewall off?') if active else tr('Turn the firewall on?')) + ' [y/N]: ').strip().lower()
    if answer not in ("y", "yes"):
        print(tr('Nothing was changed.'))
        return
    subprocess.run(["sudo", HELPER, "firewall-off" if active else "firewall-on"], check=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
    except (EOFError, KeyboardInterrupt):
        sys.exit("Nothing was changed.")
