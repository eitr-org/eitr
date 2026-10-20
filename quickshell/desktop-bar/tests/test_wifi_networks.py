import importlib.util
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("wifi", Path(__file__).parents[1] / "scripts/wifi-popup.py")
wifi = importlib.util.module_from_spec(spec)
try:
    # wifi-popup.py connects to the system D-Bus at import time.
    spec.loader.exec_module(wifi)
except Exception as error:  # no gi or no system bus (CI containers, macOS)
    raise unittest.SkipTest(f"wifi-popup.py needs GObject and a system bus: {error}")


class KnownNetworkTests(unittest.TestCase):
    def setUp(self):
        self.saved = {"/known": {wifi.PREFIX + "KnownNetwork": {"Name": "Hotspot", "Type": "psk"}}}

    def test_offline_saved_network_remains(self):
        row = wifi.merge_known([], self.saved)[0]
        self.assertTrue(row["known"])
        self.assertFalse(row["available"])
        self.assertIsNone(row["strength"])
        self.assertEqual(row["knownPath"], "/known")

    def test_visible_saved_network_is_not_duplicated(self):
        visible = [{"name": "Hotspot", "type": "psk", "known": False, "connected": True, "strength": 80, "path": "/network"}]
        rows = wifi.merge_known(visible, self.saved)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["known"])
        self.assertTrue(rows[0]["available"])
        self.assertEqual(rows[0]["knownPath"], "/known")
        self.assertFalse(visible[0]["known"])

    def test_same_ssid_different_security_is_distinct(self):
        visible = [{"name": "Hotspot", "type": "open", "known": False, "connected": False, "strength": 80, "path": "/network"}]
        self.assertEqual(len(wifi.merge_known(visible, self.saved)), 2)


class EnterpriseConnectTests(unittest.TestCase):
    def test_connect_waits_for_iwd_to_load_the_new_profile(self):
        helper = Mock()
        helper.is_file.return_value = True
        helper.stat.return_value = SimpleNamespace(st_uid=0, st_mode=0o100755)
        attempts = []

        def connect(path, password, identity):
            attempts.append((path, password, identity))
            if len(attempts) == 1:
                raise RuntimeError("GDBus.Error:net.connman.iwd.NotConfigured: Not configured")

        with tempfile.NamedTemporaryFile() as certificate, patch.object(wifi, "NETWORK_HELPER", helper), \
                patch.object(wifi.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run, \
                patch.object(wifi, "connect", side_effect=connect), patch.object(wifi.time, "sleep"):
            wifi.connect_enterprise("/network", {"identity": "student", "password": "test secret", "ca": certificate.name})
        self.assertEqual(attempts, [("/network", "test secret", "student")] * 2)
        self.assertNotIn("test secret", " ".join(run.call_args.args[0]))

    def test_other_connect_errors_are_not_retried(self):
        helper = Mock()
        helper.is_file.return_value = True
        helper.stat.return_value = SimpleNamespace(st_uid=0, st_mode=0o100755)
        with tempfile.NamedTemporaryFile() as certificate, patch.object(wifi, "NETWORK_HELPER", helper), \
                patch.object(wifi.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")), \
                patch.object(wifi, "connect", side_effect=RuntimeError("Failed")) as connect, \
                self.assertRaises(RuntimeError):
            wifi.connect_enterprise("/network", {"identity": "student", "password": "test secret", "ca": certificate.name})
        self.assertEqual(connect.call_count, 1)


class PanelDetailsTests(unittest.TestCase):
    def test_the_panel_shows_ping_band_address_and_gateway_only(self):
        qml = (Path(__file__).parents[1] / "WifiMenu.qml").read_text()
        self.assertIn('["Ping", menu.latency.ping != null', qml)
        self.assertIn('"Wi-Fi Band", menu.details.band', qml)
        self.assertIn('["IP Address", menu.details.ip || "--", "Gateway", menu.details.gateway || "--"]', qml)
        for removed in ("Packet Loss", "Receiving", "Downloaded", "WI-FI BAND", "AUTOMATIC"):
            self.assertNotIn(removed, qml)
