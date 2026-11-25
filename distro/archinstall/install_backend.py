"""Defer initramfs generation and batch packages for the reviewed archinstall."""
from contextlib import contextmanager
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, distribution
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

__archinstall__version__ = 4.5

BACKEND_FILES = {
    "lib/installer.py": "8a891c129a4baf266f60c0fe9cbbcc38b22c4e895c6708b3fabef0aea7abdea3",
    "lib/pacman/pacman.py": "ff31fb5948218cb6a720c587f0e85a65b91c8e85e3f295ee98494f026d6acd99",
    "lib/args.py": "f995582130db7fd21f9ebcbafe3eda192f29754ed336f8f61ca6e33a226e9ed5",
    "lib/plugins.py": "e0ee174755e4694e47a565485dc0806bb623ad013924b1fc66e663bea5d99b0f",
    "scripts/guided.py": "1e3b474d78e92eecba9e7dfa59e41aecca2f659be4cae6f1122fe81b57efc34a",
}
HOOK_DIR = "etc/pacman.d/hooks"
KERNEL_HOOK = "90-mkinitcpio-install.hook"
THEME_HOOK = "91-eitr-plymouth.hook"
HOOK_ENV = "eitr-install-defer-mkinitcpio.sh"
HOOK_SCRIPT = "/usr/share/libalpm/scripts/mkinitcpio"
HOOK_COMMAND = f"Exec = {HOOK_SCRIPT} install"
HOOK_OVERRIDE = f"Exec = /usr/bin/env BASH_ENV=/{HOOK_DIR}/{HOOK_ENV} {HOOK_SCRIPT} install"
DEFER_BUILD = "mkinitcpio() { :; }\n"


def reviewed_backend():
    try:
        package = distribution("archinstall")
        return package.version == "4.5" and all(
            sha256(package.locate_file(f"archinstall/{path}").read_bytes()).hexdigest() == digest
            for path, digest in BACKEND_FILES.items()
        )
    except (PackageNotFoundError, OSError):
        return False


def prepare_backend(pool, work):
    """Return a staged hook override when both the backend and payload are compatible."""
    if not reviewed_backend():
        return None
    packages = [path for path in pool.glob("mkinitcpio-*.pkg.tar.*")
                if path.suffix != ".sig" and path.name.removeprefix("mkinitcpio-")[0].isdigit()]
    if len(packages) != 1:
        return None
    try:
        hook, script = (
            subprocess.check_output(["bsdtar", "-xOf", packages[0], member], text=True)
            for member in (f"usr/share/libalpm/hooks/{KERNEL_HOOK}", HOOK_SCRIPT.lstrip("/"))
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    # Keep the upstream kernel copy and preset generation, including on kernel upgrades.
    if (HOOK_COMMAND not in hook.splitlines() or not script.startswith("#!/usr/bin/env bash\n")
            or not script.endswith('    mkinitcpio "${args[@]}"\nfi\n')):
        return None
    override = work / KERNEL_HOOK
    override.write_text(hook.replace(HOOK_COMMAND, HOOK_OVERRIDE))
    return override


def install_overrides(target, override, owned):
    directory = target / HOOK_DIR
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in ((HOOK_ENV, DEFER_BUILD), (KERNEL_HOOK, override.read_text()), (THEME_HOOK, None)):
        path = directory / name
        if content is None:
            path.symlink_to("/dev/null")
            (owned / name).touch()
        else:
            with path.open("x") as handle:
                (owned / name).touch()
                handle.write(content)


def remove_overrides(target, owned):
    # The marker lives on the live ISO and records only files this run created.
    for marker in owned.iterdir():
        (target / HOOK_DIR / marker.name).unlink(missing_ok=True)
        marker.unlink()


@contextmanager
def deferred_hooks(target, pool, work, pacman_conf=Path("/etc/pacman.conf")):
    from eitr_i18n import tr

    owned = work / "overrides"
    owned.mkdir()
    if prepare_backend(pool, work) is None:
        print(tr("Using standard archinstall package transactions and initramfs hooks"), flush=True)
        yield False
        return

    original = pacman_conf.read_text()
    try:
        pacman_conf.write_text(original.replace("[options]\n", f"[options]\nHookDir = {target / HOOK_DIR}\n", 1))
        yield True
    finally:
        try:
            remove_overrides(target, owned)
        finally:
            pacman_conf.write_text(original)


def adapt_backend(installer_class, pacman_class, features, override, owned):
    strap = pacman_class.strap
    arch_chroot = installer_class.arch_chroot
    batched = set()

    def strap_packages(pacman, packages):
        requested = [packages] if isinstance(packages, str) else packages
        if not batched and requested == ["zram-generator"]:
            strap(pacman, features)
            batched.update(features)
        elif not set(requested).issubset(batched):
            if not (owned / KERNEL_HOOK).exists():
                install_overrides(pacman.target, override, owned)
            strap(pacman, packages)

    def defer_build(installer, cmd, run_as=None, peek_output=False):
        if cmd == "mkinitcpio -P":
            return None
        return arch_chroot(installer, cmd, run_as=run_as, peek_output=peek_output)

    pacman_class.strap = strap_packages
    installer_class.arch_chroot = defer_build


class Plugin:
    """Loaded by archinstall's local --plugin option in its own process."""

    def __init__(self):
        from archinstall.applications.audio import AudioApp
        from archinstall.applications.bluetooth import BluetoothApp
        from archinstall.lib.hardware import SysInfo
        from archinstall.lib.installer import Installer
        from archinstall.lib.pacman.pacman import Pacman

        work = Path(os.environ["EITR_INSTALL_WORK"])
        config = json.loads((work / "user_configuration.json").read_text())
        features = ["zram-generator", "plymouth", "limine", "efibootmgr", *BluetoothApp().packages,
                    *(["sof-firmware"] if SysInfo.requires_sof_fw() else []),
                    *(["alsa-firmware"] if SysInfo.requires_alsa_fw() else []),
                    *AudioApp().pipewire_packages, *config["packages"]]
        adapt_backend(Installer, Pacman, list(dict.fromkeys(features)), work / KERNEL_HOOK, work / "overrides")


PRESET_IMAGES = """
shopt -s nullglob
presets=(/etc/mkinitcpio.d/*.preset)
(( ${#presets[@]} )) || exit 1
for preset in "${presets[@]}"; do
    (
        source "$preset"
        (( ${#PRESETS[@]} )) || exit 1
        for name in "${PRESETS[@]}"; do
            image="${name}_image"
            path="${!image:-${ALL_image:-}}"
            [[ "$path" == /* && -s "$path" ]] || exit 1
            printf '%s\\n' "$path"
        done
    ) || exit 1
done
"""


def build_initramfs(encrypted, run, output):
    from eitr_i18n import tr

    run(["plymouth-set-default-theme", "eitr"])
    run(["mkinitcpio", "-P"])
    images = output(["bash", "-c", PRESET_IMAGES]).splitlines()
    if not images:
        raise OSError(tr("No boot image was found for the installed kernels"))
    for image in images:
        contents = {name.removeprefix("./") for name in output(["lsinitcpio", "-l", image]).splitlines()}
        config = output(["lsinitcpio", "-c", image])
        hooks = re.findall(r"^HOOKS=\((.*?)\)", config, re.MULTILINE)
        enabled = set(hooks[-1].split()) if hooks else set()
        splash = (("plymouth" in enabled and "hooks/plymouth" in contents)
                  or ("sd-plymouth" in enabled and "usr/lib/systemd/system/plymouth-start.service" in contents))
        if not splash or "usr/share/plymouth/themes/eitr/eitr.plymouth" not in contents:
            raise OSError(tr("Boot image {image} is missing the Plymouth hook or Eitr theme", image=image))
        unlock = (("encrypt" in enabled and "hooks/encrypt" in contents)
                  or ("sd-encrypt" in enabled
                      and "usr/lib/systemd/system-generators/systemd-cryptsetup-generator" in contents))
        if encrypted and not unlock:
            raise OSError(tr("Boot image {image} is missing the encrypted root hook", image=image))


def finish_boot_image(target, work, encrypted, run, output):
    remove_overrides(target, work / "overrides")
    build_initramfs(encrypted, run, lambda command: output(["arch-chroot", str(target), *command]))


def save_boot_palette(target, user, directory):
    """Keep the palette the boot menu used before profile preferences were applied."""
    palette = Path(user["home"]) / ".config/theme/current/colors.toml"
    source = target / palette.relative_to("/")
    if not source.is_file() or source.is_symlink():
        return
    path = directory / "colors.toml"
    shutil.copyfile(source, path)
    os.chown(path, user["uid"], user["gid"])


def boot_style_command(target, user, directory):
    command = ["/usr/lib/eitr/eitr-system", "boot-menu-style", user["name"]]
    saved = directory / "colors.toml"
    if not saved.is_file():
        return command
    palette = Path(user["home"]) / ".config/theme/current/colors.toml"
    # The style service still follows this user's theme after first boot. The
    # private mount only supplies the pre-profile palette for the initial menu.
    return ["unshare", "--mount", "--propagation", "private", "bash", "-ec",
            'mount --bind "$1" "$2"; shift 2; exec "$@"', "eitr-boot-style",
            "/" + str(saved.relative_to(target)), str(palette), *command]
