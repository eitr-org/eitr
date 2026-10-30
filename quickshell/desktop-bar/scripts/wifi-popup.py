#!/usr/bin/env python3
"""Read and control the active WiFi backend without changing network services."""
import eitr_bootstrap
from eitr_i18n import tr
import importlib.util
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from gi.repository import Gio, GLib

SERVICE = "net.connman.iwd"
PREFIX = SERVICE + "."
NETWORK_HELPER = Path("/usr/lib/eitr/eitr-network")
bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

spec = importlib.util.spec_from_file_location("wifi_nm", Path(__file__).with_name("wifi-networkmanager.py"))
NM_ADAPTER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(NM_ADAPTER)


def active_backend():
    def owns(service):
        return bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                             "NameHasOwner", GLib.Variant("(s)", (service,)), None,
                             Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
    nm, iwd = owns("org.freedesktop.NetworkManager"), owns(SERVICE)
    if nm and iwd:
        raise RuntimeError(tr('Both network backends are running; select one in Settings > Connectivity > Network Backend and reboot'))
    if nm:
        return "networkmanager"
    if iwd:
        return "iwd"
    raise RuntimeError(tr('No WiFi backend is running'))


def call(path, interface, method, parameters=None):
    return bus.call_sync(SERVICE, path, interface, method, parameters, None,
                         Gio.DBusCallFlags.NONE, 5000, None).unpack()


def merge_known(networks, objects):
    result = [dict(network, available=True) for network in networks]
    visible = {(network["name"], network["type"]) for network in result}
    saved = [dict(interfaces[PREFIX + "KnownNetwork"], path=path) for path, interfaces in objects.items()
             if PREFIX + "KnownNetwork" in interfaces]
    saved_paths = {(network.get("Name"), network.get("Type")): network["path"] for network in saved}
    saved_keys = {(network.get("Name"), network.get("Type")) for network in saved}
    for network in result:
        network["known"] = network["known"] or (network["name"], network["type"]) in saved_keys
        network["knownPath"] = saved_paths.get((network["name"], network["type"]), "")
    for network in sorted(saved, key=lambda item: item.get("Name", "").casefold()):
        key = (network.get("Name"), network.get("Type"))
        if key in visible:
            continue
        result.append({"path": "", "name": network.get("Name", "Hidden network"),
                       "type": network.get("Type", ""), "known": True,
                       "connected": False, "available": False, "strength": None, "knownPath": network["path"]})
    return result


def snapshot(include_details=True):
    objects = call("/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects")[0]
    devices = []
    for path, interfaces in objects.items():
        device = interfaces.get(PREFIX + "Device")
        if not device or device.get("Mode") != "station":
            continue
        station = interfaces.get(PREFIX + "Station", {})
        networks = []
        if device.get("Powered") and station:
            for network_path, strength in call(path, PREFIX + "Station", "GetOrderedNetworks")[0]:
                network = objects.get(network_path, {}).get(PREFIX + "Network", {})
                networks.append({"path": network_path, "name": network.get("Name", "Hidden network"),
                                 "type": network.get("Type", ""), "known": bool(network.get("KnownNetwork")),
                                 "connected": station.get("ConnectedNetwork") == network_path,
                                 "strength": max(0, min(100, 2 * (strength / 100 + 100)))})
        networks = merge_known(networks, objects)
        details = telemetry(device["Name"]) if include_details else {}
        if include_details and station.get("State") == "connected":
            try:
                diagnostic = call(path, PREFIX + "StationDiagnostic", "GetDiagnostics")[0]
                frequency = diagnostic.get("Frequency", 0)
                details["band"] = "6 GHz" if frequency >= 5925 else "5 GHz" if frequency >= 4900 else "2.4 GHz"
            except GLib.Error:
                pass
        devices.append({"path": path, "name": device["Name"], "powered": device.get("Powered", False),
                        "state": station.get("State", "off"), "scanning": station.get("Scanning", False),
                        "networks": networks, "details": details})
    return {"devices": devices}


def telemetry(interface):
    result = {}
    try:
        addresses = json.loads(subprocess.check_output(["ip", "-j", "-4", "addr", "show", "dev", interface], timeout=2))
        result["ip"] = next((a["local"] for link in addresses for a in link.get("addr_info", []) if a.get("scope") == "global"), "")
        routes = json.loads(subprocess.check_output(["ip", "-j", "-4", "route", "show", "default", "dev", interface], timeout=2))
        result["gateway"] = next((r["gateway"] for r in routes if r.get("gateway")), "")
    except (OSError, GLib.Error, subprocess.SubprocessError, ValueError):
        pass
    return result


def probe(interface):
    result = subprocess.run(["ping", "-n", "-I", interface, "-c", "2", "-W", "1", "1.1.1.1"],
                            capture_output=True, text=True, timeout=4, env={"PATH": "/usr/bin", "LC_ALL": "C"})
    loss = re.search(r"([\d.]+)% packet loss", result.stdout)
    timing = re.search(r"= [\d.]+/([\d.]+)/", result.stdout)
    return {"loss": float(loss[1]) if loss else None, "ping": float(timing[1]) if timing else None}


def connect(path, password, identity=""):
    # iwd asks the temporary agent for secrets on this same bus connection.
    xml = '''<node><interface name="net.connman.iwd.Agent">
      <method name="Release"/><method name="Cancel"><arg type="s" direction="in"/></method>
      <method name="RequestPassphrase"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
      <method name="RequestPrivateKeyPassphrase"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
      <method name="RequestUserNameAndPassword"><arg type="o" direction="in"/><arg type="s" direction="out"/><arg type="s" direction="out"/></method>
      <method name="RequestUserPassword"><arg type="o" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="out"/></method>
    </interface></node>'''
    def agent(connection, sender, object_path, interface, method, parameters, invocation):
        if method in ("Release", "Cancel"):
            invocation.return_value(None)
        elif method == "RequestPassphrase" and password:
            invocation.return_value(GLib.Variant("(s)", (password,)))
        elif method == "RequestUserNameAndPassword" and identity and password:
            invocation.return_value(GLib.Variant("(ss)", (identity, password)))
        elif method == "RequestUserPassword" and password:
            invocation.return_value(GLib.Variant("(s)", (password,)))
        else:
            invocation.return_dbus_error(PREFIX + "Error.Canceled", "Credentials required")

    agent_path = "/desktop_bar/wifi_agent"
    registration = bus.register_object(agent_path, Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0], agent, None, None)
    call("/net/connman/iwd", PREFIX + "AgentManager", "RegisterAgent", GLib.Variant("(o)", (agent_path,)))
    loop = GLib.MainLoop()
    errors = []
    def finished(connection, result):
        try:
            connection.call_finish(result)
        except GLib.Error as error:
            errors.append(error.message)
        loop.quit()
    try:
        bus.call(SERVICE, path, PREFIX + "Network", "Connect", None, None,
                 Gio.DBusCallFlags.NONE, 45000, None, finished)
        loop.run()
    finally:
        call("/net/connman/iwd", PREFIX + "AgentManager", "UnregisterAgent", GLib.Variant("(o)", (agent_path,)))
        bus.unregister_object(registration)
    if errors:
        raise RuntimeError(errors[0])


def connect_enterprise(path, request):
    """Write the iwd profile through the root helper, then connect with it."""
    if not NETWORK_HELPER.is_file() or NETWORK_HELPER.stat().st_uid != 0 or NETWORK_HELPER.stat().st_mode & 0o022:
        raise RuntimeError(tr('Install the Eitr network helper first; see distro/NETWORKING.md'))
    certificate = Path(request.get("ca", "")).expanduser().read_bytes()
    if len(certificate) > 65536:
        raise ValueError(tr('CA certificate is too large'))
    request = {**request, "certificate": base64.b64encode(certificate).decode()}
    result = subprocess.run(["pkexec", str(NETWORK_HELPER), "enterprise"], input=json.dumps(request) + "\n",
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Enterprise setup cancelled")
    # iwd loads the new profile through its directory watch, shortly after it is written.
    deadline = time.monotonic() + 3
    while True:
        try:
            connect(path, request["password"], request["identity"])
            return
        except RuntimeError as error:
            if "NotConfigured" not in str(error) or time.monotonic() > deadline:
                raise
        time.sleep(0.25)


def read_state(action="status", interface=""):
    """Shared read entry point for the CLI and broker."""
    if action == "probe":
        return probe(interface)
    backend = active_backend()
    if action == "icon":
        if backend == "networkmanager":
            adapter = NM_ADAPTER
            result = adapter.snapshot(bus, lambda interface: {})
        else:
            result = {**snapshot(include_details=False), "backend": "iwd"}
        radios = Path('/sys/class/rfkill')
        result["blocked"] = any(
            (radio / 'type').read_text().strip() == 'wlan' and (radio / 'state').read_text().strip() == '0'
            for radio in radios.glob('rfkill*'))
        result["wired"] = any(
            interface.name != 'lo' and not (interface / 'wireless').exists() and (interface / 'device').exists()
            and (interface / 'operstate').read_text().strip() == 'up'
            for interface in Path('/sys/class/net').iterdir())
        return result
    if backend == "networkmanager":
        adapter = NM_ADAPTER
        return adapter.snapshot(bus, telemetry)
    return {**snapshot(), "backend": "iwd"}


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action in ("icon", "status", "probe"):
        return read_state(action, sys.argv[2] if action == "probe" else "")
    backend = active_backend()
    if backend == "networkmanager":
        adapter = NM_ADAPTER
        request = json.loads(sys.stdin.readline()) if action == "connect" else None
        return adapter.action(bus, action, sys.argv[2], request, sys.argv[3] if len(sys.argv) > 3 else None)
    path = sys.argv[2]
    if action == "connect":
        request = json.loads(sys.stdin.readline())
        if request.get("identity"):
            connect_enterprise(path, request)
        else:
            connect(path, request.get("password", ""))
    elif action in ("scan", "disconnect"):
        call(path, PREFIX + "Station", action.capitalize())
    elif action == "forget":
        call(path, PREFIX + "KnownNetwork", "Forget")
    elif action == "power":
        call(path, "org.freedesktop.DBus.Properties", "Set",
             GLib.Variant("(ssv)", (PREFIX + "Device", "Powered", GLib.Variant("b", sys.argv[3] == "true"))))
    else:
        raise ValueError('Unknown action')
    return {"ok": True}


if __name__ == "__main__":
    try:
        print(json.dumps(main()))
    except (GLib.Error, RuntimeError, ValueError, IndexError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)}))
        sys.exit(1)
