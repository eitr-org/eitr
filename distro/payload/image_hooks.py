"""Keep pacman's kernel and preset deployment while deferring initramfs generation."""
from contextlib import contextmanager

KERNEL_HOOK = "90-mkinitcpio-install.hook"
THEME_HOOK = "91-eitr-plymouth.hook"
KERNEL_SCRIPT = "/usr/share/libalpm/scripts/mkinitcpio"
KERNEL_COMMAND = f"Exec = {KERNEL_SCRIPT} install"
HOOK = f"usr/share/libalpm/hooks/{KERNEL_HOOK}"


@contextmanager
def deferred(root, hook, script):
    if (KERNEL_COMMAND not in hook.splitlines() or not script.startswith("#!/usr/bin/env bash\n")
            or not script.rstrip().endswith('    mkinitcpio "${args[@]}"\nfi')):
        raise ValueError("Review the mkinitcpio package hook before deferring boot image generation")
    directory = root / "etc/pacman.d/hooks"
    directory.mkdir(parents=True, exist_ok=True)
    env = "/etc/pacman.d/hooks/eitr-image-bash-env"
    overridden = []
    try:
        for path, contents in (
            (root / env.lstrip("/"), "mkinitcpio() { :; }\n"),
            (directory / KERNEL_HOOK,
             hook.replace(KERNEL_COMMAND, f"Exec = /usr/bin/env BASH_ENV={env} {KERNEL_SCRIPT} install").rstrip() + "\n"),
            (directory / THEME_HOOK, None),
        ):
            if contents is None:
                path.symlink_to("/dev/null")
                overridden.append(path)
            else:
                with path.open("x") as handle:
                    overridden.append(path)
                    handle.write(contents)
        yield
    finally:
        for path in reversed(overridden):
            path.unlink(missing_ok=True)
