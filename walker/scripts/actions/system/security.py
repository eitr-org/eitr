#!/usr/bin/env python3
"""Interactive enrollment; policy changes only after separate confirmation."""
import getpass
import os
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config
from eitr_i18n import tr
import subprocess

# The eitr-desktop package installs the helper under /usr/lib; earlier manual
# installs used /usr/local/lib. Both locations are root-owned.
ROOT_HELPERS = ("/usr/lib/eitr/eitr-system", "/usr/local/lib/eitr/eitr-system")


def root_helper():
    return next((path for path in ROOT_HELPERS if Path(path).is_file()), None)


def fido_enroll():
    user = getpass.getuser()
    path = user_config("Yubico/u2f_keys")
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    result = subprocess.run(["pamu2fcfg", "-u", user, "-o", "pam://eitr", "-i", "pam://eitr"],
                            capture_output=True, text=True, check=True)
    registration = result.stdout.strip()
    if not registration.startswith(user + ":") or "\n" in registration:
        raise ValueError(tr('Unexpected FIDO2 registration'))
    if path.exists():
        existing = path.read_text().strip()
        if not existing.startswith(user + ":") or "\n" in existing:
            raise ValueError(tr('Existing FIDO2 registration needs manual review'))
        # Credentials are "keyhandle,publickey,..." entries joined by ":".
        known = {credential.split(",", 1)[0] for credential in existing.split(":")[1:]}
        added = [credential for credential in registration.split(":")[1:]
                 if credential.split(",", 1)[0] not in known]
        if not added:
            print(tr('This security key is already enrolled.'))
            return
        registration = ":".join([existing, *added])
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as file:
        os.fchmod(file.fileno(), 0o600)
        file.write(registration + "\n")
    print(tr('Security key enrolled. Enable FIDO2 authentication separately; keep your password available.'))


def require_helper():
    helper = root_helper()
    if helper is None:
        raise RuntimeError(tr('The root-owned Eitr helper is not installed. See distro/README.md; never sudo a user-writable helper.'))
    return helper


def luks_devices():
    result = subprocess.run(["lsblk", "-rpno", "PATH,FSTYPE"], capture_output=True, text=True, check=True)
    rows = (line.split() for line in result.stdout.splitlines())
    return [row[0] for row in rows if len(row) == 2 and row[1] == "crypto_LUKS"]


def choose_luks_device():
    devices = luks_devices()
    if not devices:
        raise RuntimeError(tr('No LUKS-encrypted partition was found.'))
    if len(devices) == 1:
        return devices[0]
    for number, device in enumerate(devices, 1):
        print(f"{number}. {device}")
    choice = input(tr('Encrypted partition number: ')).strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(devices):
        raise ValueError(tr('No encrypted partition selected; nothing was changed.'))
    return devices[int(choice) - 1]


TPM_EXPLANATION = """
TPM unlock lets this computer open the encrypted disk at boot without the
passphrase while its firmware and Secure Boot state (TPM PCR 7) are unchanged.
Anyone who boots this computer unmodified reaches the login screen with the disk
unlocked; your login password still protects the session.
The existing passphrase stays enrolled. It is needed after firmware updates,
Secure Boot key changes or a TPM reset, then TPM unlock must be re-enrolled.
Undo at any time with Security > TPM Disk Unlock > Remove TPM Unlock.
"""


def tpm_action(action):
    helper = require_helper()
    device = choose_luks_device()
    if action == "tpm-status":
        subprocess.run(["sudo", helper, "luks-tpm-check", device], check=True)
        return
    if action == "tpm-remove":
        print(tr('This removes TPM unlock from {device}; the passphrase is required at every boot again.', device=f'{device}'))
        if input(tr('Type {confirmation} to confirm (anything else cancels): ', confirmation='REMOVE TPM')) == "REMOVE TPM":
            subprocess.run(["sudo", helper, "luks-tpm-remove", device], check=True)
        return
    subprocess.run(["sudo", helper, "luks-tpm-check", device], check=True)
    print(TPM_EXPLANATION)
    if input(tr('Create a recovery key first? Strongly recommended.') + ' [Y/n]: ').strip().lower() not in ("n", "no"):
        subprocess.run(["sudo", helper, "luks-recovery-key", device], check=True)
        input(tr('Write the recovery key down and store it offline, then press Enter. '))
    if input(tr('Type {confirmation} to enroll TPM unlock (anything else cancels): ', confirmation='ENROLL TPM')) != "ENROLL TPM":
        return
    subprocess.run(["sudo", helper, "luks-tpm-enroll", device], check=True)


def main(action):
    if action in ("tpm-enroll", "tpm-remove", "tpm-status"):
        tpm_action(action)
    elif action == "password":
        subprocess.run(["passwd"], check=True)
    elif action == "fingerprint":
        subprocess.run(["fprintd-enroll"], check=True)
        print(tr('Fingerprint enrolled. Enable fingerprint authentication separately.'))
    elif action == "fido2":
        fido_enroll()
    elif action in ("enable-fingerprint", "enable-fido2", "password-only"):
        helper = require_helper()
        method = "password" if action == "password-only" else action.removeprefix("enable-")
        print(tr('This changes login, lockscreen and sudo authentication. Password fallback is retained.'))
        if input(tr('Type {confirmation} to confirm (anything else cancels): ', confirmation='ENABLE')) != "ENABLE":
            return
        subprocess.run(["sudo", helper, "auth-enable", method], check=True)
    else:
        raise ValueError('Unknown security action')


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
