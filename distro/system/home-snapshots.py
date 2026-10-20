#!/usr/bin/env python3
"""Snapshots of the home folders, so a lost or changed file can be restored.

  eitr-home-snapshots status            on or off, how many, how much space
  eitr-home-snapshots on USER           start (USER may browse the snapshots)
  eitr-home-snapshots off               stop and delete every home snapshot
  eitr-home-snapshots exclude           (at boot) move caches, Downloads, VM
                                        disks and games out of the snapshots

Off by default. On, Snapper keeps a snapshot of /home every hour for a day and
one a day for a week, and deletes the oldest when free space falls below 20%.
Folders that change constantly or hold large, replaceable data become nested
Btrfs subvolumes, which snapshots of /home do not include. That conversion
moves files, so it runs at the next start, before anyone logs in
(eitr-home-exclusions.service). The factory reset's Keep My Files carries those
subvolumes across (factory-reset.py).
"""
import eitr_bootstrap
from eitr_i18n import tr
import argparse
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys

HOME = Path("/home")
CONFIG = "home"
STATE = Path("/var/lib/eitr")
PENDING = STATE / "home-exclusions-pending"
UNIT = "eitr-home-exclusions.service"
SNAPPER_CONFIGS = Path("/etc/snapper/configs")
# Relative to each home folder. Missing ones are created only when marked True,
# so new data there starts out excluded.
EXCLUDED = {
    ".cache": True,
    "Downloads": True,
    ".local/share/Steam": False,
    ".local/share/libvirt/images": False,
    ".local/share/gnome-boxes/images": False,
    "VirtualBox VMs": False,
}
POLICY = ["TIMELINE_CREATE=yes", "TIMELINE_CLEANUP=yes", "TIMELINE_MIN_AGE=1800",
          "TIMELINE_LIMIT_HOURLY=24", "TIMELINE_LIMIT_DAILY=7", "TIMELINE_LIMIT_WEEKLY=0",
          "TIMELINE_LIMIT_MONTHLY=0", "TIMELINE_LIMIT_QUARTERLY=0", "TIMELINE_LIMIT_YEARLY=0",
          "NUMBER_CLEANUP=yes", "FREE_LIMIT=0.2", "SYNC_ACL=yes"]


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def is_subvolume(path):
    return path.is_dir() and subprocess.run(["btrfs", "subvolume", "show", str(path)],
                                            capture_output=True).returncode == 0


def snapper_has_config():
    return subprocess.run(["snapper", "-c", CONFIG, "get-config"], capture_output=True).returncode == 0


def home_is_btrfs_subvolume():
    result = subprocess.run(["findmnt", "-n", "-o", "FSTYPE", "-M", str(HOME)], capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() == "btrfs"


def login_homes():
    """Home folders of login accounts under /home."""
    return [Path(account.pw_dir) for account in pwd.getpwall()
            if 1000 <= account.pw_uid < 60000 and account.pw_dir.startswith(str(HOME) + "/")
            and account.pw_shell not in ("/usr/bin/nologin", "/bin/false") and Path(account.pw_dir).is_dir()]


def status():
    if not snapper_has_config():
        print(tr('Home snapshots: off'))
        return 3
    result = subprocess.run(["snapper", "-c", CONFIG, "--jsonout", "list"], capture_output=True, text=True)
    snapshots = [item for item in json.loads(result.stdout or "{}").get(CONFIG, []) if item.get("number")]
    pending = " (folders to exclude are moved at the next start)" if PENDING.exists() else ""
    print(tr('Home snapshots: on, {snapshot_count} kept{pending}', snapshot_count=f'{len(snapshots)}', pending=f'{pending}'))
    return 0


def turn_on(user):
    if not home_is_btrfs_subvolume():
        raise RuntimeError(tr('/home is not on Btrfs, so it cannot have snapshots'))
    try:
        pwd.getpwnam(user)
    except KeyError:
        raise RuntimeError(tr('No account named {user}', user=f'{user}')) from None
    if not snapper_has_config():
        run(["snapper", "-c", CONFIG, "create-config", str(HOME)])
    run(["snapper", "-c", CONFIG, "set-config", *POLICY, f"ALLOW_USERS={user}"])
    run(["systemctl", "enable", "--now", "snapper-timeline.timer", "snapper-cleanup.timer"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    STATE.mkdir(parents=True, exist_ok=True)
    PENDING.touch()
    run(["systemctl", "enable", UNIT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run(["snapper", "-c", CONFIG, "create", "--description", "Eitr home snapshots turned on",
         "--cleanup-algorithm", "timeline"])
    print(tr('Home snapshots are on: one every hour for a day and one a day for a week. Caches, Downloads, VM disks and games are left out from the next start.'))


def turn_off():
    if snapper_has_config():
        run(["snapper", "-c", CONFIG, "delete-config"])
    # The hourly timer stays for any other config that still takes timeline snapshots.
    if not any('TIMELINE_CREATE="yes"' in config.read_text() for config in SNAPPER_CONFIGS.glob("*")
               if config.is_file()):
        subprocess.run(["systemctl", "disable", "--now", "snapper-timeline.timer"], capture_output=True)
    PENDING.unlink(missing_ok=True)
    subprocess.run(["systemctl", "disable", UNIT], capture_output=True)
    print(tr('Home snapshots are off, and the existing ones were deleted. The excluded folders stay as they are.'))


def convert(path):
    """Turn a folder into a subvolume in place, keeping its files (reflinked, not copied)."""
    staging = path.with_name(path.name + ".eitr-subvolume")
    old = path.with_name(path.name + ".eitr-old")
    if staging.exists() or old.exists():
        raise RuntimeError(tr('{staging} or {old} is left over from an earlier attempt; check and remove it', staging=f'{staging}', old=f'{old}'))
    run(["btrfs", "subvolume", "create", str(staging)], stdout=subprocess.DEVNULL)
    try:
        info = path.stat()
        os.chown(staging, info.st_uid, info.st_gid)
        os.chmod(staging, info.st_mode & 0o7777)
        run(["cp", "-a", "--reflink=always", f"{path}/.", f"{staging}/"])
        path.rename(old)
    except BaseException:
        run(["btrfs", "subvolume", "delete", str(staging)], stdout=subprocess.DEVNULL)
        raise
    staging.rename(path)
    shutil.rmtree(old)


def exclude(homes=None):
    """Make the excluded folders of every home nested subvolumes. Runs before login."""
    for home in homes if homes is not None else login_homes():
        owner = home.stat()
        for relative, create in EXCLUDED.items():
            path = home / relative
            if is_subvolume(path):
                continue
            if path.is_dir() and not path.is_symlink():
                convert(path)
            elif create and not path.exists():
                run(["btrfs", "subvolume", "create", str(path)], stdout=subprocess.DEVNULL)
                os.chown(path, owner.st_uid, owner.st_gid)
                os.chmod(path, 0o755 if relative == "Downloads" else 0o700)
    PENDING.unlink(missing_ok=True)
    subprocess.run(["systemctl", "disable", UNIT], capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["status", "on", "off", "exclude"])
    parser.add_argument("user", nargs="?")
    args = parser.parse_args()
    if args.action == "status":
        return status()
    if os.geteuid() != 0:
        parser.error('Run through sudo (System > Maintenance > Snapshots)')
    if args.action == "on":
        if not args.user:
            parser.error('on needs the user who may browse the snapshots')
        turn_on(args.user)
    elif args.action == "off":
        turn_off()
    else:
        exclude()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(f"eitr-home-snapshots: {error}")
