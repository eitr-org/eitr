#!/usr/bin/env python3
"""Choose the next boot's network stack, with an explicit reboot prompt."""
import eitr_bootstrap
from eitr_i18n import tr
from pathlib import Path
import subprocess
import sys

HELPER = Path("/usr/lib/eitr/eitr-network")


def main(args):
    if len(args) != 1 or args[0] not in ("iwd", "networkmanager", "restore"):
        raise ValueError(tr('Choose iwd, networkmanager, or restore'))
    if not HELPER.is_file() or HELPER.stat().st_uid != 0 or HELPER.stat().st_mode & 0o022:
        raise RuntimeError(tr('Install the root-owned Eitr network helper first. See distro/NETWORKING.md.'))
    running = [name for name, unit in (("iwd", "iwd.service"), ("NetworkManager", "NetworkManager.service"))
               if subprocess.run(["systemctl", "is-active", "--quiet", unit]).returncode == 0]
    print(tr('Running now: {backends}', backends=', '.join(running) or tr('no WiFi backend')))
    print(tr('This changes the network backend only after rebooting.'))
    print(tr('Saved profiles are kept separately; you may need to reconnect after the first switch.'))
    print(tr('Custom static-IP/VPN setups need manual review before switching.'))
    if input(tr('Save this choice for the next boot?') + ' [y/N] ').strip().lower() not in ("y", "yes"):
        return
    command = ["sudo", str(HELPER), "restore"] if args[0] == "restore" else ["sudo", str(HELPER), "stage", args[0]]
    subprocess.run(command, check=True)
    if input(tr('Reboot now to apply?') + ' [y/N] ').strip().lower() in ("y", "yes"):
        subprocess.run(["systemctl", "reboot"], check=True)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
