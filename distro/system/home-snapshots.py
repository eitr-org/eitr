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
import errno
from contextlib import contextmanager
import json
import os
from pathlib import Path
import pwd
import shutil
import stat
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
    """A Btrfs subvolume's top directory is always inode 256; this needs no root."""
    try:
        info = Path(path).lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISDIR(info.st_mode) and info.st_ino == 256


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


@contextmanager
def directory(path, device=None):
    """Pin every ancestor without following symlinks, optionally on one device."""
    path = Path(path)
    descriptor = os.open("/" if path.is_absolute() else ".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts:
            if component == "/":
                continue
            if component == "..":
                raise RuntimeError("Parent traversal is not allowed")
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            if device is not None and os.fstat(descriptor).st_dev != device:
                raise RuntimeError(f"{path} leaves the home's filesystem")
        yield descriptor
    finally:
        os.close(descriptor)


def check_tree(path, device):
    """Refuse nested mounts rather than silently omit their data from the copy."""
    def failed(error):
        raise error

    for parent, folders, files in os.walk(path, followlinks=False, onerror=failed):
        for name in folders + files:
            if os.lstat(Path(parent) / name).st_dev != device:
                raise RuntimeError(f"{path} leaves the home's filesystem")


def check_leftovers(path):
    staging = path.with_name(path.name + ".eitr-subvolume")
    old = path.with_name(path.name + ".eitr-old")
    if os.path.lexists(staging) or os.path.lexists(old):
        raise RuntimeError(tr('{staging} or {old} is left over from an earlier attempt; check and remove it', staging=f'{staging}', old=f'{old}'))
    return staging, old


def convert(path):
    """Convert as the home owner; failed copies are left for manual inspection."""
    if os.geteuid() == 0:
        raise RuntimeError("Home conversion must not run as root")
    staging, old = check_leftovers(path)
    try:
        with directory(path) as source:
            source_info = os.fstat(source)
            check_tree(path, source_info.st_dev)
            run(["btrfs", "subvolume", "create", str(staging)], stdout=subprocess.DEVNULL)
            # A new Btrfs subvolume has its own st_dev. Creation in this pinned
            # parent keeps it on the same filesystem; do not compare device numbers.
            with directory(staging) as destination:
                # Pin both copy endpoints so concurrent symlink swaps cannot redirect cp.
                # cp preserves metadata as this user, without privileged ownership changes.
                destination_info = os.fstat(destination)
                run(["cp", "-a", "--one-file-system", "--reflink=always",
                     f"/proc/self/fd/{source}/.", f"/proc/self/fd/{destination}/"],
                    pass_fds=(source, destination))
                for candidate, expected in ((path, source_info), (staging, destination_info)):
                    actual = candidate.lstat()
                    if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
                        raise RuntimeError(f"{candidate} changed during conversion")
                path.rename(old)
                staging.rename(path)
        shutil.rmtree(old)
    except BaseException as error:
        # Subvolume deletion normally needs root or user_subvol_rm_allowed.
        # Never ask the privileged parent to clean up a user-controlled pathname.
        raise RuntimeError(f"{error}; conversion stopped; check {staging} and {old}; "
                           "original files remain at the original path or in .eitr-old") from error


def exclude_home(home_descriptor):
    """All home mutations happen after the child permanently drops privileges."""
    if os.geteuid() == 0:
        raise RuntimeError("Home exclusions must not run as root")
    device = os.fstat(home_descriptor).st_dev
    previous = os.open(".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for relative, create in EXCLUDED.items():
            os.fchdir(home_descriptor)
            target = Path(relative)
            try:
                with directory(target.parent, device) as parent:
                    os.fchdir(parent)
                    path = Path(target.name)
                    check_leftovers(path)
                    try:
                        info = path.lstat()
                    except FileNotFoundError:
                        if create:
                            # Restrictive umask applies during creation, before chmod.
                            run(["btrfs", "subvolume", "create", str(path)], stdout=subprocess.DEVNULL)
                            with directory(path) as created:
                                os.fchmod(created, 0o755 if relative == "Downloads" else 0o700)
                        continue
                    if stat.S_ISLNK(info.st_mode):
                        # A symlinked folder (for example Downloads on another disk) is left as it is.
                        print(f"eitr-home-snapshots: leaving symlinked {relative} as it is", file=sys.stderr)
                        continue
                    if not stat.S_ISDIR(info.st_mode):
                        continue
                    if info.st_uid != os.geteuid():
                        raise RuntimeError(f"Excluded folder is not owned by the home owner: {relative}")
                    # Existing nested subvolumes have distinct st_dev values and
                    # need no conversion or writes, including on subsequent boots.
                    if is_subvolume(path):
                        continue
                    if info.st_dev != device:
                        raise RuntimeError(f"{relative} leaves the home's filesystem")
                    convert(path)
            except FileNotFoundError:
                # Optional folders may have missing ancestors.
                if create:
                    raise
            except OSError as error:
                if error.errno not in (errno.ELOOP, errno.ENOTDIR):
                    raise
                # A symlinked parent folder is never followed; the folder is left as it is.
                print(f"eitr-home-snapshots: leaving {relative} as it is: a parent folder is a symlink", file=sys.stderr)
    finally:
        os.fchdir(previous)
        os.close(previous)


def drop_privileges(owner):
    account = pwd.getpwuid(owner.st_uid)
    if owner.st_uid == 0:
        raise RuntimeError("Refusing a root-owned home")
    os.setgroups(os.getgrouplist(account.pw_name, account.pw_gid))
    os.setgid(account.pw_gid)
    os.setuid(owner.st_uid)
    os.umask(0o077)


def exclude(homes=None):
    """Root retains Snapper state; a separate unprivileged child handles each home."""
    for home in homes if homes is not None else login_homes():
        with directory(home) as descriptor:
            owner = os.fstat(descriptor)
            sys.stdout.flush()
            sys.stderr.flush()
            child = os.fork()
            if child == 0:
                try:
                    drop_privileges(owner)
                    exclude_home(descriptor)
                except BaseException as error:
                    print(f"eitr-home-snapshots: {home}: {error}", file=sys.stderr, flush=True)
                    os._exit(1)
                os._exit(0)
            _, status = os.waitpid(child, 0)
            if status != 0:
                raise RuntimeError(f"Home exclusions failed for {home}; pending setup retained")
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
