#!/usr/bin/env python3
"""Laptop battery charge limit; changes only after typed confirmation."""
import eitr_bootstrap
import json
from eitr_battery import system_batteries
from eitr_i18n import tr
from pathlib import Path
import subprocess
import sys

# Packaged location first, then the older manual install path; both root-owned.
ROOT_HELPERS = ("/usr/lib/eitr/eitr-system", "/usr/local/lib/eitr/eitr-system")


def valid_limit(value):
    return value == "off" or (value.isdigit() and 60 <= int(value) <= 100)


def main(args):
    if args == ["menu-state"]:
        batteries = system_batteries()
        try:
            current = Path('/etc/eitr/battery-limit').read_text().strip()
        except OSError:
            current = "off"
        print(json.dumps({'available': bool(batteries), 'current': current}))
        return
    helper = next((path for path in ROOT_HELPERS if Path(path).is_file()), None)
    if helper is None:
        raise RuntimeError(tr('The root-owned Eitr helper is not installed. See distro/README.md; never sudo a user-writable helper.'))
    if args == ["status"]:
        # Reading sysfs thresholds needs no privileges.
        subprocess.run([helper, "battery-limit-status"], check=False)
        return
    if len(args) != 2 or args[0] != "set" or not valid_limit(args[1]):
        raise ValueError('Usage: battery-limit.py status | set <60-100|off>')
    value = args[1]
    if value == "off":
        print(tr('This removes the charge limit, so the battery charges to 100%.'))
    else:
        print(tr('Charging will stop at {value}% to reduce battery wear, also after reboot and resume.', value=f'{value}'))
        print(tr('Only firmware that exposes charge_control_end_threshold supports this.'))
    if input(tr('Type {confirmation} to apply (anything else cancels): ', confirmation='yes')) != "yes":
        return
    subprocess.run(["sudo", helper, "battery-limit", value], check=True)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
