#!/usr/bin/env python3
"""Eitr's boot guard: undo an update that leaves the computer unable to start.

System Update arms the guard with its "before" snapshot (``arm``). Each start
counts itself (``boot``, early in boot) and a start that keeps the login screen
up for a while counts as healthy (``healthy``), which disarms the guard. When
two starts in a row never got there, the third restores the system and its boot
files from that snapshot, keeps the failed system aside, and restarts. The
restored system deletes the failed one once it is healthy and tells the user at
the next login (``notice``).

Only Eitr's guided-install layout is guarded: the root on the Btrfs @ subvolume
with Snapper's store nested at @/.snapshots, /home on @home and the EFI
partition at /boot, whose files System Update archives with every snapshot.
A system that cannot start the kernel never runs this; its snapshots stay in
the boot menu (distro/RECOVERY.md).
"""
import eitr_bootstrap
from eitr_i18n import tr
import argparse
import datetime
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

STATE = Path("/var/lib/eitr")
ARMED = STATE / "boot-guard.json"
NOTICE = STATE / "boot-guard-notice.json"
FAILED = "@eitr-guard-failed"
FAILED_STARTS = 2
HEALTHY_SECONDS = 45
LOGIN_UNIT = "display-manager.service"
SCRATCH = Path("/run")


def factory_reset():
    """The factory reset owns Eitr's Btrfs layout helpers; reuse them, not copies."""
    here = Path(__file__).resolve().parent
    for name in ("eitr-factory-reset", "factory-reset.py"):
        if (here / name).is_file():
            loader = importlib.machinery.SourceFileLoader("eitr_factory_reset", str(here / name))
            spec = importlib.util.spec_from_loader(loader.name, loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            return module
    raise RuntimeError(tr('The factory reset helper is missing beside the boot guard'))


def write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    os.chmod(temporary, mode)
    temporary.replace(path)


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def arm(snapshot, boot_archive):
    """Called after a successful update; silently does nothing outside Eitr's layout."""
    if not str(snapshot).isdigit() or not boot_archive or not (Path(boot_archive) / "boot.tar").is_file():
        return False
    try:
        factory_reset().layout()
    except Exception:
        return False
    write(ARMED, {"snapshot": str(snapshot), "boot": str(boot_archive), "starts": 0,
                  "armed": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")})
    return True


def boot():
    """Early in every start: count it, and restore after too many failed starts."""
    armed = read(ARMED)
    if not armed:
        return
    armed["starts"] = int(armed.get("starts", 0)) + 1
    write(ARMED, armed)
    if armed["starts"] > FAILED_STARTS:
        restore(armed)


def restore(armed):
    reset = factory_reset()
    info = reset.layout()
    number = armed["snapshot"]
    archive = Path(armed["boot"]) / "boot.tar"
    when = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    print(tr("Eitr's boot guard: {FAILED_STARTS} starts after the last update failed; restoring the system from snapshot {number}.", FAILED_STARTS=f'{FAILED_STARTS}', number=f'{number}'))
    with reset.top_level(info["device"]) as top, tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
        source = top / reset.ROOT_SUBVOLUME / ".snapshots" / number / "snapshot"
        if not source.is_dir() or not archive.is_file():
            raise RuntimeError(tr('Snapshot {number} or its boot files are missing; nothing was changed', number=f'{number}'))
        if (top / FAILED).exists():
            raise RuntimeError(tr('{FAILED} already exists from an earlier restore; nothing was changed', FAILED=f'{FAILED}'))
        staging = Path(directory)
        reset.extract(archive, staging / "restored-boot")
        # Today's boot files, to put back if the swap below fails.
        reset.run(["tar", "-C", "/boot", "-cf", str(staging / "current-boot.tar"), "."])
        reset.copy_boot(staging / "restored-boot")
        current, failed = top / reset.ROOT_SUBVOLUME, top / FAILED
        try:
            current.rename(failed)
            reset.snapshot(failed / ".snapshots" / number / "snapshot", current)
            # Snapper's store is a nested subvolume: move it into the restored root.
            (current / ".snapshots").rmdir()
            (failed / ".snapshots").rename(current / ".snapshots")
        except BaseException:
            if failed.exists():
                if current.exists():
                    if (current / ".snapshots").is_dir() and not (failed / ".snapshots").exists():
                        (current / ".snapshots").rename(failed / ".snapshots")
                    reset.delete(current)
                failed.rename(current)
            reset.extract(staging / "current-boot.tar", staging / "current-boot")
            reset.copy_boot(staging / "current-boot")
            raise
        # A record copied into the snapshot by an earlier update must not arm the restored system.
        (current / str(ARMED).lstrip("/")).unlink(missing_ok=True)
        write(current / str(NOTICE).lstrip("/"), {"snapshot": number, "restored": when, "failed": FAILED,
                                                  "cleaned": False}, mode=0o644)
        reset.run(["sync", "-f", str(top)])
    reset.run(["systemctl", "reboot"])


def healthy(wait=HEALTHY_SECONDS, timeout=600):
    """After the login screen stayed up for a while: disarm, and finish a restore."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if subprocess.run(["systemctl", "is-active", "--quiet", LOGIN_UNIT]).returncode == 0:
            time.sleep(wait)
            if subprocess.run(["systemctl", "is-active", "--quiet", LOGIN_UNIT]).returncode == 0:
                break
        time.sleep(5)
    else:
        return
    ARMED.unlink(missing_ok=True)
    notice = read(NOTICE)
    if notice and not notice.get("cleaned"):
        reset = factory_reset()
        with reset.top_level(reset.layout()["device"]) as top:
            if (top / notice["failed"]).exists():
                reset.delete(top / notice["failed"])
        notice["cleaned"] = True
        write(NOTICE, notice, mode=0o644)


def notice():
    """For the desktop: a restore that has not been announced yet, as JSON."""
    data = read(NOTICE)
    print(json.dumps(data or {}))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["arm", "boot", "healthy", "notice"])
    parser.add_argument("snapshot", nargs="?")
    parser.add_argument("archive", nargs="?")
    args = parser.parse_args()
    if args.action == "notice":
        notice()
        return 0
    if os.geteuid() != 0:
        parser.error('The boot guard runs as root (System Update and its own services start it)')
    if args.action == "arm":
        arm(args.snapshot, args.archive)
    elif args.action == "boot":
        boot()
    else:
        healthy()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(f"eitr-boot-guard: {error}")
