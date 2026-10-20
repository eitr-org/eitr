#!/usr/bin/python3 -I
"""Root-owned, narrow Eitr snapshot/authentication operations; never run at login."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eitr_bootstrap
from eitr_i18n import tr
import argparse
import datetime
import io
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import subprocess
import sys
import tempfile

STATE = Path("/var/lib/eitr")
PAM = Path("/etc/pam.d")
SERVICES = ("hyprlock", "sddm", "sudo")
MARKER = " # eitr-managed-auth"
U2F_KEYS = Path("/etc/security/eitr/u2f_keys")
BOOT_ARCHIVE_LIMIT = 10
BOOT_GUARD = Path("/usr/lib/eitr/eitr-boot-guard")
FIREWALL_UNIT = "eitr-firewall.service"
FIREWALL_RULES = Path("/usr/share/eitr/firewall.nft")
FIREWALL_OPENINGS = Path("/etc/eitr/firewall.d")
SSH_OPENING = "add rule inet eitr_firewall input tcp dport 22 accept\n"
SYSTEM_BUS = "/run/dbus/system_bus_socket"


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def output(args):
    return subprocess.check_output(args, text=True).strip()


def atomic(path, content, mode=0o600, directory_mode=0o700):
    path.parent.mkdir(parents=True, exist_ok=True, mode=directory_mode)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".eitr-")
    try:
        with os.fdopen(fd, "w") as file:
            file.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def mount_source(path):
    return output(["findmnt", "-n", "-o", "SOURCE", "-T", path])


def snapshot_supported():
    if output(["findmnt", "-n", "-o", "FSTYPE", "/"]) != "btrfs":
        raise RuntimeError(tr('Snapshot-protected updates require a Btrfs root. No update was started.'))
    source = mount_source("/")
    for path in ("/usr", "/etc", "/var/lib/pacman"):
        if mount_source(path) != source:
            raise RuntimeError(tr('{path} is outside the root snapshot. Configure a coordinated snapshot backend first.', path=f'{path}'))


def in_chroot():
    return subprocess.run(["systemd-detect-virt", "--quiet", "--chroot"]).returncode == 0


def snapper_root():
    """Snapper for the root config. In the installer's chroot, which can see the
    live system's bus but no snapperd, it works on the files directly."""
    if Path(SYSTEM_BUS).exists() and not in_chroot():
        return ["snapper", "-c", "root"]
    return ["snapper", "--no-dbus", "-c", "root"]


def setup_snapshots():
    snapshot_supported()
    snapper = snapper_root()
    result = subprocess.run([*snapper, "get-config"], capture_output=True)
    if result.returncode:
        run([*snapper, "create-config", "/"])
        run([*snapper, "set-config", "NUMBER_CLEANUP=yes",
             "NUMBER_LIMIT=10", "NUMBER_LIMIT_IMPORTANT=5", "TIMELINE_CREATE=no"])
    run(["systemctl", "enable", "snapper-cleanup.timer"])
    print(tr('Root snapshots configured. Existing Snapper policy is preserved.'))


def is_mountpoint(path):
    return subprocess.run(["findmnt", "-n", "-M", path], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0


def separate_boot_mounts():
    # /boot inside the Btrfs root is already covered by the root snapshot.
    return [mount for mount in ("/boot", "/efi") if Path(mount).is_dir() and is_mountpoint(mount)]


def prune_boot_archives(keep=BOOT_ARCHIVE_LIMIT):
    """Keep only the newest numbered boot archives, like Snapper's number cleanup."""
    root = STATE / "boot-backups"
    if not root.is_dir():
        return
    archives = sorted((path for path in root.iterdir() if path.is_dir() and path.name.isdigit()),
                      key=lambda path: int(path.name))
    for path in archives[:-keep] if keep else archives:
        shutil.rmtree(path)


def snapshot_pre():
    snapshot_supported()
    run(["snapper", "-c", "root", "get-config"], stdout=subprocess.DEVNULL)
    if (STATE / "pending-upgrade.json").exists():
        # A previous update was interrupted before its post snapshot; pair it
        # now so the old pre snapshot is not left orphaned.
        print(tr('Closing the recovery point of an interrupted earlier update.'))
        snapshot_post("interrupted")
    # Snapshots never carry an armed boot guard; this update arms it again once it succeeds.
    (STATE / "boot-guard.json").unlink(missing_ok=True)
    root = STATE / "boot-backups"
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    # Archive boot files before creating the snapshot so a failure here never
    # leaves a pre snapshot without a pending record.
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=root))
    try:
        mounts = separate_boot_mounts()
        for mount in mounts:
            run(["tar", "-C", mount, "-cpf", str(staging / (mount[1:] + ".tar")), "."])
        identifier = output(["snapper", "-c", "root", "create", "--type", "pre", "--print-number",
                             "--description", "Eitr before package upgrade", "--cleanup-algorithm", "number"])
        if not identifier.isdigit():
            raise RuntimeError(tr('Snapper returned an invalid snapshot number'))
        archive = ""
        if mounts:
            target = root / identifier
            if target.exists():
                shutil.rmtree(target)  # Left over from a deleted snapshot with the same number.
            staging.rename(target)
            archive = str(target)
        atomic(STATE / "pending-upgrade.json", json.dumps({"snapshot": identifier, "boot": archive}) + "\n")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    prune_boot_archives()
    extra = " and boot archives" if mounts else ""
    print(tr('Recovery snapshot {identifier}{extra} created.', identifier=f'{identifier}', extra=f'{extra}'))


POST_DESCRIPTIONS = {
    "success": "Eitr after package upgrade",
    "failed": "Eitr after failed package upgrade",
    "interrupted": "Eitr after interrupted package upgrade",
}


def snapshot_post(outcome="success"):
    path = STATE / "pending-upgrade.json"
    if not path.exists():
        return
    pending = json.loads(path.read_text())
    identifier = str(pending["snapshot"])
    if not identifier.isdigit():
        raise RuntimeError('Invalid pending snapshot')
    run(["snapper", "-c", "root", "create", "--type", "post", "--pre-number", identifier,
         "--description", POST_DESCRIPTIONS[outcome], "--cleanup-algorithm", "number"])
    path.unlink()
    # A successful update arms the boot guard with its "before" snapshot and boot files.
    if outcome == "success" and BOOT_GUARD.is_file():
        subprocess.run([str(BOOT_GUARD), "arm", identifier, pending.get("boot", "")], check=False)


# Bootable snapshots. Detection only reads files under SYSTEM_ROOT, so tests
# can point it at a fake tree. ESP contents may need root to read (vfat masks).
SYSTEM_ROOT = Path("/")
ESP_CANDIDATES = ("efi", "boot", "boot/efi")
GRUB_CONFIG = "boot/grub/grub.cfg"
LIMINE_CONFIGS = ("limine.conf", "limine/limine.conf", "EFI/limine/limine.conf", "EFI/BOOT/limine.conf",
                  "EFI/arch-limine/limine.conf")
BOOT_INTEGRATIONS = {
    # Files and commands supplied by distro/bootloader/<name>[-aur].txt packages.
    "grub": {"unit": "grub-btrfsd.service", "files": ("etc/grub.d/41_snapshots-btrfs",),
             "commands": ("inotifywait", "grub-mkconfig")},
    "limine": {"unit": "limine-snapper-sync.service",
               "files": ("usr/lib/systemd/system/limine-snapper-sync.service",),
               "commands": ("limine-snapper-sync", "limine-update")},
}
UNSUPPORTED_BOOT = {
    "systemd-boot": "systemd-boot only loads kernels from the EFI/XBOOTLDR partition and cannot boot "
                    "Btrfs snapshots. Use the live-media recovery in RECOVERY.md instead.",
    "unknown": "No GRUB, Limine or systemd-boot configuration was found (run as root so the EFI "
               "partition is readable).",
}


def bootloader_evidence(root=None):
    """Return {loader: [paths]} for every boot loader configuration found."""
    root = Path(root or SYSTEM_ROOT)
    evidence = {}

    def found(loader, path):
        evidence.setdefault(loader, []).append("/" + str(path.relative_to(root)))

    if (root / GRUB_CONFIG).is_file():
        found("grub", root / GRUB_CONFIG)
    for directory in ESP_CANDIDATES:
        for name in LIMINE_CONFIGS:
            if (root / directory / name).is_file():
                found("limine", root / directory / name)
    for esp in ESP_CANDIDATES:
        efi = root / esp / "EFI"
        if (root / esp / "loader/loader.conf").is_file():
            found("systemd-boot", root / esp / "loader/loader.conf")
        elif (efi / "systemd").is_dir() and any((efi / "systemd").glob("systemd-boot*.efi")):
            found("systemd-boot", next((efi / "systemd").glob("systemd-boot*.efi")))
        if efi.is_dir() and "grub" not in evidence:
            for image in sorted(efi.glob("*/grub*.efi")):
                found("grub", image)
                break
    return evidence


def detect_bootloader(root=None):
    """Return (name, evidence); name is grub, limine, systemd-boot, unknown or ambiguous."""
    evidence = bootloader_evidence(root)
    if not evidence:
        return "unknown", evidence
    if len(evidence) > 1:
        return "ambiguous", evidence
    return next(iter(evidence)), evidence


def boot_integration_missing(loader, root=None):
    root = Path(root or SYSTEM_ROOT)
    spec = BOOT_INTEGRATIONS[loader]
    missing = ["/" + name for name in spec["files"] if not (root / name).is_file()]
    return missing + [name for name in spec["commands"] if not shutil.which(name)]


def unit_enabled(unit):
    return subprocess.run(["systemctl", "is-enabled", "--quiet", unit],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def supported_bootloader():
    loader, evidence = detect_bootloader()
    if loader == "ambiguous":
        listing = "; ".join(f"{name}: {', '.join(paths)}" for name, paths in evidence.items())
        raise RuntimeError(tr('Several boot loaders are configured ({listing}). Remove stale loader files or configure snapshot boot entries manually. Nothing was changed.', listing=f'{listing}'))
    if loader not in BOOT_INTEGRATIONS:
        raise RuntimeError(tr('Bootable snapshots are not supported with {loader}. {reason} Nothing was changed.', loader=f'{loader}', reason=f'{UNSUPPORTED_BOOT[loader]}'))
    return loader, evidence


def boot_snapshot_status():
    loader, evidence = detect_bootloader()
    print(tr('Boot loader: {loader}', loader=f'{loader}'))
    for name, paths in evidence.items():
        print(f"  {name}: {', '.join(paths)}")
    if loader == "ambiguous":
        print(tr('Snapshot boot entries: unsupported until only one boot loader remains configured.'))
        return 1
    if loader not in BOOT_INTEGRATIONS:
        print(tr('Snapshot boot entries: unsupported. {reason}', reason=f'{UNSUPPORTED_BOOT[loader]}'))
        return 1
    missing = boot_integration_missing(loader)
    if missing:
        print(tr('Snapshot boot entries: not installed (missing {missing_files}).', missing_files=f"{', '.join(missing)}"))
        print(tr('Install them and enable snapshot entries with: bash distro/bootloader/setup.sh'))
        return 1
    unit = BOOT_INTEGRATIONS[loader]["unit"]
    if not unit_enabled(unit):
        print(tr('Snapshot boot entries: installed, but {unit} is not enabled.', unit=f'{unit}'))
        return 1
    print(tr('Snapshot boot entries: enabled through {unit}.', unit=f'{unit}'))
    return 0


def backup_boot_config(path):
    target = STATE / "boot-config-backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    target.mkdir(parents=True, mode=0o700)
    shutil.copy2(path, target / path.name)
    return target / path.name


def setup_boot_snapshots():
    """Add snapshot boot entries for GRUB or Limine; refuse everything else."""
    snapshot_supported()
    run(["snapper", "-c", "root", "get-config"], stdout=subprocess.DEVNULL)
    loader, evidence = supported_bootloader()
    missing = boot_integration_missing(loader)
    if missing:
        raise RuntimeError(tr('Missing {missing_files}. Install the {loader} packages listed in distro/bootloader/ first. Nothing was changed.', missing_files=f"{', '.join(missing)}", loader=f'{loader}'))
    unit = BOOT_INTEGRATIONS[loader]["unit"]
    if loader == "grub":
        config = SYSTEM_ROOT / GRUB_CONFIG
        backup = backup_boot_config(config)
        # grub-mkconfig validates a .new file before replacing grub.cfg.
        run(["grub-mkconfig", "-o", "/" + GRUB_CONFIG])
        run(["systemctl", "enable", unit])
        print(tr("GRUB now lists Snapper snapshots in its 'Arch Linux snapshots' submenu. Backup: {backup}", backup=f'{backup}'))
        if separate_boot_mounts():
            print(tr('/boot is a separate partition: snapshot entries boot the current kernel. After a kernel update, restore the matching boot archive as RECOVERY.md describes.'))
    else:
        config = SYSTEM_ROOT / evidence["limine"][0].lstrip("/")
        backup = backup_boot_config(config)
        run(["systemctl", "enable", unit])
        print(tr('{unit} is enabled; snapshot entries are written to {entries_path} from the next boot.', unit=f'{unit}', entries_path=f"{evidence['limine'][0]}"))
        print(tr('Review /etc/default/limine first, then run: sudo systemctl start {unit}', unit=f'{unit}'))
        print(tr('Backup of the current Limine menu: {backup}', backup=f'{backup}'))
    print(tr('Snapshot entries boot read-only; see RECOVERY.md before relying on them.'))


# Laptop battery charge limit. Only batteries whose firmware driver exposes
# charge_control_end_threshold are supported; desktops have none.
POWER_SUPPLY = Path("/sys/class/power_supply")
BATTERY_LIMIT_CONFIG = Path("/etc/eitr/battery-limit")
SYSTEMD_SYSTEM = Path("/etc/systemd/system")
BATTERY_UNIT = "eitr-battery-limit.service"
# The eitr-desktop package installs the helper in /usr/lib; older manual installs
# used /usr/local/lib. Generated units call whichever root-owned copy is running.
HELPER_PATHS = ("/usr/lib/eitr/eitr-system", "/usr/local/lib/eitr/eitr-system")
INSTALLED_HELPER = next((path for path in HELPER_PATHS if Path(path).is_file()), HELPER_PATHS[0])
SLEEP_TARGETS = "suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target"
BATTERY_UNIT_CONTENT = f"""[Unit]
Description=Apply the Eitr battery charge limit
After={SLEEP_TARGETS}

[Service]
Type=oneshot
ExecStart={INSTALLED_HELPER} battery-limit-apply

[Install]
# Some firmware resets the threshold on resume, so it is applied again then.
WantedBy=multi-user.target {SLEEP_TARGETS}
"""


def limit_batteries():
    batteries = []
    for battery in sorted(POWER_SUPPLY.glob("BAT*")):
        try:
            kind = (battery / "type").read_text().strip()
        except OSError:
            continue
        if kind == "Battery" and (battery / "charge_control_end_threshold").is_file():
            batteries.append(battery)
    return batteries


def parse_battery_limit(value):
    """Return the end threshold for 60-100, or None for off."""
    if value == "off":
        return None
    if not value or not value.isdigit() or not 60 <= int(value) <= 100:
        raise ValueError(tr('Battery limit must be a whole number from 60 to 100, or off'))
    return int(value)


def write_battery_thresholds(limit, batteries):
    # Validate every battery before writing any, so a refusal changes nothing.
    for battery in batteries:
        start = battery / "charge_control_start_threshold"
        if limit < 100 and start.is_file() and int(start.read_text()) >= limit:
            raise RuntimeError(tr('{name} starts charging at {charge_percent}%; choose a limit above that. Nothing was changed.', name=f'{battery.name}', charge_percent=f'{start.read_text().strip()}'))
    for battery in batteries:
        (battery / "charge_control_end_threshold").write_text(f"{limit}\n")


def battery_limit(value):
    limit = parse_battery_limit(value)
    batteries = limit_batteries()
    if not batteries:
        raise RuntimeError(tr('No battery with a firmware charge limit (charge_control_end_threshold) was found.'))
    unit = SYSTEMD_SYSTEM / BATTERY_UNIT
    if limit is None:
        write_battery_thresholds(100, batteries)
        if unit.exists():
            run(["systemctl", "disable", BATTERY_UNIT])
            unit.unlink()
            run(["systemctl", "daemon-reload"])
        BATTERY_LIMIT_CONFIG.unlink(missing_ok=True)
        print(tr('Battery charge limit removed; batteries charge to 100%.'))
        return
    write_battery_thresholds(limit, batteries)
    atomic(BATTERY_LIMIT_CONFIG, f"{limit}\n", mode=0o644, directory_mode=0o755)
    atomic(unit, BATTERY_UNIT_CONTENT, mode=0o644, directory_mode=0o755)
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", BATTERY_UNIT])
    names = ", ".join(battery.name for battery in batteries)
    print(tr('{names} now stop charging at {limit}%. The limit is restored at boot and after resume.', names=f'{names}', limit=f'{limit}'))
    print(tr('Undo with: sudo {INSTALLED_HELPER} battery-limit off', INSTALLED_HELPER=f'{INSTALLED_HELPER}'))


def battery_limit_apply():
    if not BATTERY_LIMIT_CONFIG.is_file():
        return
    limit = parse_battery_limit(BATTERY_LIMIT_CONFIG.read_text().strip())
    batteries = limit_batteries()
    if limit is not None and batteries:
        write_battery_thresholds(limit, batteries)


def battery_limit_status():
    batteries = limit_batteries()
    if not batteries:
        print(tr('No battery charge limit control on this machine.'))
        return 1
    for battery in batteries:
        print(tr('{name}: stops charging at {charge_percent}%', name=f'{battery.name}', charge_percent=f"{(battery / 'charge_control_end_threshold').read_text().strip()}"))
    saved = BATTERY_LIMIT_CONFIG.read_text().strip() if BATTERY_LIMIT_CONFIG.is_file() else "none"
    print(tr('Saved limit: {saved}', saved=f'{saved}'))
    return 0


# TPM2 unlock for LUKS2. Every operation keeps the existing passphrase slot;
# nothing here runs from the installer.
MKINITCPIO_CONFIGS = (Path("/etc/mkinitcpio.conf"), Path("/etc/mkinitcpio.conf.d"))
TPM_PCRS = "7"
KEEP_SLOT_TYPES = {"password", "recovery"}


def is_block_device(path):
    return stat.S_ISBLK(os.stat(path).st_mode)


def luks2_device(device):
    if not device or not device.startswith("/dev/"):
        raise ValueError(tr('Give the encrypted partition as a /dev path, for example /dev/nvme0n1p2'))
    if not is_block_device(device):
        raise RuntimeError(tr('{device} is not a block device', device=f'{device}'))
    if subprocess.run(["cryptsetup", "isLuks", "--type", "luks2", device]).returncode:
        raise RuntimeError(tr('{device} is not a LUKS2 volume. TPM unlock needs LUKS2.', device=f'{device}'))
    return device


def enrolled_slot_types(device):
    """Parse `systemd-cryptenroll DEVICE`: a SLOT TYPE header, then one slot per line."""
    lines = output(["systemd-cryptenroll", device]).splitlines()[1:]
    return [line.split()[1] for line in lines if len(line.split()) >= 2]


def tpm2_devices():
    result = subprocess.run(["systemd-cryptenroll", "--tpm2-device=list"], capture_output=True, text=True)
    if result.returncode:
        return []
    return [line.split()[0] for line in result.stdout.splitlines() if line.startswith("/dev/")]


def initramfs_hooks():
    """Return the effective mkinitcpio HOOKS list, or None without mkinitcpio."""
    main, drop_ins = MKINITCPIO_CONFIGS
    files = ([main] if main.is_file() else []) + (sorted(drop_ins.glob("*.conf")) if drop_ins.is_dir() else [])
    hooks = None
    for path in files:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith("HOOKS=(") and line.endswith(")"):
                hooks = line[len("HOOKS=("):-1].split()
    return hooks


def luks_tpm_check(device):
    luks2_device(device)
    slots = enrolled_slot_types(device)
    devices = tpm2_devices()
    hooks = initramfs_hooks()
    print(tr('{device}: LUKS2, enrolled slots: {slot_names}', device=f'{device}', slot_names=f"{', '.join(slots) or 'none'}"))
    print(tr('TPM2 devices: {devices}', devices=f"{', '.join(devices) or 'none found'}"))
    if hooks is None:
        print(tr('Initramfs: mkinitcpio not found; make sure your initramfs unlocks with systemd-cryptsetup.'))
    elif "sd-encrypt" in hooks:
        print(tr('Initramfs: systemd sd-encrypt hook present; it tries the TPM2 token at boot.'))
    else:
        print(tr("Initramfs: the busybox 'encrypt' hook cannot use TPM2 tokens. Switch to the systemd and sd-encrypt hooks first (see RECOVERY.md, TPM disk unlock)."))
    print(tr('PCR policy: {TPM_PCRS} (Secure Boot state). Firmware or Secure Boot key changes require the passphrase once, then re-enrollment.', TPM_PCRS=f'{TPM_PCRS}'))
    return slots, devices, hooks


def luks_tpm_enroll(device):
    slots, devices, hooks = luks_tpm_check(device)
    if not devices:
        raise RuntimeError(tr('No TPM2 device found. Nothing was changed.'))
    if hooks is not None and "sd-encrypt" not in hooks:
        raise RuntimeError(tr('The initramfs cannot use TPM2 unlock yet. Nothing was changed.'))
    if "tpm2" in slots:
        raise RuntimeError(tr('{device} already has a TPM2 slot. Remove it first to re-enroll.', device=f'{device}'))
    if not KEEP_SLOT_TYPES & set(slots):
        raise RuntimeError(tr('No passphrase or recovery key slot found; refusing to rely on the TPM alone.'))
    # Adds a slot; existing passphrase and recovery slots are left untouched.
    run(["systemd-cryptenroll", "--tpm2-device=auto", f"--tpm2-pcrs={TPM_PCRS}", device])
    print(tr('TPM2 unlock enrolled for {device} with PCR {TPM_PCRS}. Your passphrase still works.', device=f'{device}', TPM_PCRS=f'{TPM_PCRS}'))
    print(tr('Undo with: sudo {INSTALLED_HELPER} luks-tpm-remove {device}', INSTALLED_HELPER=f'{INSTALLED_HELPER}', device=f'{device}'))


def luks_recovery_key(device):
    luks2_device(device)
    # The key is printed to this terminal only; it is never written to disk.
    run(["systemd-cryptenroll", "--recovery-key", device])


def luks_tpm_remove(device):
    luks2_device(device)
    slots = enrolled_slot_types(device)
    if "tpm2" not in slots:
        print(tr('{device} has no TPM2 slot.', device=f'{device}'))
        return
    if not KEEP_SLOT_TYPES & set(slots):
        raise RuntimeError(tr('No passphrase or recovery key slot remains; add one before removing TPM2 unlock.'))
    run(["systemd-cryptenroll", "--wipe-slot=tpm2", device])
    print(tr('TPM2 unlock removed from {device}; the passphrase is required at boot again.', device=f'{device}'))


def pam_with_method(content, method):
    remaining = [line for line in content.splitlines() if not line.endswith(MARKER)]
    modules = {
        "fingerprint": "auth sufficient pam_fprintd.so timeout=10 max-tries=1",
        "fido2": "auth sufficient pam_u2f.so authfile=/etc/security/eitr/u2f_keys origin=pam://eitr appid=pam://eitr cue userpresence=1",
    }
    if method == "password":
        return "\n".join(remaining) + "\n"
    # Preserve the original password/account/session stack; never replace it.
    return modules[method] + MARKER + "\n" + "\n".join(remaining) + "\n"


def write_u2f_keys(user, content):
    current = U2F_KEYS.read_text().splitlines() if U2F_KEYS.exists() else []
    current = [line for line in current if not line.startswith(user + ":")]
    # hyprlock runs PAM as the desktop user, so pam_u2f must be able to read
    # the authfile. It holds only public key handles, never secrets.
    atomic(U2F_KEYS, "\n".join([*current, content.strip()]) + "\n", mode=0o644, directory_mode=0o755)
    os.chmod(U2F_KEYS.parent, 0o755)


def read_user_u2f_keys(user, account):
    source = Path(account.pw_dir) / ".config/Yubico/u2f_keys"
    # Do not let a root helper follow an arbitrary user symlink.
    descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor) as registration:
        metadata = os.fstat(registration.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != account.pw_uid or metadata.st_size > 65536:
            raise RuntimeError(tr('FIDO2 registration must be a regular file owned by the desktop user'))
        content = registration.read(65537)
    if not content.startswith(user + ":") or "\n" in content.rstrip("\n"):
        raise RuntimeError(tr('Invalid FIDO2 registration'))
    return content


def check_pam_files():
    for service in SERVICES:
        path = PAM / service
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(tr('Unsupported PAM file: {path}', path=f'{path}'))


def restore_pam(backup, services=SERVICES):
    for service in services:
        source = backup / service
        if source.is_file():
            atomic(PAM / service, source.read_text(), mode=0o644, directory_mode=0o755)


def write_pam(method):
    """Rewrite each PAM file, restoring all of them if any write fails."""
    check_pam_files()
    backup = STATE / "pam-backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True, mode=0o700)
    for service in SERVICES:
        shutil.copy2(PAM / service, backup / service)
    enabled = SERVICES
    written = []
    try:
        for service in SERVICES:
            path = PAM / service
            written.append(service)
            atomic(path, pam_with_method(path.read_text(), method if service in enabled else "password"), mode=0o644)
    except BaseException:
        restore_pam(backup, written)
        raise
    return backup, enabled


def enable_auth(method):
    user = os.environ.get("SUDO_USER", "")
    if not user or user == "root":
        raise RuntimeError(tr('Use sudo from your normal desktop user'))
    account = pwd.getpwnam(user)
    if method == "fingerprint":
        run(["fprintd-list", user])
    elif method == "fido2":
        write_u2f_keys(user, read_user_u2f_keys(user, account))
    backup, enabled = write_pam(method)
    print(tr('Authentication updated for {authentication_methods}. Password fallback retained. Backup: {backup}', authentication_methods=f"{', '.join(enabled)}", backup=f'{backup}'))
    print(tr('Undo with: sudo {helper} auth-restore {name}', helper=f'{sys.argv[0]}', name=f'{backup.name}'))


def restore_auth(name):
    root = (STATE / "pam-backups").resolve()
    backup = (root / name).resolve()
    if backup.parent != root or not backup.is_dir():
        raise RuntimeError(tr('No PAM backup named {name} in {root}', name=f'{name!r}', root=f'{root}'))
    missing = [service for service in SERVICES if not (backup / service).is_file()]
    if missing:
        raise RuntimeError(tr('Backup {name} is incomplete: missing {missing_files}', name=f'{name}', missing_files=f"{', '.join(missing)}"))
    check_pam_files()
    restore_pam(backup)
    print(tr('Restored {service_names} PAM files from {backup}', service_names=f"{', '.join(SERVICES)}", backup=f'{backup}'))


CODE_ROOT = Path("/usr/share/eitr")
# The theme a new user starts with (distro/user-defaults.json); used when no desktop theme can be read.
DEFAULT_THEME = "afterglow"
BOOT_MENU_STATE = STATE / "boot-menu-style.json"
BOOT_MENU_UNIT = "eitr-boot-menu.service"
STYLE_BEGIN, STYLE_END = "# BEGIN EITR BOOT MENU STYLE", "# END EITR BOOT MENU STYLE"
# The firmware's SecureBoot variable: four attribute bytes, then 1 when enabled.
SECURE_BOOT_VARIABLE = Path("/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c")
HEX_COLOR = re.compile(r'^\s*([a-z0-9_]+)\s*=\s*"#([0-9a-fA-F]{6})"\s*$')


def theme_palette(text):
    """The theme's colours as {key: "rrggbb"}; only plain hex colour lines are read."""
    palette = {}
    for line in text.splitlines():
        match = HEX_COLOR.match(line)
        if match:
            palette[match[1]] = match[2].lower()
    required = ("background", "foreground", "accent", *(f"color{index}" for index in range(16)))
    missing = [key for key in required if key not in palette]
    if missing:
        raise ValueError(tr('theme colours missing: {colors}', colors=', '.join(missing)))
    return palette


def read_user_theme(user):
    """The desktop user's current theme colours, read without following their symlinks."""
    account = pwd.getpwnam(user)
    source = Path(account.pw_dir) / ".config/theme/current/colors.toml"
    descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor) as colors:
        metadata = os.fstat(colors.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != account.pw_uid or metadata.st_size > 65536:
            raise ValueError(tr('the theme colours must be a small regular file owned by the desktop user'))
        return theme_palette(colors.read(65537))


def boot_menu_palette(user):
    """The user's theme colours, else the default theme's; returns (palette, source description)."""
    if user:
        try:
            return read_user_theme(user), f"{user}'s theme"
        except (OSError, KeyError, ValueError, UnicodeDecodeError) as error:
            print(tr("Using the default theme: {user}'s theme could not be read ({error}).", user=f'{user}', error=f'{error}'))
    return theme_palette((CODE_ROOT / "themes" / DEFAULT_THEME / "colors.toml").read_text()), "the default theme"


def mix(first, second, amount):
    """Blend two rrggbb colours; amount 0 is first, 1 is second."""
    channels = [round(int(first[index:index + 2], 16) * (1 - amount) + int(second[index:index + 2], 16) * amount)
                for index in (0, 2, 4)]
    return "".join(f"{channel:02x}" for channel in channels)


def limine_style_block(palette, wallpaper):
    background, foreground = palette["background"], palette["foreground"]
    highlight = palette.get("selection_background") or mix(background, palette["accent"], 0.22)
    lines = [
        STYLE_BEGIN,
        "interface_branding: E I T R",
        f"interface_branding_colour: {palette['accent']}",
        f"interface_help_colour: {mix(foreground, background, 0.35)}",
        f"interface_help_colour_bright: {palette['accent']}",
        "term_font_scale: 2x2",
        "term_margin: 120",
        "term_margin_gradient: 30",
        # Limine's alpha is inverted: 00 is opaque. The panel lets the wallpaper show through faintly.
        f"term_background: 30{background}",
        f"term_foreground: {foreground}",
        f"term_background_bright: {highlight}",
        f"term_foreground_bright: {palette.get('selection_foreground') or foreground}",
        "term_palette: " + ";".join(palette[f"color{index}"] for index in range(8)),
        "term_palette_bright: " + ";".join(palette[f"color{index}"] for index in range(8, 16)),
        f"backdrop: {background}",
    ]
    if wallpaper:
        lines += ["wallpaper: boot():/eitr/boot-menu.png", "wallpaper_style: stretched"]
    return "\n".join([*lines, STYLE_END]) + "\n"


def boot_menu_wallpaper(palette, path):
    """Render a quiet theme-coloured gradient with a soft accent glow; False without Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError:
        return False
    width, height = 1920, 1080
    background = palette["background"]
    light = sum(int(background[index:index + 2], 16) for index in (0, 2, 4)) > 3 * 128
    # Dark themes sink toward black; light ones deepen only slightly, toward their own text colour.
    bottom = mix(background, palette["foreground"], 0.08) if light else mix(background, "000000", 0.35)
    top = mix(background, palette["accent"], 0.10)
    image = Image.new("RGB", (1, height))
    for row in range(height):
        image.putpixel((0, row), tuple(bytes.fromhex(mix(top, bottom, row / (height - 1)))))
    image = image.resize((width, height))
    glow = Image.new("L", (width, height), 0)
    ImageDraw.Draw(glow).ellipse((width * 0.15, -height * 0.55, width * 0.85, height * 0.35), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    image = Image.composite(Image.new("RGB", (width, height), tuple(bytes.fromhex(palette["accent"]))), image, glow)
    encoded = io.BytesIO()
    image.save(encoded, "PNG", optimize=True)
    # The refresh runs at every shutdown; leave the ESP alone when nothing changed.
    if not path.is_file() or path.read_bytes() != encoded.getvalue():
        path.parent.mkdir(exist_ok=True)
        temporary = path.with_name(".boot-menu.png")
        temporary.write_bytes(encoded.getvalue())
        os.replace(temporary, path)
    return True


def styled_limine_config(text, block):
    """Replace (or, with an empty block, remove) the marked style block; entries stay untouched."""
    if STYLE_BEGIN in text:
        start = text.index(STYLE_BEGIN)
        end = text.index(STYLE_END, start) + len(STYLE_END)
        if text[end:end + 1] == "\n":
            end += 1
        text = text[:start] + text[end:]
    return block + text if block else text


def secure_boot_enabled():
    try:
        return SECURE_BOOT_VARIABLE.read_bytes()[-1:] == b"\x01"
    except OSError:
        return False


def limine_config():
    loader, evidence = detect_bootloader()
    if loader != "limine":
        raise RuntimeError(tr('The boot menu style needs Limine; this system uses {loader}. Nothing was changed.', loader=f'{loader}'))
    if secure_boot_enabled():
        raise RuntimeError(tr('Secure Boot is enabled; an enrolled Limine config hash would stop booting after an edit. Nothing was changed.'))
    config = SYSTEM_ROOT / evidence["limine"][0].lstrip("/")
    text = config.read_text()
    if STYLE_BEGIN in text and STYLE_END not in text:
        raise RuntimeError(tr('{config} has an unfinished EITR style block; fix it by hand. Nothing was changed.', config=f'{config}'))
    return config, text


def write_boot_menu_style(user):
    """Style Limine with the user's theme colours; returns False when nothing needed changing."""
    config, original = limine_config()
    palette, source = boot_menu_palette(user)
    esp = Path(output(["findmnt", "-n", "-o", "TARGET", "-T", str(config)]))
    has_wallpaper = boot_menu_wallpaper(palette, esp / "eitr/boot-menu.png")
    styled = styled_limine_config(original, limine_style_block(palette, has_wallpaper))
    if styled == original:
        return False
    backup = backup_boot_config(config)
    atomic(config, styled, mode=stat.S_IMODE(config.stat().st_mode))
    print(tr('Styled the boot menu in {config} with the colours of {source}. Backup: {backup}', config=f'{config}', source=f'{source}', backup=f'{backup}'))
    return True


def boot_menu_style(enable, named_user=None):
    """Apply or remove EITR's Limine menu style; applied, it follows theme changes at each shutdown.

    Through sudo it follows the invoking user; the installer, running as root, names the new user.
    """
    user = os.environ.get("SUDO_USER") or named_user
    if user == "root":
        user = None
    if enable:
        write_boot_menu_style(user)
        atomic(BOOT_MENU_STATE, json.dumps({"user": user}) + "\n", mode=0o644, directory_mode=0o755)
        # The unit refreshes the colours when the system shuts down; enabling it needs no running systemd.
        run(["systemctl", "enable", BOOT_MENU_UNIT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not in_chroot():
            run(["systemctl", "start", BOOT_MENU_UNIT])
        print(tr('It shows at the next boot and follows your theme from then on. Your boot entries were not changed.'))
        return
    config, original = limine_config()
    if STYLE_BEGIN in original:
        backup = backup_boot_config(config)
        atomic(config, styled_limine_config(original, ""), mode=stat.S_IMODE(config.stat().st_mode))
        print(tr('Removed the EITR boot menu style from {config}. Backup: {backup}', config=f'{config}', backup=f'{backup}'))
    wallpaper = Path(output(["findmnt", "-n", "-o", "TARGET", "-T", str(config)])) / "eitr/boot-menu.png"
    wallpaper.unlink(missing_ok=True)
    if wallpaper.parent.is_dir() and not any(wallpaper.parent.iterdir()):
        wallpaper.parent.rmdir()
    BOOT_MENU_STATE.unlink(missing_ok=True)
    subprocess.run(["systemctl", "disable", "--now", BOOT_MENU_UNIT], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(tr('Limine shows its default menu from the next boot. Your boot entries were not changed.'))


def boot_menu_refresh():
    """Run at shutdown: restyle with the recorded user's current theme, only when it changed."""
    try:
        user = json.loads(BOOT_MENU_STATE.read_text()).get("user")
    except (OSError, ValueError):
        return
    try:
        if STYLE_BEGIN in limine_config()[1]:
            write_boot_menu_style(user)
    except RuntimeError as error:
        print(error)


SNAPSHOTS = Path("/.snapshots")
PACKAGE_DATABASE = Path("var/lib/pacman/local")


def installed_packages(database):
    """name -> version from a pacman local database directory."""
    packages = {}
    if not database.is_dir():
        return packages
    for entry in database.iterdir():
        try:
            fields = entry.joinpath("desc").read_text().split("\n\n")
        except OSError:
            continue
        values = {block.split("\n", 1)[0]: block.split("\n", 1)[1].strip()
                  for block in fields if block.startswith("%") and "\n" in block}
        if values.get("%NAME%") and values.get("%VERSION%"):
            packages[values["%NAME%"]] = values["%VERSION%"]
    return packages


def package_changes(before, after):
    """What changed between two name -> version maps, each list sorted by name."""
    changed = {"upgraded": [], "downgraded": [], "installed": [], "removed": []}
    for name in sorted(before.keys() | after.keys()):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue
        if old is None:
            changed["installed"].append((name, new))
        elif new is None:
            changed["removed"].append((name, old))
        else:
            # vercmp prints a positive number when the first version is newer.
            comparison = subprocess.run(["vercmp", new, old], capture_output=True, text=True).stdout.strip()
            kind = "downgraded" if comparison.startswith("-") else "upgraded"
            changed[kind].append((name, f"{old} -> {new}"))
    return changed


def update_pairs():
    """Snapper's pre/post pairs from System Update: (pre, post or None, date, description)."""
    data = json.loads(output(["snapper", "-c", "root", "--jsonout", "list"]))
    snapshots = data.get("root", [])
    posts = {item.get("pre-number"): item for item in snapshots if item.get("type") == "post"}
    return [(item["number"], posts.get(item["number"], {}).get("number"), item.get("date", ""),
             posts.get(item["number"], {}).get("description", "not finished"))
            for item in snapshots if item.get("type") == "pre"]


def snapshot_changes(number=None):
    pairs = update_pairs()
    if not pairs:
        print(tr('No update snapshots yet.'))
        return
    def packages_at(snapshot):
        root = SNAPSHOTS / str(snapshot) / "snapshot" if snapshot else Path("/")
        return installed_packages(root / PACKAGE_DATABASE)
    if number is None:
        print(tr("Updates with snapshots (pass a 'before' number to see every package):\n"))
        for pre, post, date, outcome in pairs:
            changed = package_changes(packages_at(pre), packages_at(post))
            counts = ", ".join(f"{len(items)} {kind}" for kind, items in changed.items() if items) or "no changes"
            print(f"  {pre:>4} -> {post if post else 'now':<4} {date[:16]:<17} {counts}  ({outcome})")
        return
    match = next((pair for pair in pairs if str(pair[0]) == str(number)), None)
    if not match:
        raise RuntimeError(tr("Snapshot {number} is not the 'before' snapshot of an update", number=f'{number}'))
    pre, post, date, outcome = match
    changed = package_changes(packages_at(pre), packages_at(post))
    print(tr('Update of {update_date} (snapshot {pre} -> {state}, {outcome}):', update_date=f'{date[:16]}', pre=f'{pre}', state=f"{(post if post else 'the running system')}", outcome=f'{outcome}'))
    for kind, items in changed.items():
        if items:
            print(f"\n{kind.capitalize()} ({len(items)}):")
            for name, detail in items:
                print(f"  {name:<32} {detail}")
    if not any(changed.values()):
        print(tr('\nNo packages changed.'))


PACMAN_CONF = Path("/etc/pacman.conf")
TESTING_MARKER = "# Eitr testing channel: newer Eitr builds first (eitr channel stable switches back)"
TESTING_BLOCK = (TESTING_MARKER + "\n[eitr-testing]\nSigLevel = Required\n"
                 "Server = https://download.eitr.info/repo-testing\n\n")


def channel_status(conf=None):
    text = (conf or PACMAN_CONF).read_text()
    return "testing" if "\n[eitr-testing]\n" in "\n" + text else "stable"


def with_channel(text, channel):
    """pacman.conf with the testing repository listed right before [eitr], or without it."""
    without = text.replace(TESTING_BLOCK, "")
    if channel == "stable":
        return without
    if "\n[eitr]\n" not in "\n" + without:
        raise RuntimeError(tr('pacman.conf has no [eitr] repository to add the testing channel before'))
    index = ("\n" + without).index("\n[eitr]\n")
    return without[:index] + TESTING_BLOCK + without[index:]


TESTING_DATABASE = "https://download.eitr.info/repo-testing/eitr-testing.db"


def testing_reachable(url=TESTING_DATABASE):
    """Whether the testing repository can be downloaded; a missing one would break System Update."""
    import urllib.request
    try:
        # Cloudflare refuses Python's default user agent.
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Eitr System Update"})
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status == 200
    except OSError:
        return False


def channel_set(channel, conf=None, reachable=testing_reachable):
    conf = conf or PACMAN_CONF
    if channel not in ("stable", "testing"):
        raise ValueError(tr('The channel is stable or testing'))
    if channel == "testing" and channel_status(conf) != "testing" and not reachable():
        raise RuntimeError(tr('The testing repository cannot be reached right now, so nothing was changed. Check the connection and try again.'))
    text = conf.read_text()
    updated = with_channel(text, channel)
    if updated != text:
        atomic(conf, updated, mode=0o644, directory_mode=0o755)
    if channel == "testing":
        print(tr('Testing channel: System Update now installs new Eitr builds as soon as they are published, before everyone else. Everything else still comes from the stable repositories.'))
    else:
        print(tr('Stable channel. Eitr packages already newer than stable stay until stable catches up.'))


def firewall_allow_ssh():
    """Let SSH through the firewall; written whenever sshd is enabled, so remote logins keep working."""
    atomic(FIREWALL_OPENINGS / "ssh.nft", SSH_OPENING, mode=0o644, directory_mode=0o755)


def firewall_on():
    if not FIREWALL_RULES.is_file():
        raise RuntimeError(tr('{FIREWALL_RULES} is missing; update the eitr-desktop package first', FIREWALL_RULES=f'{FIREWALL_RULES}'))
    if unit_enabled("sshd.service"):
        firewall_allow_ssh()
    run(["systemctl", "enable", FIREWALL_UNIT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not in_chroot():
        run(["systemctl", "reload-or-restart", FIREWALL_UNIT])
    services = "KDE Connect, LocalSend" + (", SSH" if (FIREWALL_OPENINGS / "ssh.nft").is_file() else "")
    print(tr('The firewall is on: incoming connections are refused except replies and these sharing services: {services}.', services=services))


def firewall_off():
    subprocess.run(["systemctl", "disable", "--now", FIREWALL_UNIT], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(tr('The firewall is off: every incoming connection reaches the apps listening for it.'))


def firewall_status():
    active = subprocess.run(["systemctl", "is-active", "--quiet", FIREWALL_UNIT]).returncode == 0
    openings = sorted(path.stem for path in FIREWALL_OPENINGS.glob("*.nft")) if FIREWALL_OPENINGS.is_dir() else []
    if openings:
        print(tr('Firewall: on (also open: {ports})', ports=', '.join(openings)) if active
              else tr('Firewall: off (also open: {ports})', ports=', '.join(openings)))
    else:
        print(tr('Firewall: on') if active else tr('Firewall: off'))
    return 0 if active else 3


READ_ONLY_ACTIONS = {"snapshots-check", "bootloader-detect", "snapshots-boot-status", "battery-limit-status",
                     "firewall-status", "channel-status"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["snapshots-check", "snapshots-setup", "snapshot-pre", "snapshot-post",
                                           "bootloader-detect", "snapshots-boot-status", "snapshots-boot-setup",
                                           "battery-limit", "battery-limit-apply", "battery-limit-status",
                                           "luks-tpm-check", "luks-tpm-enroll", "luks-recovery-key", "luks-tpm-remove",
                                           "auth-enable", "auth-restore", "boot-menu-style",
                                           "boot-menu-style-remove", "boot-menu-refresh",
                                           "firewall-on", "firewall-off", "firewall-status", "firewall-allow-ssh",
                                           "snapshot-changes", "channel-status", "channel-set",
                                           "remote-setup", "remote-arm", "remote-undo", "remote-open", "remote-close",
                                           "remote-tailscale", "remote-tailscale-undo"])
    parser.add_argument("argument", nargs="?",
                        help='auth-enable: fingerprint|fido2|password; auth-restore: backup name; snapshot-post: success|failed; boot-menu-style: desktop user; battery-limit: 60-100|off; luks-*: /dev path')
    args = parser.parse_args()
    # Read-only checks may run unprivileged (an unreadable EFI partition then
    # reports "unknown"), so the installer's --check can use them.
    if args.action not in READ_ONLY_ACTIONS and os.geteuid() != 0:
        parser.error('This root-owned helper must run through sudo or a pacman hook')
    try:
        if args.action.startswith("remote-"):
            import eitr_remote
            eitr_remote.dispatch(args.action.removeprefix("remote-"), args.argument)
        elif args.action == "snapshots-check":
            snapshot_supported()
        elif args.action == "snapshots-setup":
            setup_snapshots()
        elif args.action == "bootloader-detect":
            print(detect_bootloader()[0])
        elif args.action == "snapshots-boot-status":
            sys.exit(boot_snapshot_status())
        elif args.action == "snapshots-boot-setup":
            setup_boot_snapshots()
        elif args.action == "battery-limit":
            battery_limit(args.argument)
        elif args.action == "battery-limit-apply":
            battery_limit_apply()
        elif args.action == "battery-limit-status":
            sys.exit(battery_limit_status())
        elif args.action == "luks-tpm-check":
            luks_tpm_check(args.argument)
        elif args.action == "luks-tpm-enroll":
            luks_tpm_enroll(args.argument)
        elif args.action == "luks-recovery-key":
            luks_recovery_key(args.argument)
        elif args.action == "luks-tpm-remove":
            luks_tpm_remove(args.argument)
        elif args.action == "snapshot-pre":
            snapshot_pre()
        elif args.action == "snapshot-post":
            if args.argument not in (None, "success", "failed"):
                parser.error('snapshot-post outcome must be success or failed')
            snapshot_post(args.argument or "success")
        elif args.action == "auth-enable":
            if args.argument not in ("fingerprint", "fido2", "password"):
                parser.error('Authentication method required: fingerprint, fido2 or password')
            enable_auth(args.argument)
        elif args.action in ("boot-menu-style", "boot-menu-style-remove"):
            boot_menu_style(args.action == "boot-menu-style", args.argument)
        elif args.action == "boot-menu-refresh":
            boot_menu_refresh()
        elif args.action == "firewall-on":
            firewall_on()
        elif args.action == "firewall-off":
            firewall_off()
        elif args.action == "firewall-status":
            sys.exit(firewall_status())
        elif args.action == "firewall-allow-ssh":
            firewall_allow_ssh()
        elif args.action == "channel-status":
            print(channel_status())
        elif args.action == "channel-set":
            channel_set(args.argument or "")
        elif args.action == "snapshot-changes":
            if args.argument is not None and not args.argument.isdigit():
                parser.error('snapshot-changes takes a snapshot number')
            snapshot_changes(args.argument)
        elif args.action == "auth-restore":
            if not args.argument:
                parser.error('PAM backup name required')
            restore_auth(args.argument)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error) + "\n")
