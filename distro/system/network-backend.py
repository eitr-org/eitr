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
import stat
import subprocess
import sys
import tempfile

STATE = Path("/var/lib/eitr/network-backend")
ETC = Path("/etc")
IWD = Path("/var/lib/iwd")
IWD_SUFFIXES = (".psk", ".8021x", ".open")
NM_SUFFIXES = (".nmconnection",)
MAX_WIFI_PROFILE_BYTES = 131072
MAX_WIFI_STDIN_BYTES = 4 * 1024 * 1024
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


def atomic_bytes(path, raw, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".eitr-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
        os.chmod(temporary, mode)
        if os.geteuid() == 0:
            os.chown(temporary, 0, 0)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def validate_wifi_profile_name(backend, name):
    if backend not in ("iwd", "networkmanager"):
        raise ValueError(tr('Choose iwd or NetworkManager'))
    if not isinstance(name, str) or not name or len(name.encode("utf-8")) > 255:
        raise ValueError(tr('Invalid WiFi profile filename'))
    if "/" in name or "\\" in name or "\x00" in name or name in (".", "..") or ".." in name or name.startswith("."):
        raise ValueError(tr('Invalid WiFi profile filename'))
    suffixes = IWD_SUFFIXES if backend == "iwd" else NM_SUFFIXES
    matched = next((suf for suf in suffixes if name.endswith(suf)), None)
    if not matched or len(name) <= len(matched):
        raise ValueError(tr('Invalid WiFi profile filename'))
    return name


def _profile_dir(backend):
    if backend == "iwd":
        if IWD.is_symlink():
            raise RuntimeError(tr('Refusing to replace custom symlink: {path}', path=f'{IWD}'))
        return IWD
    nm_parent = ETC / "NetworkManager"
    nm_dir = nm_parent / "system-connections"
    for check_path in (ETC, nm_parent, nm_dir):
        if check_path.is_symlink():
            raise RuntimeError(tr('Refusing to replace custom symlink: {path}', path=f'{check_path}'))
    return nm_dir


def _read_regular_profile(path):
    if path.is_symlink():
        raise ValueError(tr('Refusing symlinked WiFi profile: {path}', path=f'{path}'))
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(tr('WiFi profile must be a regular file: {path}', path=f'{path}'))
        if info.st_size > MAX_WIFI_PROFILE_BYTES:
            raise ValueError(tr('WiFi profile exceeds size limit: {path}', path=f'{path}'))
        with os.fdopen(fd, "rb") as stream:
            fd = None
            data = stream.read(MAX_WIFI_PROFILE_BYTES + 1)
    finally:
        if fd is not None:
            os.close(fd)
    if len(data) > MAX_WIFI_PROFILE_BYTES:
        raise ValueError(tr('WiFi profile exceeds size limit: {path}', path=f'{path}'))
    return data


def is_wifi_profile(backend, raw):
    """iwd keeps only WiFi profiles; a NetworkManager keyfile must say it is WiFi, so VPN,
    ethernet and other connections (and their secrets) never pass through these actions."""
    if backend == "iwd":
        return True
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read_string(raw.decode("utf-8"))
    except (UnicodeDecodeError, configparser.Error):
        return False
    return parser.get("connection", "type", fallback="").strip() in ("wifi", "802-11-wireless")


def reload_networkmanager():
    try:
        subprocess.run(["nmcli", "connection", "reload"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError):
        pass


def export_wifi():
    profiles = []
    for backend, suffixes in (("iwd", IWD_SUFFIXES), ("networkmanager", NM_SUFFIXES)):
        directory = _profile_dir(backend)
        if not directory.exists():
            continue
        if not directory.is_dir():
            raise ValueError(tr('WiFi profile directory is not a folder: {path}', path=f'{directory}'))
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            if entry.name.startswith(".") or not entry.name.endswith(suffixes):
                continue
            validate_wifi_profile_name(backend, entry.name)
            raw = _read_regular_profile(entry)
            if not is_wifi_profile(backend, raw):
                continue
            profiles.append({
                "backend": backend,
                "name": entry.name,
                "content_b64": base64.b64encode(raw).decode("ascii"),
            })
    return {"profiles": profiles}


def import_wifi(request):
    if not isinstance(request, dict):
        raise ValueError(tr('Invalid WiFi import payload'))
    raw_profiles = request.get("profiles", [])
    raw_removals = request.get("remove", [])
    overwrite = bool(request.get("overwrite", True))
    if not isinstance(raw_profiles, list) or not isinstance(raw_removals, list):
        raise ValueError(tr('Invalid WiFi import payload'))

    validated = []
    for item in raw_profiles:
        if not isinstance(item, dict):
            raise ValueError(tr('Invalid WiFi import payload'))
        backend = item.get("backend")
        name = validate_wifi_profile_name(backend, item.get("name", ""))
        if "content_b64" in item:
            raw = base64.b64decode(item["content_b64"], validate=True)
        elif isinstance(item.get("content"), str):
            raw = item["content"].encode("utf-8")
        else:
            raise ValueError(tr('WiFi profile content is required'))
        if not 1 <= len(raw) <= MAX_WIFI_PROFILE_BYTES:
            raise ValueError(tr('WiFi profile exceeds size limit: {path}', path=name))
        if not is_wifi_profile(backend, raw):
            raise ValueError(tr('Not a WiFi profile: {path}', path=name))
        directory = _profile_dir(backend)
        target = directory / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(tr('Refusing symlinked WiFi profile: {path}', path=f'{target}'))
        if target.exists() and not overwrite:
            raise RuntimeError(tr('WiFi profile already exists: {path}', path=f'{target}'))
        validated.append((backend, name, raw, target))

    removals = []
    for item in raw_removals:
        if not isinstance(item, dict):
            raise ValueError(tr('Invalid WiFi import payload'))
        backend = item.get("backend")
        name = validate_wifi_profile_name(backend, item.get("name", ""))
        target = _profile_dir(backend) / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(tr('Refusing symlinked WiFi profile: {path}', path=f'{target}'))
        removals.append((backend, name, target))

    previous = []
    for backend, name, raw, target in validated:
        if target.exists():
            old_bytes = _read_regular_profile(target)
            previous.append({
                "backend": backend,
                "name": name,
                "existed": True,
                "content_b64": base64.b64encode(old_bytes).decode("ascii"),
            })
        else:
            previous.append({"backend": backend, "name": name, "existed": False})
        atomic_bytes(target, raw, 0o600)

    for _backend, _name, target in removals:
        if target.exists():
            _read_regular_profile(target)
            target.unlink()

    if any(backend == "networkmanager" for backend, *_ in validated + removals):
        reload_networkmanager()
    return {"imported": len(validated), "removed": len(removals), "previous": previous}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "restore", "enterprise", "export-wifi", "import-wifi"))
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
    elif args.action == "export-wifi":
        print(json.dumps(export_wifi()))
    elif args.action == "import-wifi":
        print(json.dumps(import_wifi(json.loads(sys.stdin.read(MAX_WIFI_STDIN_BYTES)))))
    else:
        enterprise(json.loads(sys.stdin.readline(100000)))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
