#!/usr/bin/env python3
"""Eitr factory reset: a read-only first-login restore point and two resets.

capture  The installer's last step. Saves read-only snapshots of the @ and @home
         subvolumes and an archive of the EFI partition under the top-level
         @eitr-factory subvolume, outside Snapper's configs and cleanup.
status   Reports whether this computer can be reset.
reset    Prepares writable copies of the restore point beside the running
         system, swaps them in by renaming subvolumes and restarts. The running
         root and home are never written; they are kept under
         @eitr-reset-previous until the reset system has started.
finish   Boot service: deletes the previous system once the reset one runs.

See distro/FACTORY-RESET.md for the design and manual recovery.
"""
import eitr_bootstrap
from eitr_i18n import tr
import argparse
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

FACTORY = "@eitr-factory"
PREVIOUS = "@eitr-reset-previous"
ROOT_SUBVOLUME = "@"
HOME_SUBVOLUME = "@home"
CONFIRMATION = "RESET MY COMPUTER"
MODES = ("everything", "keep-files")
FINISH_UNIT = "eitr-factory-reset-finish.service"
FINISH_LINK = Path("etc/systemd/system/multi-user.target.wants") / FINISH_UNIT
SECURE_BOOT = Path("/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c")
MANUAL = "distro/FACTORY-RESET.md (also /usr/share/eitr/FACTORY-RESET.md)"


class ResetError(RuntimeError):
    pass


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def output(args):
    return subprocess.check_output(args, text=True).strip()


def in_chroot():
    return subprocess.run(["systemd-detect-virt", "--quiet", "--chroot"]).returncode == 0


def mount_info(path):
    """Device, filesystem type and UUID, and subvolume of the mount at path."""
    result = subprocess.run(["findmnt", "--json", "-M", path, "-o", "SOURCE,FSTYPE,UUID,OPTIONS"],
                            capture_output=True, text=True)
    if result.returncode:
        raise ResetError(tr('{path} is not a separate mount', path=f'{path}'))
    (filesystem,) = json.loads(result.stdout)["filesystems"]
    options = dict(option.partition("=")[::2] for option in filesystem["options"].split(","))
    return {"device": filesystem["source"].split("[", 1)[0], "fstype": filesystem["fstype"],
            "uuid": filesystem["uuid"], "subvolume": options.get("subvol", "")}


def layout():
    """The guided-install layout: @ and @home on one Btrfs filesystem, the EFI
    partition at /boot. Anything else is refused before any change."""
    root, home, boot = mount_info("/"), mount_info("/home"), mount_info("/boot")
    if root["fstype"] != "btrfs" or root["subvolume"] != "/" + ROOT_SUBVOLUME:
        raise ResetError(tr('The root filesystem is not the Btrfs @ subvolume of an Eitr installation'))
    if home["fstype"] != "btrfs" or home["uuid"] != root["uuid"] or home["subvolume"] != "/" + HOME_SUBVOLUME:
        raise ResetError(tr('/home is not the @home subvolume beside the root filesystem'))
    if boot["fstype"] != "vfat":
        raise ResetError(tr('/boot is not the EFI system partition'))
    return {"device": root["device"], "uuid": root["uuid"], "boot_uuid": boot["uuid"]}


@contextlib.contextmanager
def top_level(device):
    """The Btrfs top level, where the subvolumes are named."""
    with tempfile.TemporaryDirectory(prefix="eitr-reset-", dir="/run") as directory:
        run(["mount", "-o", "subvolid=5", device, directory])
        try:
            yield Path(directory)
        finally:
            run(["umount", directory])


def subvolume_uuid(path):
    for line in output(["btrfs", "subvolume", "show", str(path)]).splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "UUID":
            return value.strip()
    raise ResetError(tr('{path} is not a Btrfs subvolume', path=f'{path}'))


def read_only(path):
    return output(["btrfs", "property", "get", "-ts", str(path), "ro"]) == "ro=true"


def snapshot(source, target, readonly=False):
    run(["btrfs", "subvolume", "snapshot", *(["-r"] if readonly else []), str(source), str(target)],
        stdout=subprocess.DEVNULL)


def delete(path):
    run(["btrfs", "subvolume", "delete", "--recursive", "--commit-after", str(path)], stdout=subprocess.DEVNULL)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def login_users(passwd):
    """Accounts with a home under /home, from an /etc/passwd text."""
    users = []
    for line in passwd.splitlines():
        fields = line.split(":")
        if len(fields) == 7 and fields[2].isdigit() and 1000 <= int(fields[2]) < 60000 \
                and fields[5].startswith("/home/") and fields[6] not in ("/usr/bin/nologin", "/bin/false"):
            users.append({"name": fields[0], "home": fields[5].removeprefix("/home/")})
    return users


def merged_shadow(restored, current):
    """The restored shadow file, keeping each remaining account's current password."""
    passwords = {}
    for line in current.splitlines():
        fields = line.split(":")
        if len(fields) == 9:
            passwords[fields[0]] = fields[1:3]
    lines = []
    for line in restored.splitlines():
        fields = line.split(":")
        if len(fields) == 9 and fields[0] in passwords:
            fields[1:3] = passwords[fields[0]]
        lines.append(":".join(fields))
    return "\n".join(lines) + "\n"


def settings_folder(stamp):
    return f"Settings before reset {stamp}"


def keep_files(home, factory_home, users, stamp):
    """Reset each restore-point account's settings and keep its files: hidden
    entries move into a visible folder, then the restore point's settings are
    copied back. Other accounts' folders are left as they are."""
    for user in users:
        current, original = home / user["home"], factory_home / user["home"]
        if not current.is_dir():
            run(["cp", "-a", "--reflink=auto", str(original), str(current)])
            continue
        hidden = sorted(entry for entry in current.iterdir() if entry.name.startswith("."))
        if hidden:
            folder = current / settings_folder(stamp)
            folder.mkdir(mode=0o700)
            owner = current.stat()
            os.chown(folder, owner.st_uid, owner.st_gid)
            for entry in hidden:
                entry.rename(folder / entry.name)
        restored = sorted(str(entry) for entry in original.iterdir() if entry.name.startswith("."))
        if restored:
            run(["cp", "-a", "--reflink=auto", *restored, str(current) + "/"])


# Nested subvolumes a Keep My Files reset leaves behind: caches are rebuilt, and
# Snapper's home snapshot store belongs to the replaced system's configuration.
NOT_CARRIED = (".cache", ".snapshots")


def nested_subvolumes(top, home):
    """Paths, relative to home, of the subvolumes nested in it (home snapshots'
    exclusions such as Downloads or VM disks; see home-snapshots.py)."""
    prefix = str(home.relative_to(top)) + "/"
    paths = []
    for line in output(["btrfs", "subvolume", "list", "-o", str(home)]).splitlines():
        path = line.split(" path ", 1)[-1].strip()
        if path.startswith(prefix):
            paths.append(path.removeprefix(prefix))
    return sorted(paths)


def carry_subvolumes(top, old_home, new_home, users, stamp):
    """Move nested subvolumes from the replaced home into the restored one, where
    keep_files put the rest of their folder: hidden ones of restore-point accounts
    into the "Settings before reset" folder. Returns what could not be moved."""
    restore_point_homes = {user["home"] for user in users}
    failed = []
    for relative in nested_subvolumes(top, old_home):
        account, _, inside = relative.partition("/")
        if not inside or inside.split("/")[0] in NOT_CARRIED:
            continue
        if account in restore_point_homes and inside.startswith("."):
            target = new_home / account / settings_folder(stamp) / inside
        else:
            target = new_home / account / inside
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir() and not target.is_symlink() and not any(target.iterdir()):
                target.rmdir()  # The empty placeholder a snapshot leaves for a nested subvolume.
            if target.exists():
                target = target.with_name(target.name + " (kept by reset)")
            (old_home / relative).rename(target)
        except OSError as error:
            failed.append(f"{relative}: {error}")
    return failed


def secure_boot_enabled():
    try:
        return SECURE_BOOT.read_bytes()[-1:] == b"\x01"
    except OSError:
        return False


def capture():
    """Save the restore point once, from the installer's chroot."""
    info = layout()
    users = login_users(Path("/etc/passwd").read_text())
    if not users:
        raise ResetError(tr('No login account exists to restore'))
    if not (Path("/usr/lib/systemd/system") / FINISH_UNIT).is_file():
        raise ResetError(tr('{FINISH_UNIT} is missing; install the eitr-desktop package first', FINISH_UNIT=f'{FINISH_UNIT}'))
    with top_level(info["device"]) as top:
        target, partial = top / FACTORY, top / (FACTORY + ".partial")
        if target.exists():
            raise ResetError(tr('A factory reset point already exists; it is never replaced'))
        if partial.exists():
            delete(partial)
        run(["btrfs", "subvolume", "create", str(partial)], stdout=subprocess.DEVNULL)
        snapshot(top / ROOT_SUBVOLUME, partial / "root", readonly=True)
        snapshot(top / HOME_SUBVOLUME, partial / "home", readonly=True)
        run(["tar", "-C", "/boot", "-cf", str(partial / "boot.tar"), "."])
        manifest = {"version": 1, "created": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
                    "filesystem": info["uuid"], "boot_filesystem": info["boot_uuid"], "users": users,
                    "boot_sha256": sha256(partial / "boot.tar")}
        (partial / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        os.chmod(partial, 0o700)
        partial.rename(target)
        run(["btrfs", "property", "set", "-ts", str(target), "ro", "true"])
        run(["sync", "-f", str(target)])
    print(tr('Factory reset point saved for {usernames}.', usernames=f"{', '.join((user['name'] for user in users))}"))


def verified_factory(top, info):
    """The restore point's manifest after checking it belongs to this installation."""
    factory = top / FACTORY
    if not factory.is_dir():
        raise ResetError(tr('This computer has no factory reset point. Only computers installed with the Eitr ISO have one.'))
    for path in (factory, factory / "root", factory / "home"):
        if not read_only(path):
            raise ResetError(tr('{relative_path} is no longer read-only; the restore point is not trusted', relative_path=f'{path.relative_to(top)}'))
    manifest = json.loads((factory / "manifest.json").read_text())
    if manifest.get("version") != 1 or manifest.get("filesystem") != info["uuid"]:
        raise ResetError(tr('The restore point belongs to a different filesystem'))
    if manifest.get("boot_filesystem") != info["boot_uuid"]:
        raise ResetError(tr('The EFI partition changed since installation; reset is not safe'))
    if sha256(factory / "boot.tar") != manifest.get("boot_sha256"):
        raise ResetError(tr("The restore point's boot files are damaged"))
    for required in ("etc/fstab", "etc/shadow", f"usr/lib/systemd/system/{FINISH_UNIT}"):
        if not (factory / "root" / required).is_file():
            raise ResetError(tr('The restore point is missing /{required}', required=f'{required}'))
    return manifest


def check_ready(top, info):
    if in_chroot():
        raise ResetError(tr('Run factory reset on the installed system, not from a chroot'))
    if secure_boot_enabled():
        raise ResetError(tr('Secure Boot is on. The restored boot files are not signed with your keys; turn Secure Boot off in the firmware settings first'))
    if (top / PREVIOUS).exists():
        raise ResetError(tr('An earlier factory reset has not finished. Restart the computer first; if this persists, see {MANUAL}', MANUAL=f'{MANUAL}'))
    return verified_factory(top, info)


def status():
    info = layout()
    with top_level(info["device"]) as top:
        manifest = check_ready(top, info)
    names = ", ".join(user["name"] for user in manifest["users"])
    created = datetime.datetime.fromisoformat(manifest["created"]).astimezone()
    print(tr('Factory reset point: {created} (accounts: {names})', created=f'{created:%Y-%m-%d %H:%M %Z}', names=f'{names}'))
    print(tr('Filesystem {uuid} on {device}', uuid=f"{info['uuid']}", device=f"{info['device']}"))
    print(tr('Ready. Both resets restart the computer immediately.'))


def prepare_root(root, current_shadow):
    """The restore point's root as the next system: Snapper's subvolume, the
    accounts' current passwords and the service that finishes the reset."""
    snapshots = root / ".snapshots"
    if snapshots.is_dir() and not any(snapshots.iterdir()):
        snapshots.rmdir()
    if not snapshots.exists():
        run(["btrfs", "subvolume", "create", str(snapshots)], stdout=subprocess.DEVNULL)
        os.chmod(snapshots, 0o750)
    shadow = root / "etc/shadow"
    mode = shadow.stat().st_mode & 0o777
    replacement = shadow.with_name(".shadow.eitr-reset")
    replacement.write_text(merged_shadow(shadow.read_text(), current_shadow))
    os.chmod(replacement, mode)
    replacement.replace(shadow)
    link = root / FINISH_LINK
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(f"/usr/lib/systemd/system/{FINISH_UNIT}")


def copy_boot(source):
    """Overwrite the EFI partition's files with those under source. Extra files
    such as snapshot kernels stay; the restored menu no longer lists them."""
    run(["cp", "-rT", str(source), "/boot"])
    run(["sync", "-f", "/boot"])


def extract(archive, directory):
    directory.mkdir()
    run(["tar", "-C", str(directory), "--no-same-owner", "-xf", str(archive)])


def write_state(previous, state):
    manifest = previous / "manifest.json"
    data = json.loads(manifest.read_text())
    data["state"] = state
    manifest.write_text(json.dumps(data, indent=2) + "\n")
    run(["sync", "-f", str(manifest)])


def reset(mode, confirmation):
    if mode not in MODES:
        raise ResetError('Unknown reset mode {mode}'.format(mode=f'{mode}'))
    if confirmation != CONFIRMATION:
        raise ResetError(tr('Type {CONFIRMATION} exactly to confirm; nothing was changed', CONFIRMATION=f'{CONFIRMATION}'))
    info = layout()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H.%M")
    with top_level(info["device"]) as top:
        manifest = check_ready(top, info)
        factory, previous = top / FACTORY, top / PREVIOUS
        print(tr('Preparing the restored system (the running system is not changed yet)'))
        run(["btrfs", "subvolume", "create", str(previous)], stdout=subprocess.DEVNULL)
        os.chmod(previous, 0o700)
        try:
            (previous / "manifest.json").write_text(json.dumps({
                "mode": mode, "state": "prepared", "previous_root": subvolume_uuid(top / ROOT_SUBVOLUME),
                "created": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")}, indent=2) + "\n")
            snapshot(factory / "root", previous / "new-root")
            prepare_root(previous / "new-root", Path("/etc/shadow").read_text())
            if mode == "everything":
                snapshot(factory / "home", previous / "new-home")
            else:
                snapshot(top / HOME_SUBVOLUME, previous / "new-home")
                keep_files(previous / "new-home", factory / "home", manifest["users"], stamp)
            run(["tar", "-C", "/boot", "-cf", str(previous / "boot.tar"), "."])
            extract(factory / "boot.tar", previous / "new-boot")
        except BaseException:
            delete(previous)
            raise
        print(tr('Restoring the boot files'))
        try:
            copy_boot(previous / "new-boot")
        except BaseException:
            restore_boot(previous)
            delete(previous)
            raise
        print(tr('Switching to the restored system'))
        write_state(previous, "swapping")
        swapped = []
        try:
            for name, staged in ((ROOT_SUBVOLUME, "new-root"), (HOME_SUBVOLUME, "new-home")):
                (top / name).rename(previous / f"old{name}")
                swapped.append(name)
                (previous / staged).rename(top / name)
        except BaseException:
            undo_swap(top, previous, swapped)
            restore_boot(previous)
            delete(previous)
            raise
        failed = []
        if mode == "keep-files":
            failed = carry_subvolumes(top, previous / f"old{HOME_SUBVOLUME}", top / HOME_SUBVOLUME,
                                      manifest["users"], stamp)
        # A folder that could not be carried stays in the replaced home, which
        # finish() then keeps for review instead of deleting.
        write_state(previous, "carry-failed" if failed else "swapped")
        for problem in failed:
            print(tr('Could not carry {problem}; the previous home folder is kept at /{PREVIOUS} for review.', problem=f'{problem}', PREVIOUS=f'{PREVIOUS}'))
        run(["sync", "-f", str(top)])
    print(tr('Factory reset is ready. Restarting now.'))
    run(["systemctl", "reboot", "--no-wall"])


def undo_swap(top, previous, swapped):
    for name in reversed(swapped):
        if (top / name).exists():
            staged = "new-root" if name == ROOT_SUBVOLUME else "new-home"
            (top / name).rename(previous / staged)
        (previous / f"old{name}").rename(top / name)


def restore_boot(previous):
    with tempfile.TemporaryDirectory(dir=previous) as directory:
        extract(previous / "boot.tar", Path(directory) / "boot")
        copy_boot(Path(directory) / "boot")


def finish():
    """Delete the previous system once the reset one is running."""
    info = layout()
    with top_level(info["device"]) as top:
        previous = top / PREVIOUS
        if previous.exists():
            state = json.loads((previous / "manifest.json").read_text())
            if state.get("state") != "swapped":
                raise ResetError(tr('An interrupted factory reset needs manual review; see {MANUAL}', MANUAL=f'{MANUAL}'))
            if subvolume_uuid("/") == state["previous_root"]:
                raise ResetError(tr('The previous system is still running; see {MANUAL}', MANUAL=f'{MANUAL}'))
            delete(previous)
            print(tr('Factory reset finished; the previous system was deleted.'))
    (Path("/") / FINISH_LINK).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["capture", "status", "reset", "finish"])
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('This root-owned helper must run through sudo')
    try:
        if args.action == "capture":
            capture()
        elif args.action == "status":
            status()
        elif args.action == "reset":
            reset(args.mode, args.confirm)
        else:
            finish()
    except (OSError, ValueError, KeyError, ResetError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
