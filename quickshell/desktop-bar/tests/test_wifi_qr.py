import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("wifi_qr", Path(__file__).parents[1] / "scripts/wifi-qr.py")
qr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qr)


class WifiQrTests(unittest.TestCase):
    def test_secure_network_escapes_reserved_characters(self):
        self.assertEqual(qr.payload({"name": "A;B", "type": "psk"}, 'p:q\\r'),
                         'WIFI:T:WPA;S:A\\;B;P:p\\:q\\\\r;;')

    def test_open_network_needs_no_password(self):
        self.assertEqual(qr.payload({"name": "Guest", "type": "open"}, ""),
                         "WIFI:T:nopass;S:Guest;P:;;")

    def test_password_and_enterprise_restrictions(self):
        with self.assertRaises(ValueError):
            qr.payload({"name": "Home", "type": "psk"}, "")
        with self.assertRaises(ValueError):
            qr.payload({"name": "Office", "type": "8021x"}, "secret")
