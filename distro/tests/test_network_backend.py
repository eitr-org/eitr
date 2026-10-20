import base64
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("network_backend", ROOT / "distro/system/network-backend.py")
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)


class NetworkBackendTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name, value in {"ETC": root / "etc", "STATE": root / "state", "IWD": root / "iwd"}.items():
            replacement = patch.object(network, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        network.ETC.mkdir()
        (network.ETC / "resolv.conf").symlink_to("/run/systemd/resolve/stub-resolv.conf")
        self.commands = []

    def command(self, args, **kwargs):
        self.commands.append(args)
        if args[:2] == ["systemctl", "is-active"]:
            return subprocess.CompletedProcess(args, 3, "", "")
        if args[:2] == ["systemctl", "is-enabled"]:
            return subprocess.CompletedProcess(args, 0, "enabled\n" if args[2] != "NetworkManager.service" else "disabled\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    def test_switch_preserves_current_connection_and_original_configuration(self):
        with patch.object(network.subprocess, "run", side_effect=self.command):
            network.stage("networkmanager")
            original = (network.STATE / "original.json").read_text()
            network.stage("iwd")
            self.assertEqual((network.STATE / "original.json").read_text(), original)
        self.assertTrue(any(command == ["systemctl", "enable", "NetworkManager.service"] for command in self.commands))
        for command in self.commands:
            self.assertNotIn("--now", command)
            self.assertFalse(set(command) & {"stop", "restart", "start", "reload", "reboot"})
        self.assertIn("wifi.backend=wpa_supplicant", (network.ETC / network.FILES[0]).read_text())
        self.assertEqual((network.STATE / "original.json").stat().st_mode & 0o777, 0o600)

    def test_failure_rolls_back_files_and_service_enable_states(self):
        original = {"units": {unit: "disabled" for unit in network.UNITS},
                    "files": {name: None for name in network.FILES}}
        def run(args):
            if args == ["systemctl", "enable", "NetworkManager.service"]:
                raise subprocess.CalledProcessError(1, args)
        with patch.object(network.subprocess, "run", side_effect=self.command), patch.object(network, "capture", return_value=original), patch.object(network, "run", side_effect=run), self.assertRaises(subprocess.CalledProcessError):
            network.stage("networkmanager")
        self.assertFalse((network.ETC / network.FILES[0]).exists())
        self.assertFalse((network.STATE / "selected").exists())

    def test_custom_resolver_is_not_replaced(self):
        (network.ETC / "resolv.conf").unlink()
        (network.ETC / "resolv.conf").write_text("nameserver 192.0.2.1\n")
        with patch.object(network.subprocess, "run", side_effect=self.command), self.assertRaises(RuntimeError):
            network.stage("networkmanager")
        self.assertFalse(network.STATE.exists())

    def enterprise(self):
        return {"name": "Campus", "eap": "peap", "identity": "student", "password": "test secret",
                "domain": "radius.example.org", "certificate": base64.b64encode(
                    b"-----BEGIN CERTIFICATE-----\nQUJD\n-----END CERTIFICATE-----\n").decode()}

    def test_iwd_switch_installs_the_fresh_install_networkd_files_without_replacing_custom_ones(self):
        for name, content in network.NETWORKD_FILES.items():
            shipped = (ROOT / "distro/network" / name).read_text().splitlines()
            self.assertEqual([line for line in shipped if not line.startswith("#")], content.splitlines())
        custom = network.ETC / "systemd/network/20-ethernet.network"
        custom.parent.mkdir(parents=True)
        custom.write_text("[Match]\nType=ether\n\n[Network]\nAddress=192.0.2.10/24\n")
        with patch.object(network.subprocess, "run", side_effect=self.command):
            network.stage("iwd")
        self.assertIn("Address=192.0.2.10/24", custom.read_text())
        self.assertEqual((network.ETC / "systemd/network/20-wifi.network").read_text(),
                         network.NETWORKD_FILES["20-wifi.network"])

    def test_restore_without_a_switch_explains_that_nothing_changed(self):
        with patch("sys.argv", ["eitr-network", "restore"]), patch.object(network.os, "geteuid", return_value=0), \
                self.assertRaisesRegex(RuntimeError, "never switched"):
            network.main()

    def test_enterprise_profile_uses_the_file_name_iwd_reads(self):
        network.enterprise(self.enterprise())
        self.assertTrue((network.IWD / "Campus.8021x").exists())
        request = self.enterprise()
        request["name"] = "Café.Net"
        network.enterprise(request)
        self.assertTrue((network.IWD / ("=" + "Café.Net".encode().hex() + ".8021x")).exists())

    def test_enterprise_profile_is_private_and_has_ca_and_server_validation(self):
        network.enterprise(self.enterprise())
        path = next(network.IWD.glob("*.8021x"))
        text = path.read_text()
        self.assertIn("EAP-PEAP-ServerDomainMask=radius.example.org", text)
        self.assertIn("EAP-PEAP-CACert=embed:eitr_ca", text)
        self.assertIn("EAP-PEAP-Phase2-Method=MSCHAPV2", text)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(RuntimeError):
            network.enterprise(self.enterprise())

    def test_enterprise_rejects_injection_and_missing_validation(self):
        for key, value in (("identity", "user\n[Security]"), ("domain", ""), ("domain", "*.example.org"),
                           ("certificate", base64.b64encode(b"[Security]\nEAP-Method=PWD").decode())):
            request = self.enterprise()
            request[key] = value
            with self.assertRaises(ValueError):
                network.enterprise(request)
        self.assertFalse(network.IWD.exists())


if __name__ == "__main__":
    unittest.main()
