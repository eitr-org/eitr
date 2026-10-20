import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("wifi_nm", Path(__file__).parents[1] / "scripts/wifi-networkmanager.py")
nm = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(nm)
except ImportError as error:
    raise unittest.SkipTest(f"GObject required: {error}")


class NetworkManagerTests(unittest.TestCase):
    def test_security_types_do_not_treat_encrypted_networks_as_open(self):
        for flags, kind in ((0, "open"), (0x100, "psk"), (0x200, "8021x"), (0x400, "sae"), (0x800, "unsupported")):
            self.assertEqual(nm.security({"RsnFlags": flags}), kind)
        self.assertEqual(nm.security({"Flags": 1}), "unsupported")
        self.assertEqual(nm.security({"RsnFlags": 0x100 | 0x400}), "psk")

    def test_credentials_are_typed_dbus_values_not_command_arguments(self):
        settings = nm.connection_settings("Cafe", "psk", {"password": "test secret"})
        self.assertEqual(settings["802-11-wireless-security"]["psk"].unpack(), "test secret")
        self.assertEqual(settings["802-11-wireless"]["ssid"].unpack(), list(b"Cafe"))

    def test_enterprise_requires_ca_and_domain_and_sets_validation(self):
        with self.assertRaises(ValueError):
            nm.connection_settings("Campus", "8021x", {"identity": "student", "password": "test secret"})
        with tempfile.NamedTemporaryFile() as certificate:
            request = {"identity": "student", "password": "test secret", "ca": certificate.name,
                       "domain": "radius.example.org", "eap": "ttls"}
            eap = nm.connection_settings("Campus", "8021x", request)["802-1x"]
            self.assertEqual(eap["phase2-auth"].unpack(), "pap")
            self.assertEqual(eap["domain-suffix-match"].unpack(), "radius.example.org")
            self.assertTrue(bytes(eap["ca-cert"].unpack()).endswith(b"\0"))
            self.assertNotIn("anonymous-identity", eap)
            request["anonymous"] = "anonymous@example.org"
            eap = nm.connection_settings("Campus", "8021x", request)["802-1x"]
            self.assertEqual(eap["anonymous-identity"].unpack(), "anonymous@example.org")

    def test_snapshot_keeps_offline_profiles_and_deduplicates_access_points(self):
        def properties(bus, path, interface):
            return {
                (nm.ROOT, nm.SERVICE): {"Devices": ["/device"], "WirelessEnabled": True},
                ("/device", nm.SERVICE + ".Device"): {"DeviceType": 2, "Interface": "test0", "State": 100},
                ("/device", nm.SERVICE + ".Device.Wireless"): {"AccessPoints": ["/weak", "/active"], "ActiveAccessPoint": "/active"},
                ("/weak", nm.SERVICE + ".AccessPoint"): {"Ssid": b"Cafe", "RsnFlags": 0x100, "Strength": 20},
                ("/active", nm.SERVICE + ".AccessPoint"): {"Ssid": b"Cafe", "RsnFlags": 0x100, "Strength": 80, "Frequency": 5180},
            }[(path, interface)]
        with patch.object(nm, "profiles", return_value={("Cafe", "psk"): "/saved", ("Home", "psk"): "/home"}), patch.object(nm, "properties", side_effect=properties):
            device = nm.snapshot(None, lambda interface: {})["devices"][0]
        self.assertEqual(len(device["networks"]), 2)
        self.assertTrue(device["networks"][0]["connected"])
        self.assertEqual(device["networks"][0]["path"], "/active")
        self.assertFalse(device["networks"][1]["available"])
        self.assertIsNone(device["networks"][1]["strength"])
        self.assertEqual(device["details"]["band"], "5 GHz")


if __name__ == "__main__":
    unittest.main()
