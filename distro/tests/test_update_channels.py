import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eitr_system_channels", DISTRO / "system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)

PACMAN_CONF = """[options]
HoldPkg = pacman glibc

[core]
Include = /etc/pacman.d/mirrorlist

[eitr]
SigLevel = Required
Server = https://download.eitr.info/repo

[extra]
Include = /etc/pacman.d/mirrorlist
"""


class UpdateChannelTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.conf = Path(directory.name) / "pacman.conf"
        self.conf.write_text(PACMAN_CONF)
        patcher = patch("builtins.print")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_testing_check_names_a_user_agent_cloudflare_accepts(self):
        with patch("urllib.request.urlopen", side_effect=OSError("offline")) as urlopen:
            self.assertFalse(system.testing_reachable())
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "HEAD")
        self.assertNotIn("Python-urllib", request.get_header("User-agent"))

    def test_testing_is_listed_right_before_stable(self):
        system.channel_set("testing", self.conf, reachable=lambda: True)
        text = self.conf.read_text()
        self.assertEqual(system.channel_status(self.conf), "testing")
        self.assertLess(text.index("[eitr-testing]"), text.index("[eitr]\n"))
        self.assertGreater(text.index("[eitr-testing]"), text.index("[core]"))
        self.assertIn("Server = https://download.eitr.info/repo-testing", text)

    def test_switching_back_restores_the_file_exactly(self):
        system.channel_set("testing", self.conf, reachable=lambda: True)
        system.channel_set("testing", self.conf, reachable=lambda: True)
        self.assertEqual(self.conf.read_text().count("[eitr-testing]"), 1, "switching twice adds nothing")
        system.channel_set("stable", self.conf)
        self.assertEqual(self.conf.read_text(), PACMAN_CONF)
        self.assertEqual(system.channel_status(self.conf), "stable")

    def test_an_unreachable_testing_repository_changes_nothing(self):
        with self.assertRaisesRegex(RuntimeError, "cannot be reached"):
            system.channel_set("testing", self.conf, reachable=lambda: False)
        self.assertEqual(self.conf.read_text(), PACMAN_CONF)
        system.channel_set("stable", self.conf, reachable=lambda: False)

    def test_stable_publishes_also_fill_testing(self):
        release = (DISTRO / "repo/release-desktop.py").read_text()
        self.assertIn('if channel == "stable" and not arguments.promote:', release)
        self.assertIn('"--key", key, "--channel", "testing"]', release)

    def test_a_system_without_eitrs_repository_is_refused(self):
        self.conf.write_text("[core]\nInclude = /etc/pacman.d/mirrorlist\n")
        with self.assertRaisesRegex(RuntimeError, "no \\[eitr\\] repository"):
            system.channel_set("testing", self.conf, reachable=lambda: True)

    def test_publishing_targets_each_channels_repository(self):
        publish = (DISTRO / "repo/publish.py").read_text()
        self.assertIn('CHANNELS = {"stable": ("repo", "eitr"), "testing": ("repo-testing", "eitr-testing")}', publish)
        release = (DISTRO / "repo/release-desktop.py").read_text()
        self.assertIn('"--channel", channel]', release)
        self.assertIn("--promote", release)
        self.assertIn('if channel == "stable":\n            reuse_published_packages', release,
                      "testing carries only Eitr's own new builds")

    def test_menu_and_command_offer_it(self):
        rows = json.loads((DISTRO.parent / "elephant/menu-rows/system.json").read_text())
        names = [row["text"] for row in rows]
        self.assertIn("Update Channel", names)
        row = next(row for row in rows if row["text"] == "Update Channel")
        self.assertEqual(row["submenu"], "update-channel")
        menu = (DISTRO.parent / "elephant/menus/update-channel.lua").read_text()
        self.assertIn('Parent = "system"', menu)
        self.assertIn('" set " .. channel.name', menu)
        self.assertIn('if not active then', menu, "the current channel opens nothing")
        script = (DISTRO.parent / "walker/scripts/actions/system/update-channel.py").read_text()
        self.assertIn('["sudo", HELPER, "channel-set", channel]', script)
        self.assertIn('"channel-set", arguments.name', (DISTRO / "bin/eitr").read_text())


if __name__ == "__main__":
    unittest.main()
