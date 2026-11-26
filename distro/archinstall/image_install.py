"""Install a verified root using the reviewed archinstall disk and boot writers."""
from contextlib import contextmanager
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, distribution, distributions
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit

import eitr_profile
from eitr_i18n import tr
import image_hooks
import payload
import system_image

BACKEND_FILES = {
    "lib/boot.py": "22b1d8ece9d12fc302a1da58691705823483fc9fe474708e13b90ab7a0b0c71e",
    "lib/disk/device_handler.py": "db9c3e5ff0ad40c7213fd13a6a44f4dc8fd1d8d8267a4b2bb07f45122a433d2f",
    "lib/disk/filesystem.py": "9e7bdf8b952bf48dab23ba143706f1c0099c2f1a467200b2e0aee3a02c222950",
    "lib/disk/luks.py": "99a7def514d225ad04661ef5a43974b728a1bf0d1154f4ed9ffa4070426acdf5",
    "lib/installer.py": "8a891c129a4baf266f60c0fe9cbbcc38b22c4e895c6708b3fabef0aea7abdea3",
    "lib/models/device.py": "09bd46470956bf4d4b65b5a2d676474d86af6e0d6a6414248eb8085a34df5067",
    "lib/models/users.py": "9b9d75ea0636b1f8a48c749fd49dc68390f42221f8c61f2d3f5bfaecd0470f6f",
}
MEDIA = Path("/eitr-install-medium")
OFFLINE_CONF = Path("/etc/pacman.d/eitr-install.conf")
BOOT_FILES = "usr/lib/eitr/install-boot"


def reviewed_backend(site_packages=None):
    try:
        if site_packages is None:
            package = distribution("archinstall")
        else:
            package = next(distributions(name="archinstall", path=[str(site_packages)]))
        return package.version == "4.5" and all(
            sha256(package.locate_file(f"archinstall/{name}").read_bytes()).hexdigest() == digest
            for name, digest in BACKEND_FILES.items()
        )
    except (PackageNotFoundError, OSError, StopIteration):
        return False


def prepare(config, passphrase, target):
    from archinstall.lib.disk.filesystem import FilesystemHandler
    from archinstall.lib.installer import Installer
    from archinstall.lib.models.device import DiskLayoutConfiguration
    from archinstall.lib.models.users import Password

    layout = DiskLayoutConfiguration.parse_arg(
        config["disk_config"], Password(plaintext=passphrase) if passphrase else None)
    if layout is None or len(layout.device_modifications) != 1 or len(layout.device_modifications[0].partitions) != 2:
        raise OSError(tr("The installer could not load the selected disk layout"))
    filesystem = FilesystemHandler(layout)
    installer = Installer(target, layout, silent=True)
    filesystem.perform_filesystem_operations()
    installer.mount_ordered_layout()
    return installer


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def mounted(target):
    return subprocess.run(["findmnt", "-n", "-M", target], stdout=subprocess.DEVNULL).returncode == 0


@contextmanager
def target_mounts(target, encrypted, mapper=Path("/dev/mapper/root")):
    if mounted(target) or mounted(target / "boot"):
        raise OSError(tr("{TARGET} is already mounted; unmount it before installing", TARGET=str(target)))
    if encrypted and mapper.exists():
        raise OSError(tr("The root encryption mapping is already in use"))
    try:
        yield
    finally:
        if mounted(target):
            run(["umount", "-R", target])
        if encrypted and mapper.exists():
            run(["cryptsetup", "close", mapper.name])


def extract(target, medium, expected, run_step, output):
    if not all(mounted(target / name) for name in ("", "boot", "home", "var/log", "var/cache/pacman/pkg")):
        raise OSError(tr("The installed filesystems are incomplete"))
    threads = min(16, len(os.sched_getaffinity(0)))
    run_step(["unsquashfs", "-no-progress", "-strict-errors", "-xattrs", "-f",
              "-p", str(threads), "-d", str(target), str(medium / system_image.IMAGE)])
    actual = dict(line.split(maxsplit=1) for line in output(["pacman", "--root", str(target), "-Q"]).splitlines())
    explicit = output(["pacman", "--root", str(target), "-Qqe"]).splitlines()
    if actual != expected["packages"] or set(explicit) != set(expected["explicit"]):
        raise OSError(tr("The installed image package inventory does not match the ISO manifest"))
    boot_files = target / BOOT_FILES
    shutil.copytree(boot_files, target / "boot", dirs_exist_ok=True, copy_function=shutil.copyfile)
    shutil.rmtree(boot_files)


def configure(installer, config, username, password, encrypted, chroot):
    from archinstall.lib.models.locale import LocaleConfiguration
    from archinstall.lib.models.users import Password, User

    target = installer.target
    installer.genfstab()
    run(["systemd-firstboot", "--root", target, "--setup-machine-id"])
    installer.set_hostname(config["hostname"])
    if not installer.set_timezone(config["timezone"]):
        raise OSError(tr("The installer could not set the selected time zone"))
    locale = LocaleConfiguration.parse_arg(config["locale_config"])
    installer.set_vconsole(locale)
    installer.set_locale(locale)
    installer.set_keyboard_language(locale.kb_layout)
    user = User(username, Password(plaintext=password), True)
    installer.create_users(user)
    # Eitr's packaged rule is already present. Keep the first account rule
    # in the same place as when archinstall created it before the desktop.
    rules = target / "etc/sudoers.d"
    for rule in rules.glob(f"[0-9][0-9]_{username}"):
        rule.rename(rules / f"00_{username}")
    shadow = (target / "etc/shadow").read_text().splitlines()
    if not any(line.startswith(f"{username}:{user.password.enc_password}:") for line in shadow):
        raise OSError(tr("The installer could not set the account password"))
    if encrypted:
        path = target / "etc/mkinitcpio.conf"
        text = path.read_text()
        if text.count("block plymouth filesystems") != 1:
            raise OSError(tr("The system image has an unexpected initramfs configuration"))
        path.write_text(text.replace("block plymouth filesystems", "block plymouth encrypt filesystems"))
    chroot(["pacman-key", "--init"])
    keyrings = ["archlinux"]
    if (target / "usr/share/pacman/keyrings/eitr.gpg").is_file():
        keyrings.append("eitr")
    try:
        chroot(["pacman-key", "--populate", *keyrings])
    finally:
        chroot(["gpgconf", "--homedir", "/etc/pacman.d/gnupg", "--kill", "all"])


def install_limine(installer, removable, chroot):
    def confirm_installed(name):
        chroot(["pacman", "-Q", name])

    installer.pacman.strap = confirm_installed
    installer._zram_enabled = True
    installer._kernel_params.extend(("quiet", "splash"))
    installer._add_limine_bootloader(installer._get_boot_partition(), installer._get_efi_partition(),
                                    installer._get_root(), bootloader_removable=removable)
    seed = installer.target / "boot/loader/random-seed"
    if not seed.exists():
        seed.parent.mkdir(exist_ok=True)
        seed.write_bytes(os.urandom(32))


def firmware():
    from archinstall.lib.hardware import SysInfo

    return [name for name, required in zip(payload.AUDIO_FIRMWARE,
            (SysInfo.requires_sof_fw(), SysInfo.requires_alsa_fw()), strict=True) if required]


def package_hooks(target):
    return image_hooks.deferred(target, (target / image_hooks.HOOK).read_text(),
                                (target / image_hooks.KERNEL_SCRIPT.lstrip("/")).read_text())


@contextmanager
def offline_repository(target, medium):
    directory = target / MEDIA.relative_to("/")
    config = target / OFFLINE_CONF.relative_to("/")
    directory.mkdir()
    try:
        with config.open("x") as handle:
            handle.write(payload.pacman_conf(MEDIA / "pool", MEDIA / "repo"))
        try:
            run(["mount", "--bind", medium, directory])
            try:
                yield
            finally:
                run(["umount", directory])
        finally:
            config.unlink()
    finally:
        directory.rmdir()


def available(locations, medium):
    for location in locations.splitlines():
        url = urlsplit(location)
        path = Path(unquote(url.path))
        if url.scheme != "file" or path.parent not in (MEDIA / "pool", MEDIA / "repo"):
            return False
        if not (medium / path.relative_to(MEDIA)).is_file():
            return False
    return True


def install_packages(target, medium, packages, profile, desktop_dependencies, chroot, output):
    # Preserve --needed's treatment of preexisting base dependencies. Targets
    # brought in by the fixed desktop would have been explicit in the old
    # combined desktop and hardware transaction.
    explicit = sorted(set(packages) & set(desktop_dependencies))
    with offline_repository(target, medium):
        pacman = ["pacman", "--config", str(OFFLINE_CONF), "--noconfirm"]
        chroot([*pacman, "-Sy"])
        if profile:
            try:
                requested = list(dict.fromkeys([*packages, *profile]))
                locations = output([*pacman, "-Sp", "--needed", "--", *requested])
            except subprocess.CalledProcessError:
                pass
            else:
                if available(locations, medium):
                    packages = requested
        if packages:
            chroot([*pacman, "-S", "--needed", "--", *packages])
            if explicit:
                chroot(["pacman", "-D", "--asexplicit", "--", *explicit])


def preflight_profile(profile, drive, medium):
    with tempfile.TemporaryDirectory(prefix="eitr-profile-db-") as directory:
        db = Path(directory)
        databases = sorted(medium.rglob("*.db"))
        sync = db / "sync"
        sync.mkdir()
        for source in databases:
            (sync / source.name).symlink_to(source)
        conf = db / "pacman.conf"
        conf.write_text(payload.pacman_conf(medium / "pool", medium / "repo"))

        def metadata(command, **kwargs):
            if command[1] == "-Si":
                command = [command[0], "--config", conf, "--dbpath", db, *command[1:]]
            return subprocess.run(command, **kwargs)

        eitr_profile.preflight_packages(profile, drive, run=metadata, databases=databases)
