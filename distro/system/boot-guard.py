#!/usr/bin/env python3
"""Eitr's boot guard: undo an update that leaves the computer unable to start.

System Update arms the guard with its "before" snapshot (``arm``). Each start
counts itself (``boot``, early in boot) and a start that keeps the login screen
or graphical desktop session up for a while counts as healthy (``healthy``), which disarms the guard. When
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
import contextlib
import fcntl
import datetime
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import tempfile
import time

STATE = Path("/var/lib/eitr")
ARMED = STATE / "boot-guard.json"
NOTICE = STATE / "boot-guard-notice.json"
FAILED = "@eitr-guard-failed"
FAILED_STARTS = 2
HEALTHY_SECONDS = 45
BOOT_ID = Path("/proc/sys/kernel/random/boot_id")
ROLLBACK = ".eitr-guard-rollback"
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
    with temporary.open("w") as stream:
        os.fchmod(stream.fileno(), mode)
        stream.write(json.dumps(data, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


@contextlib.contextmanager
def guard_lock():
    ARMED.parent.mkdir(parents=True, exist_ok=True)
    with ARMED.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def arm(snapshot, boot_archive):
    """Arm before launching a package upgrade. Other layouts use manual recovery."""
    reset = factory_reset()
    try:
        reset.layout()
    except reset.ResetError:
        return False
    if not str(snapshot).isdigit() or not boot_archive or not (Path(boot_archive) / "boot.tar").is_file():
        raise RuntimeError(tr('Cannot arm the boot guard without a snapshot and its boot files.'))
    with guard_lock():
        write(ARMED, {"snapshot": str(snapshot), "boot": str(boot_archive), "starts": 0,
                      "armed": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")})
    return True


def boot():
    """Early in every start: count it, and restore after too many failed starts."""
    armed = read(ARMED)
    if not armed:
        return
    reset = factory_reset()
    try:
        reset.layout()
    except reset.ResetError:
        return
    boot_id = BOOT_ID.read_text().strip()
    if armed.get("boot_id") == boot_id:
        return
    armed["boot_id"] = boot_id
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
        staging = Path(directory)
        restored_boot = staging / "restored-boot"
        reset.extract(archive, restored_boot)
        rollback = top / ROLLBACK
        rollback.mkdir(mode=0o700)
        saved_boot = rollback / "boot.tar"
        current, failed = top / reset.ROOT_SUBVOLUME, top / FAILED
        previous = top / f"{FAILED}-{uuid.uuid4().hex}" if failed.exists() else None
        renamed = False
        boot_changed = False
        try:
            reset.run(["tar", "-C", "/boot", "-cf", str(saved_boot), "."])
            reset.run(["sync", "-f", str(saved_boot)])
        except BaseException:
            saved_boot.unlink(missing_ok=True)
            rollback.rmdir()
            raise
        try:
            if previous:
                failed.rename(previous)
            boot_changed = True
            reset.copy_boot(restored_boot)
            current.rename(failed)
            renamed = True
            reset.snapshot(failed / ".snapshots" / number / "snapshot", current)
            (current / ".snapshots").rmdir()
            (failed / ".snapshots").rename(current / ".snapshots")
            # A record copied into the snapshot must not arm the restored system.
            (current / str(ARMED).lstrip("/")).unlink(missing_ok=True)
            write(current / str(NOTICE).lstrip("/"), {"snapshot": number, "restored": when, "failed": FAILED,
                                                      "cleaned": False}, mode=0o644)
            reset.run(["sync", "-f", str(top)])
        except BaseException:
            try:
                if renamed:
                    if current.exists():
                        if (current / ".snapshots").is_dir() and not (failed / ".snapshots").exists():
                            (current / ".snapshots").rename(failed / ".snapshots")
                        reset.delete(current)
                    failed.rename(current)
                if previous and previous.exists():
                    previous.rename(failed)
            finally:
                if boot_changed:
                    reset.extract(saved_boot, staging / "current-boot")
                    reset.copy_boot(staging / "current-boot", undo_source=restored_boot)
            saved_boot.unlink()
            rollback.rmdir()
            raise
        saved_boot.unlink()
        rollback.rmdir()
    reset.run(["systemctl", "reboot", "--no-wall"])


def graphical_sessions():
    """Active X11/Wayland sessions on the local seat, including SDDM's greeter."""
    ready = set()
    try:
        listing = subprocess.run(["loginctl", "list-sessions", "--json=short"],
                                 capture_output=True, text=True, check=True, timeout=5)
        for session in json.loads(listing.stdout or "[]") or []:
            if session.get("seat") != "seat0" or session.get("class") not in ("greeter", "user", "user-early"):
                continue
            identifier = session["session"]
            status = subprocess.run(["loginctl", "show-session", identifier, "-p", "Type", "-p", "Active"],
                                    capture_output=True, text=True, timeout=5)
            properties = set(status.stdout.splitlines())
            if status.returncode == 0 and "Active=yes" in properties and properties & {"Type=x11", "Type=wayland"}:
                ready.add(identifier)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return ready


def healthy(wait=HEALTHY_SECONDS):
    """Disarm only the guard record counted on this boot after sustained graphical readiness."""
    armed = read(ARMED)
    if armed and armed.get("boot_id") != BOOT_ID.read_text().strip():
        armed = None
    notice = read(NOTICE)
    if not armed and (not notice or notice.get("cleaned")):
        return
    since = {}
    while True:
        now = time.monotonic()
        since = {session: since.get(session, now) for session in graphical_sessions()}
        if any(now - start >= wait for start in since.values()):
            break
        time.sleep(5)
    with guard_lock():
        if armed and read(ARMED) == armed:
            ARMED.unlink(missing_ok=True)
    if notice and not notice.get("cleaned"):
        reset = factory_reset()
        with reset.top_level(reset.layout()["device"]) as top:
            for failed in top.glob(f"{FAILED}*"):
                prefix, _, suffix = failed.name.rpartition("-")
                if failed.name == FAILED or (prefix == FAILED and len(suffix) == 32 and all(
                        char in "0123456789abcdef" for char in suffix)):
                    reset.delete(failed)
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
