import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
LID = ROOT / "hypr/scripts/lid.sh"


class LidTests(unittest.TestCase):
    """The lid script against a stand-in hyprctl: never the live compositor."""

    def lid(self, action, monitors):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "monitors.json").write_text(json.dumps([{"name": name} for name in monitors]))
            hyprctl = folder / "hyprctl"
            hyprctl.write_text(f'#!/bin/sh\nif [ "$1" = monitors ]; then cat "{folder}/monitors.json"; '
                               f'else echo "$@" >> "{folder}/calls"; fi\n')
            hyprctl.chmod(0o755)
            subprocess.run(["bash", str(LID), action], check=True,
                           env={**os.environ, "PATH": f"{folder}:{os.environ['PATH']}"})
            return (folder / "calls").read_text() if (folder / "calls").exists() else ""

    def test_closing_with_an_external_monitor_turns_the_laptop_screen_off(self):
        self.assertIn('hl.monitor({ output = "eDP-1", disabled = true })', self.lid("close", ["eDP-1", "HDMI-A-1"]))

    def test_closing_without_one_leaves_suspend_to_logind(self):
        self.assertEqual(self.lid("close", ["eDP-1"]), "")
        self.assertEqual(self.lid("close", ["DP-3"]), "", "a desktop has no laptop screen to turn off")

    def test_opening_restores_the_configured_displays(self):
        self.assertEqual(self.lid("open", ["HDMI-A-1"]).strip(), "reload")


class LaptopWiringTests(unittest.TestCase):
    def test_keys_lid_and_battery_warnings_are_wired(self):
        hypr = (ROOT / "hypr/hyprland.lua").read_text()
        self.assertIn('hl.bind("XF86KbdBrightnessUp"', hypr)
        self.assertIn('hl.bind("switch:on:Lid Switch"', hypr)
        self.assertIn('hl.bind("switch:off:Lid Switch"', hypr)
        shell = (ROOT / "quickshell/desktop-bar/services/SessionHooks.qml").read_text()
        self.assertIn('"Battery almost empty"', shell)
        self.assertIn("host.battery.percent <= 5 ? 5 : host.battery.percent <= 10 ? 10 : 0", shell)
        self.assertIn("systemctl enable thermald.service", (ROOT / "distro/system/configure-desktop.sh").read_text())


if __name__ == "__main__":
    unittest.main()
