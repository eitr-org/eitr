#!/usr/bin/env python3
"""Prepare the next boot's network backend without restarting live networking."""
import eitr_bootstrap
from eitr_i18n import tr
import argparse
import base64
import configparser
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

STATE = Path("/var/lib/eitr/network-backend")
ETC = Path("/etc")
IWD = Path("/var/lib/iwd")
UNITS = ("iwd.service", "systemd-networkd.service", "NetworkManager.service", "systemd-resolved.service")
# The same files distro/network installs on fresh systems; tests keep them equal.
NETWORKD_FILES = {
    "20-ethernet.network": "[Match]\nType=ether\n\n[Network]\nDHCP=yes\n",
    "20-wifi.network": "[Match]\nType=wlan\n\n[Network]\nDHCP=yes\n",
}
FILES = ("NetworkManager/conf.d/99-eitr.conf", "iwd/main.conf",
         "systemd/network/20-ethernet.network", "systemd/network/20-wifi.network")


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def atomic(path, content, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".eitr-")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def capture():
    units = {unit: subprocess.run(["systemctl", "is-enabled", unit], capture_output=True, text=True).stdout.strip()
             for unit in UNITS}
    if any(status in ("masked", "masked-runtime") for status in units.values()):
        raise RuntimeError(tr('A network service is masked; review your custom configuration before switching.'))
    files, modes = {}, {}
    for name in FILES:
        path = ETC / name
        if path.is_symlink():
            raise RuntimeError(tr('Refusing to replace custom symlink: {path}', path=f'{path}'))
        files[name] = path.read_text() if path.exists() else None
        modes[name] = path.stat().st_mode & 0o777 if path.exists() else 0o644
    return {"units": units, "files": files, "modes": modes}


def restore(snapshot):
    for name, content in snapshot["files"].items():
        path = ETC / name
        if content is None:
            path.unlink(missing_ok=True)
        else:
            atomic(path, content, snapshot.get("modes", {}).get(name, 0o644))
    for unit, status in snapshot["units"].items():
        run(["systemctl", "enable" if status in ("enabled", "enabled-runtime") else "disable", unit])


def stage(backend):
    if backend not in ("iwd", "networkmanager"):
        raise ValueError(tr('Choose iwd or NetworkManager'))
    for package in ("iwd", "networkmanager", "wpa_supplicant"):
        if subprocess.run(["pacman", "-Q", package], capture_output=True).returncode:
            raise RuntimeError(tr('Install {package} first: sudo pacman -Syu --needed {package_2}', package=f'{package}', package_2=f'{package}'))
    resolver = ETC / "resolv.conf"
    if not resolver.is_symlink() or resolver.resolve() not in (
            Path("/run/systemd/resolve/stub-resolv.conf"), Path("/run/systemd/resolve/resolv.conf")):
        raise RuntimeError(tr('This switch requires systemd-resolved DNS. Review /etc/resolv.conf first; no changes made.'))
    for unit in ("connman.service", "dhcpcd.service"):
        if subprocess.run(["systemctl", "is-active", "--quiet", unit], capture_output=True).returncode == 0:
            raise RuntimeError(tr('{unit} manages networking; review that custom setup first.', unit=f'{unit}'))
    before = capture()
    if backend == "networkmanager":
        for path in (ETC / "NetworkManager/conf.d").glob("*.conf"):
            if path.name != "99-eitr.conf" and re.search(r"^\s*wifi\.backend\s*=\s*iwd\b", path.read_text(), re.MULTILINE):
                raise RuntimeError(tr('Conflicting iwd backend setting in {path}; review it before switching.', path=f'{path}'))
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = STATE / "original.json"
    if not backup.exists():
        atomic(backup, json.dumps(before))
    try:
        if backend == "networkmanager":
            atomic(ETC / FILES[0], "[main]\ndns=systemd-resolved\n\n[device]\nwifi.backend=wpa_supplicant\n", 0o644)
            on, off = ("NetworkManager.service", "systemd-resolved.service"), ("iwd.service", "systemd-networkd.service")
        else:
            config = configparser.ConfigParser(interpolation=None)
            config.optionxform = str
            path = ETC / "iwd/main.conf"
            if path.exists():
                config.read(path)
            if not config.has_section("General"):
                config.add_section("General")
            config["General"]["EnableNetworkConfiguration"] = "false"
            stream = io.StringIO()
            config.write(stream, space_around_delimiters=False)
            atomic(path, stream.getvalue(), 0o644)
            # Existing files are kept: they may hold custom addressing.
            for name, content in NETWORKD_FILES.items():
                path = ETC / "systemd/network" / name
                if not path.exists():
                    atomic(path, content, 0o644)
            on, off = ("iwd.service", "systemd-networkd.service", "systemd-resolved.service"), ("NetworkManager.service",)
        # No --now: current connections and service processes stay untouched.
        for unit in off:
            run(["systemctl", "disable", unit])
        for unit in on:
            run(["systemctl", "enable", unit])
        atomic(STATE / "selected", backend + "\n")
    except Exception:
        restore(before)
        raise
    print(tr('Saved for the next boot. Your current connection has not changed.'))


def enterprise(request):
    name = request.get("name", "")
    if not isinstance(name, str) or not 1 <= len(name.encode()) <= 32:
        raise ValueError(tr('Invalid WiFi name'))
    method = request.get("eap", "peap")
    if method not in ("peap", "ttls"):
        raise ValueError(tr('Unsupported enterprise method'))
    for key in ("identity", "password", "domain"):
        value = request.get(key)
        if not isinstance(value, str) or not value or any(char in value for char in "\n\r\0"):
            raise ValueError(tr('Enterprise credentials and server domain are required'))
    anonymous = request.get("anonymous", "")
    if not isinstance(anonymous, str) or any(char in anonymous for char in "\n\r\0"):
        raise ValueError(tr('Invalid anonymous identity'))
    if not re.fullmatch(r"[A-Za-z0-9.-]+", request["domain"]):
        raise ValueError(tr('Enter the authentication server domain without wildcards'))
    certificate = base64.b64decode(request.get("certificate", ""), validate=True).decode("ascii")
    if len(certificate) > 65536 or not re.fullmatch(
            r"(?:\s*-----BEGIN CERTIFICATE-----\s+[A-Za-z0-9+/=\s]+-----END CERTIFICATE-----\s*)+", certificate):
        raise ValueError(tr('A PEM CA certificate is required'))
    # iwd reads a plain file name for SSIDs made of letters, digits, " ", "_" and "-",
    # and ignores a hex-encoded name for those SSIDs.
    safe = re.fullmatch(r"[A-Za-z0-9 _-]+", name)
    path = IWD / ((name if safe else "=" + name.encode().hex()) + ".8021x")
    if path.exists():
        raise RuntimeError(tr('Enterprise profile exists; forget it in the panel before replacing credentials.'))
    prefix = "EAP-" + method.upper()
    def escape(value):
        return value.replace("\\", "\\\\").replace("\t", "\\t").replace(" ", "\\s")
    content = (f"[Security]\nEAP-Method={method.upper()}\nEAP-Identity={escape(anonymous or request['identity'])}\n"
               f"{prefix}-CACert=embed:eitr_ca\n{prefix}-ServerDomainMask={request['domain']}\n"
               f"{prefix}-Phase2-Method={'MSCHAPV2' if method == 'peap' else 'Tunneled-PAP'}\n"
               f"{prefix}-Phase2-Identity={escape(request['identity'])}\n{prefix}-Phase2-Password={escape(request['password'])}\n"
               f"\n[@pem@eitr_ca]\n{certificate.rstrip()}\n")
    atomic(path, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "restore", "enterprise"))
    parser.add_argument("backend", nargs="?", choices=("iwd", "networkmanager"))
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Use the root-owned helper through sudo or pkexec')
    if args.action == "stage":
        stage(args.backend)
    elif args.action == "restore":
        original = STATE / "original.json"
        if not original.exists():
            raise RuntimeError(tr('Nothing to restore: the network backend was never switched.'))
        restore(json.loads(original.read_text()))
        (STATE / "selected").unlink(missing_ok=True)
        print(tr('Original configuration restored for the next boot; current networking is unchanged.'))
    else:
        enterprise(json.loads(sys.stdin.readline(100000)))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
