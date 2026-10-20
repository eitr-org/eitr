"""NetworkManager adapter for the shared WiFi panel, using its typed D-Bus API."""
import eitr_bootstrap
from eitr_i18n import tr
from pathlib import Path
import re
import time
import uuid

from gi.repository import Gio, GLib

SERVICE = "org.freedesktop.NetworkManager"
ROOT = "/org/freedesktop/NetworkManager"
SETTINGS = ROOT + "/Settings"
PROPERTIES = "org.freedesktop.DBus.Properties"


def call(bus, path, interface, method, parameters=None):
    return bus.call_sync(SERVICE, path, interface, method, parameters, None,
                         Gio.DBusCallFlags.NONE, 45000, None).unpack()


def properties(bus, path, interface):
    return call(bus, path, PROPERTIES, "GetAll", GLib.Variant("(s)", (interface,)))[0]


def security(ap):
    flags = ap.get("WpaFlags", 0) | ap.get("RsnFlags", 0)
    if flags & 0x200:
        return "8021x"
    # WPA2/WPA3 transition networks advertise both; a PSK profile works with either.
    if flags & 0x100:
        return "psk"
    if flags & 0x400:
        return "sae"
    return "unsupported" if ap.get("Flags", 0) & 1 or flags else "open"


def profile_security(settings):
    key = settings.get("802-11-wireless-security", {}).get("key-mgmt", "")
    return {"": "open", "wpa-psk": "psk", "sae": "sae", "wpa-eap": "8021x"}.get(key, "unsupported")


def profiles(bus):
    result = {}
    for path in call(bus, SETTINGS, SERVICE + ".Settings", "ListConnections")[0]:
        settings = call(bus, path, SERVICE + ".Settings.Connection", "GetSettings")[0]
        wifi = settings.get("802-11-wireless")
        if wifi:
            result[(bytes(wifi.get("ssid", [])).decode("utf-8", "replace"), profile_security(settings))] = path
    return result


def snapshot(bus, telemetry):
    saved = profiles(bus)
    manager = properties(bus, ROOT, SERVICE)
    devices = []
    for path in manager.get("Devices", []):
        device = properties(bus, path, SERVICE + ".Device")
        if device.get("DeviceType") != 2:
            continue
        wireless = properties(bus, path, SERVICE + ".Device.Wireless")
        active = wireless.get("ActiveAccessPoint", "/")
        networks = {}
        band = ""
        for ap_path in wireless.get("AccessPoints", []):
            ap = properties(bus, ap_path, SERVICE + ".AccessPoint")
            name = bytes(ap.get("Ssid", [])).decode("utf-8", "replace")
            if not name:
                continue
            kind = security(ap)
            key = (name, kind)
            row = {"name": name, "type": kind, "path": ap_path, "devicePath": path,
                   "known": key in saved, "knownPath": saved.get(key, ""), "available": True,
                   "connected": ap_path == active, "strength": ap.get("Strength", 0)}
            previous = networks.get(key)
            if previous is None or row["connected"] or not previous["connected"] and row["strength"] > previous["strength"]:
                networks[key] = row
            if row["connected"]:
                frequency = ap.get("Frequency", 0)
                band = "6 GHz" if frequency >= 5925 else "5 GHz" if frequency >= 4900 else "2.4 GHz"
        for key, known_path in saved.items():
            if key not in networks:
                networks[key] = {"name": key[0], "type": key[1], "path": "", "devicePath": path,
                                 "known": True, "knownPath": known_path, "available": False,
                                 "connected": False, "strength": None}
        details = telemetry(device["Interface"])
        details.update(band=band)
        state = device.get("State", 0)
        devices.append({"path": path, "name": device["Interface"],
                        "powered": manager.get("WirelessEnabled", False), "scanning": False,
                        "state": "connected" if state == 100 else "connecting" if 40 <= state < 100 else "disconnected",
                        "networks": sorted(networks.values(), key=lambda row: (not row["connected"], -float(row["strength"] or 0), row["name"])),
                        "details": details})
    return {"devices": devices, "backend": "networkmanager"}


def connection_settings(name, kind, request):
    v = GLib.Variant
    settings = {"connection": {"id": v("s", name), "uuid": v("s", str(uuid.uuid4())),
                               "type": v("s", "802-11-wireless"), "autoconnect": v("b", True)},
                "802-11-wireless": {"ssid": v("ay", name.encode()), "mode": v("s", "infrastructure")},
                "ipv4": {"method": v("s", "auto")}, "ipv6": {"method": v("s", "auto")}}
    if kind in ("psk", "sae"):
        password = request.get("password", "")
        if not password:
            raise ValueError(tr('Enter the WiFi password'))
        settings["802-11-wireless-security"] = {"key-mgmt": v("s", "sae" if kind == "sae" else "wpa-psk"), "psk": v("s", password)}
    elif kind == "8021x":
        method = request.get("eap", "peap")
        if method not in ("peap", "ttls"):
            raise ValueError(tr('Supported enterprise methods: PEAP/MSCHAPv2 and TTLS/PAP'))
        for key in ("identity", "password", "domain", "ca"):
            if not isinstance(request.get(key), str) or not request[key].strip():
                raise ValueError(tr('Enterprise WiFi requires username, password, CA certificate and server domain'))
        certificate = Path(request["ca"]).expanduser().resolve()
        if not certificate.is_file():
            raise ValueError(tr('CA certificate file not found'))
        if not re.fullmatch(r"[A-Za-z0-9.-]+", request["domain"]):
            raise ValueError(tr('Enter the authentication server domain without wildcards'))
        settings["802-11-wireless-security"] = {"key-mgmt": v("s", "wpa-eap")}
        settings["802-1x"] = {"eap": v("as", [method]), "identity": v("s", request["identity"]),
                              "password": v("s", request["password"]),
                              "phase2-auth": v("s", "mschapv2" if method == "peap" else "pap"),
                              "domain-suffix-match": v("s", request["domain"]),
                              "ca-cert": v("ay", ("file://" + str(certificate)).encode() + b"\0")}
        if request.get("anonymous"):
            settings["802-1x"]["anonymous-identity"] = v("s", request["anonymous"])
    elif kind != "open":
        raise ValueError(tr('This WiFi security type requires advanced network configuration'))
    return settings


def action(bus, kind, path, request=None, extra=None):
    if kind == "power":
        call(bus, ROOT, PROPERTIES, "Set", GLib.Variant("(ssv)", (SERVICE, "WirelessEnabled", GLib.Variant("b", extra == "true"))))
    elif kind == "scan":
        call(bus, path, SERVICE + ".Device.Wireless", "RequestScan", GLib.Variant("(a{sv})", ({},)))
    elif kind == "disconnect":
        call(bus, path, SERVICE + ".Device", "Disconnect")
    elif kind == "forget":
        call(bus, path, SERVICE + ".Settings.Connection", "Delete")
    elif kind == "connect":
        ap = properties(bus, path, SERVICE + ".AccessPoint")
        name = bytes(ap["Ssid"]).decode("utf-8", "replace")
        saved = profiles(bus).get((name, security(ap)))
        device = request.get("devicePath", "")
        if not device.startswith(ROOT + "/Devices/"):
            raise ValueError(tr('WiFi adapter is unavailable; refresh the panel'))
        if saved and not request.get("password"):
            active = call(bus, ROOT, SERVICE, "ActivateConnection", GLib.Variant("(ooo)", (saved, device, path)))[0]
        else:
            settings = connection_settings(name, security(ap), request)
            active = call(bus, ROOT, SERVICE, "AddAndActivateConnection", GLib.Variant("(a{sa{sv}}oo)", (settings, device, path)))[1]
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            state = properties(bus, active, SERVICE + ".Connection.Active").get("State", 0)
            if state == 2:
                return {"ok": True}
            if state == 4:
                raise RuntimeError(tr('Connection failed; verify credentials and certificate settings'))
            time.sleep(0.25)
        raise RuntimeError(tr('Connection timed out; check the WiFi panel'))
    else:
        raise ValueError('Unknown WiFi action')
    return {"ok": True}
