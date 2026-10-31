import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/actions/toggle/game-mode.sh"


class GameModeTests(unittest.TestCase):
    """The toggle against stand-in tools: never the live compositor, bar or power profile."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.calls = self.folder / "calls"
        (self.folder / "dnd").write_text("false")
        (self.folder / "profile").write_text("balanced")
        tools = {
            "hyprctl": 'echo "hyprctl $*" >> "{calls}"',
            "eitr-shell": ('echo "eitr-shell $*" >> "{calls}"\n'
                           'if [ "$6" = status ]; then echo "{{\\"doNotDisturb\\": $(cat {folder}/dnd)}}"; fi\n'
                           'if [ "$6" = dnd ]; then if [ "$(cat {folder}/dnd)" = true ]; then echo false > {folder}/dnd; '
                           'else echo true > {folder}/dnd; fi; fi'),
            "powerprofilesctl": ('echo "powerprofilesctl $*" >> "{calls}"\n'
                                 'if [ "$1" = get ]; then cat {folder}/profile; else echo "$2" > {folder}/profile; fi'),
            "notify-send": 'echo "notify-send $*" >> "{calls}"',
        }
        for name, body in tools.items():
            tool = self.folder / name
            tool.write_text("#!/bin/sh\n" + body.format(calls=self.calls, folder=self.folder) + "\n")
            tool.chmod(0o755)
        self.environment = {**os.environ, "PATH": f"{self.folder}:{os.environ['PATH']}",
                            "XDG_RUNTIME_DIR": str(self.folder), "EITR_CODE_ROOT": str(ROOT)}

    def toggle(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args], env=self.environment, check=True,
                              capture_output=True, text=True).stdout.strip()

    def calls_made(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def test_on_turns_effects_notifications_and_power_to_gaming(self):
        self.toggle("on")
        calls = self.calls_made()
        self.assertIn("animations = { enabled = false }", calls)
        self.assertIn("blur = { enabled = false }", calls)
        self.assertEqual((self.folder / "dnd").read_text().strip(), "true")
        self.assertEqual((self.folder / "profile").read_text().strip(), "performance")
        self.assertEqual(self.toggle("status"), "on")
        self.assertEqual(json.loads((self.folder / "eitr-game-mode.json").read_text()),
                         {"dnd": True, "profile": "balanced"})

    def test_off_restores_exactly_what_on_changed(self):
        self.toggle("on")
        self.toggle("off")
        self.assertIn("hyprctl reload", self.calls_made())
        self.assertEqual((self.folder / "dnd").read_text().strip(), "false")
        self.assertEqual((self.folder / "profile").read_text().strip(), "balanced")
        self.assertEqual(self.toggle("status"), "off")

    def test_settings_already_in_place_are_left_alone(self):
        (self.folder / "dnd").write_text("true")
        (self.folder / "profile").write_text("performance")
        self.toggle("on")
        self.toggle("off")
        self.assertEqual((self.folder / "dnd").read_text().strip(), "true", "do not disturb was the user's")
        self.assertEqual((self.folder / "profile").read_text().strip(), "performance")

    def test_toggle_alternates_and_repeated_on_does_nothing(self):
        self.toggle()
        self.toggle("on")
        self.assertEqual(self.calls_made().count("hyprctl eval"), 1)
        self.toggle()
        self.assertEqual(self.toggle("status"), "off")

    def test_menu_and_steam_offer_it(self):
        menu = {"entries": json.loads((ROOT / "elephant/menu-rows/toggle.json").read_text())}
        names = [entry["text"] for entry in menu["entries"]]
        self.assertIn("Game Mode", names)
        self.assertEqual(names, sorted(names, key=str.casefold))
        panels = ROOT / "quickshell/desktop-bar/panels"
        center = (panels / "ControlCenter.qml").read_text() + (panels / "ControlCenterConnectivity.qml").read_text()
        self.assertIn('title: Eitr.I18n.tr("Game Mode")', center)
        self.assertIn('command: ["bash", center.gameModeScript, "toggle"]', center)
        self.assertIn('command: ["bash", center.gameModeScript, "status"]', center)
        steam = json.loads((ROOT / "distro/software.json").read_text())["gaming"]["steam"]["packages"]
        for package in ("gamemode", "lib32-gamemode", "mangohud", "lib32-mangohud"):
            self.assertIn(package, steam)


if __name__ == "__main__":
    unittest.main()
