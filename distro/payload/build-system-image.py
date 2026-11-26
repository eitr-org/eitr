#!/usr/bin/env python3
"""Prepare the generalized SquashFS root and the ISO's supplemental package pool."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit

import image_hooks
import payload
import system_image

HOOKS = "base udev autodetect microcode modconf kms keyboard keymap consolefont block plymouth filesystems fsck"
GENERALIZE = (
    "etc/machine-id", "var/lib/dbus/machine-id", "etc/pacman.d/gnupg",
    "etc/.pwd.lock", "etc/passwd-", "etc/group-", "etc/shadow-", "etc/gshadow-",
    "etc/ssh/ssh_host_*", "etc/hostname", "etc/localtime", "etc/locale.conf",
    "etc/vconsole.conf", "etc/credstore", "etc/credstore.encrypted",
    "boot/initramfs-*", "boot/loader/random-seed", "var/lib/systemd/random-seed",
    "var/lib/systemd/credential.secret", "var/lib/systemd/timesync/clock",
    "var/lib/pacman/sync/*", "var/cache/pacman/pkg/*",
    "root/*", "root/.[!.]*", "tmp/*", "tmp/.[!.]*", "var/tmp/*", "var/tmp/.[!.]*",
)


def run(*args):
    subprocess.run(args, check=True)


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def generalize(root):
    for pattern in GENERALIZE:
        for path in root.glob(pattern):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    # Keep journal and service directories with their package-created modes.
    for path in (root / "var/log").rglob("*"):
        if path.is_file() and not path.is_symlink():
            path.unlink()


def package_hooks(root, pool):
    package = next(path for path in pool.glob("mkinitcpio-*.pkg.tar.*")
                   if path.suffix != ".sig" and payload.package_file_name(path) == "mkinitcpio")
    return image_hooks.deferred(
        root, output("bsdtar", "-xOf", package, image_hooks.HOOK),
        output("bsdtar", "-xOf", package, image_hooks.KERNEL_SCRIPT.lstrip("/")))


def configure(root):
    path = root / "etc/mkinitcpio.conf"
    values = {"MODULES": "", "BINARIES": "", "FILES": "", "HOOKS": HOOKS}
    text = path.read_text()
    for key, value in values.items():
        text, matches = re.subn(rf"^{key}=.*$", f"{key}=({value})", text, flags=re.MULTILINE)
        if matches != 1:
            raise ValueError(f"Unexpected mkinitcpio setting: {key}")
    path.write_text(text)
    (root / "etc/systemd/zram-generator.conf").write_text("[zram0]\ncompression-algorithm = zstd\n")
    run("systemctl", "--root", root, "enable", "systemd-timesyncd", "systemd-zram-setup@zram0.service")
    run("arch-chroot", root, "plymouth-set-default-theme", "eitr")
    conf = root / "etc/pacman.conf"
    online = payload.online_pacman_conf(conf.read_text())
    if payload.signing_key():
        online += payload.eitr_repository()
    conf.write_text(online)
    shutil.copyfile(payload.DISTRO / "payload/mirrorlist", root / "etc/pacman.d/mirrorlist")


def resolve(root, conf, medium):
    needed = set()
    for packages in payload.optional_transactions():
        locations = output("pacman", "--root", root, "--config", conf, "-Sp", "--needed",
                           "--noconfirm", "--print-format", "%l", "--", *packages)
        for location in locations.splitlines():
            url = urlsplit(location)
            path = Path(unquote(url.path))
            if (url.scheme != "file" or path.parent not in (medium / "pool", medium / "repo")
                    or not path.is_file() or
                    (path.parent.name == "pool" and not Path(f"{path}.sig").is_file())):
                raise ValueError(f"Missing supplemental package or signature: {location}")
            needed.add(path)
    return needed


def prune(medium, needed, installed):
    for folder, names in system_image.package_files(medium).items():
        for name in names:
            path = medium / folder / name
            if path not in needed:
                path.unlink()
                Path(f"{path}.sig").unlink(missing_ok=True)
            elif payload.package_file_name(path) in installed:
                raise ValueError(f"Supplemental transaction changes an image package: {name}")


def strap(root, conf, packages):
    run("pacstrap", "-G", "-M", "-C", conf, root, "--needed", *dict.fromkeys(packages))


def build(full_payload, medium, work, commit):
    work.mkdir()
    shutil.copytree(full_payload, medium, copy_function=shutil.copyfile)
    data = json.loads((medium / "manifest.json").read_text())
    if data["source_commit"] != commit:
        raise ValueError("The payload and ISO source commits differ")
    with tempfile.TemporaryDirectory(dir=work) as staging:
        staging = Path(staging)
        root = staging / "root"
        root.mkdir()
        (staging / "cache").mkdir()
        # The build keyring stays outside the image; every installation makes its own.
        keyring = staging / "gnupg"
        conf = staging / "pacman.conf"
        offline = payload.pacman_conf(medium / "pool", medium / "repo")
        # pacman reads hook overrides from HookDir as given, not under --root.
        conf.write_text(offline.replace(
            "[options]\n", f"[options]\nGPGDir = {keyring}\nHookDir = {root / 'etc/pacman.d/hooks'}\n"
            # An empty cache, so resolving the supplements names the medium's files.
            f"CacheDir = {staging / 'cache'}\n", 1))
        run("pacman-key", "--gpgdir", keyring, "--init")
        try:
            run("pacman-key", "--gpgdir", keyring, "--populate", "archlinux")
            with package_hooks(root, medium / "pool"):
                *base, desktop = payload.fixed_transactions()
                for packages in base:
                    strap(root, conf, packages)
                base_packages = set(output("pacman", "--root", root, "-Qq").splitlines())
                strap(root, conf, desktop)
        finally:
            run("gpgconf", "--homedir", keyring, "--kill", "all")
        # pacstrap copies its own config into the root. Read the packaged default
        # while the archive is still available.
        pacman = next(path for path in (medium / "pool").glob("pacman-*.pkg.tar.*")
                      if path.suffix != ".sig" and payload.package_file_name(path) == "pacman")
        (root / "etc/pacman.conf").write_text(output("bsdtar", "-xOf", pacman, "etc/pacman.conf") + "\n")
        configure(root)
        installed = dict(line.split(maxsplit=1) for line in output("pacman", "--root", root, "-Q").splitlines())
        explicit = output("pacman", "--root", root, "-Qqe").splitlines()
        generalize(root)
        # Reuse the release's sync databases to resolve against the installed local DB.
        sync = root / "var/lib/pacman/sync"
        sync.mkdir(exist_ok=True)
        for directory in ("pool", "repo"):
            for database in (medium / directory).glob("*.db"):
                shutil.copyfile(database, sync / database.name)
        prune(medium, resolve(root, conf, medium), installed)
        resolve(root, conf, medium)
        for database in sync.iterdir():
            database.unlink()
        boot = root / "boot"
        if not (boot / "vmlinuz-linux").is_file() or not (root / "etc/mkinitcpio.d/linux.preset").is_file():
            raise ValueError("Kernel package hook did not stage the kernel and preset")
        boot.rename(root / "usr/lib/eitr/install-boot")
        image = medium / system_image.IMAGE
        run("mksquashfs", root, image, "-noappend", "-comp", "zstd", "-b", "1M", "-xattrs", "-exit-on-error")
    repositories = system_image.package_files(medium)
    data["packages"] = {"official": repositories["pool"], "eitr": repositories["repo"]}
    data["system_image"] = {"format": system_image.FORMAT, "source_commit": commit,
                            "sha256": system_image.sha256(image), "bytes": image.stat().st_size,
                            "packages": installed, "explicit": explicit,
                            "desktop_dependencies": sorted(set(installed) - base_packages - set(explicit)),
                            "repositories": repositories, "databases": system_image.database_hashes(medium)}
    (medium / "manifest.json").write_text(json.dumps(data, indent=2) + "\n")
    files = sorted(path for path in medium.rglob("*") if path.is_file()
                   and path.name not in ("manifest.json", "SHA256SUMS"))
    (medium / "SHA256SUMS").write_text("".join(
        f"{system_image.sha256(path)}  {path.relative_to(medium)}\n" for path in files))
    system_image.read(medium, commit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("payload", "medium", "work"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    build(args.payload.resolve(), args.medium.resolve(), args.work.resolve(), args.commit)
