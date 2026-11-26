"""Build and verify the final boot image and preserve the initial boot palette."""
from pathlib import Path
import os
import re
import shutil


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


def finish_boot_image(target, encrypted, run, output):
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
