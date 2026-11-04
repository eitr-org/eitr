"""toggle/desktop-bar.sh: the menu row shows or hides the bar; SUPER + Shift + Space switches auto-hide."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "walker/scripts/actions/toggle/desktop-bar.sh"


class BarToggleTests(unittest.TestCase):
    def run_script(self, *arguments, running=True):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            calls = folder / "calls"
            listing = "Config path: /usr/share/eitr/quickshell/desktop-bar/shell.qml" if running else ""
            (folder / "quickshell").write_text(f"#!/bin/sh\necho '{listing}'\n")
            (folder / "eitr-shell").write_text(f'#!/bin/sh\necho "$*" >> "{calls}"\n')
            for name in ("quickshell", "eitr-shell"):
                (folder / name).chmod(0o755)
            environment = {**os.environ, "PATH": f"{folder}:{os.environ['PATH']}"}
            subprocess.run(["bash", str(SCRIPT), *arguments], env=environment, check=True)
            return calls.read_text().splitlines()

    def test_the_menu_row_shows_or_hides_the_bar(self):
        self.assertEqual(self.run_script(), ["desktop-bar ipc call -- bar visibility"])

    def test_the_shortcut_switches_auto_hide(self):
        self.assertEqual(self.run_script("autohide"), ["desktop-bar ipc call -- bar toggle autohide"])

    def test_a_bar_that_is_not_running_starts(self):
        for arguments in ((), ("autohide",)):
            with self.subTest(arguments=arguments):
                self.assertEqual(self.run_script(*arguments, running=False), ["desktop-bar --daemonize"])

    def test_the_bar_brings_a_hidden_bar_back_before_switching_auto_hide(self):
        source = (ROOT / "quickshell/desktop-bar/services/BarPreferences.qml").read_text()
        handler = source[source.index('kind === "autohide"'):]
        handler = handler[:handler.index("}") + 1]
        self.assertIn("if (!host.barVisible) host.barVisible = true;", handler)
        self.assertIn('updateBarSetting(kind, host.barAutoHide ? "no" : "yes")', handler)
        self.assertIn('desktop-bar.sh autohide"', (ROOT / "hypr/hyprland.lua").read_text())


if __name__ == "__main__":
    unittest.main()
