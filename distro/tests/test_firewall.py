import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
ROOT = DISTRO.parent
RULES = DISTRO / "system/firewall.nft"
spec = importlib.util.spec_from_file_location("eitr_system_firewall", DISTRO / "system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)


def in_network_namespace(script):
    """Run nft in a throwaway user and network namespace; None when unavailable (CI containers)."""
    if not shutil.which("nft") or not shutil.which("unshare"):
        return None
    result = subprocess.run(["unshare", "-rn", "sh", "-c", script], capture_output=True, text=True)
    if "Operation not permitted" in result.stderr or "unshare failed" in result.stderr:
        return None
    return result


class FirewallRulesTests(unittest.TestCase):
    def test_incoming_is_refused_except_replies_and_the_sharing_apps(self):
        rules = RULES.read_text()
        self.assertIn("policy drop;", rules)
        self.assertIn("ct state established,related accept", rules)
        for opening in ("tcp dport 1714-1764 accept", "udp dport 1714-1764 accept",
                        "tcp dport 53317 accept", "udp dport 53317 accept",
                        "meta l4proto { icmp, ipv6-icmp } accept", 'iifname { "virbr*", "docker*", "br-*" } accept'):
            self.assertIn(opening, rules)
        self.assertNotIn("dport 22 ", rules, "SSH opens only when sshd is enabled")
        self.assertNotIn("hook output", rules, "outgoing traffic is never filtered")

    def test_the_rules_load_and_reload_with_local_openings(self):
        with tempfile.TemporaryDirectory() as directory:
            openings = Path(directory) / "firewall.d"
            openings.mkdir()
            (openings / "ssh.nft").write_text(system.SSH_OPENING)
            rules = Path(directory) / "firewall.nft"
            # Never the machine's own files: the sharing guard comes from the temporary folder too.
            rules.write_text(RULES.read_text().replace("/etc/eitr/firewall.d", str(openings))
                             .replace("/etc/eitr/remote-access", str(Path(directory) / "remote-access")))
            result = in_network_namespace(f"nft -f {rules} && nft -f {rules} && nft list ruleset")
            if result is None:
                self.skipTest("unprivileged network namespaces are unavailable")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("tcp dport 22 accept"), 1, "reloading replaces, never duplicates")

    def test_the_unit_and_package_agree_on_the_rules_path(self):
        unit = (DISTRO / "system/eitr-firewall.service").read_text()
        self.assertIn("ExecStart=/usr/bin/nft -f /usr/share/eitr/firewall.nft", unit)
        self.assertIn("Before=network-pre.target", unit)
        pkgbuild = (DISTRO / "pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn('install -Dm644 distro/system/firewall.nft "$pkgdir/usr/share/eitr/firewall.nft"', pkgbuild)
        self.assertIn("distro/system/eitr-firewall.service", pkgbuild)
        self.assertIn("nftables", (DISTRO / "packages.txt").read_text().split())

    def test_new_installations_start_with_it_on(self):
        self.assertIn("systemctl enable eitr-firewall.service", (DISTRO / "system/configure-desktop.sh").read_text())
        installer = (DISTRO / "archinstall/eitr-guided-install").read_text()
        self.assertIn('chroot(["/usr/lib/eitr/eitr-system", "firewall-allow-ssh"], log)', installer)


class FirewallActionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.openings = Path(directory.name) / "firewall.d"
        self.rules = Path(directory.name) / "firewall.nft"
        self.rules.write_text("table inet eitr_firewall {}\n")
        for name, value in (("FIREWALL_OPENINGS", self.openings), ("FIREWALL_RULES", self.rules)):
            patcher = patch.object(system, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.commands = []
        for name in ("run",):
            patcher = patch.object(system, name, side_effect=lambda args, **kwargs: self.commands.append(args))
            patcher.start()
            self.addCleanup(patcher.stop)

    def turn_on(self, sshd_enabled):
        with patch.object(system, "unit_enabled", return_value=sshd_enabled), \
                patch.object(system, "in_chroot", return_value=False), patch("builtins.print"):
            system.firewall_on()

    def test_turning_it_on_keeps_ssh_reachable_when_sshd_is_enabled(self):
        self.turn_on(sshd_enabled=True)
        self.assertEqual((self.openings / "ssh.nft").read_text(), system.SSH_OPENING)
        self.assertIn(["systemctl", "enable", system.FIREWALL_UNIT], self.commands)
        self.assertIn(["systemctl", "reload-or-restart", system.FIREWALL_UNIT], self.commands)

    def test_without_sshd_no_port_is_opened(self):
        self.turn_on(sshd_enabled=False)
        self.assertFalse((self.openings / "ssh.nft").exists())

    def test_it_refuses_without_the_packaged_rules(self):
        self.rules.unlink()
        with self.assertRaisesRegex(RuntimeError, "is missing"):
            self.turn_on(sshd_enabled=False)

    def test_status_reports_openings_and_exit_code(self):
        self.openings.mkdir()
        (self.openings / "ssh.nft").write_text(system.SSH_OPENING)
        with patch.object(system.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)), \
                patch("builtins.print") as printed:
            self.assertEqual(system.firewall_status(), 0)
        self.assertEqual(printed.call_args.args[0], "Firewall: on (also open: ssh)")
        with patch.object(system.subprocess, "run", return_value=subprocess.CompletedProcess([], 3)), \
                patch("builtins.print"):
            self.assertEqual(system.firewall_status(), 3)


class FirewallMenuTests(unittest.TestCase):
    def test_security_menu_offers_the_firewall_in_order(self):
        rows = json.loads((ROOT / "elephant/menu-rows/security.json").read_text())
        names = [row["text"] for row in rows]
        row = next(row for row in rows if row["text"] == "Firewall")
        self.assertIn("walker/scripts/actions/system/firewall.py", row["actions"]["open"])
        script = (ROOT / "walker/scripts/actions/system/firewall.py").read_text()
        self.assertIn("[y/N]", script)
        self.assertIn('if answer not in ("y", "yes"):', script)


if __name__ == "__main__":
    unittest.main()
