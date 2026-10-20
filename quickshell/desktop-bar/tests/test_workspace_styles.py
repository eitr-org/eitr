from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / "quickshell/desktop-bar"
STYLES = ["Dots", "Glyph", "Numbers", "Runes"]


class WorkspaceStyleTests(unittest.TestCase):
    def test_every_style_list_offers_the_same_styles(self):
        lists = {
            "ControlCenter.qml": BAR / "ControlCenter.qml",
            "WorkspaceStyleMenu.qml": BAR / "WorkspaceStyleMenu.qml",
            "handbook-controls-preview.qml": BAR / "handbook-controls-preview.qml",
        }
        for name, path in lists.items():
            with self.subTest(file=name):
                self.assertIn('["Dots", "Glyph", "Numbers", "Runes"]', path.read_text())
        self.assertIn('{"Dots", "Glyph", "Numbers", "Runes"}', (ROOT / "elephant/menus/workspaces.lua").read_text())
        for script in ("workspace-style.py", "workspace-color.py"):
            with self.subTest(file=script):
                self.assertIn("('Dots', 'Glyph', 'Numbers', 'Runes')", (BAR / "scripts" / script).read_text())

    def test_styles_are_alphabetical_and_the_menu_fits_them_all(self):
        self.assertEqual(STYLES, sorted(STYLES))
        menu = (BAR / "WorkspaceStyleMenu.qml").read_text()
        self.assertIn("implicitHeight: styles.length * PanelStyle.selectionRowHeight", menu)
        self.assertIn("model: menu.styles", menu)

    def test_runes_cover_all_ten_workspaces_in_futhark_order(self):
        marker = (BAR / "WorkspaceMarker.qml").read_text()
        runes = re.search(r'readonly property var runes: \[(.*?)\]', marker)[1]
        self.assertEqual(re.findall(r'"(.)"', runes), list("ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾ"))
        self.assertIn('"Noto Sans Runic"', marker)
        self.assertIn("noto-fonts", (ROOT / "distro/packages.txt").read_text().split())

    def test_runes_are_the_default_when_nothing_is_saved(self):
        import json
        import os
        import subprocess
        import tempfile
        defaults = json.loads((ROOT / "distro/defaults/quickshell/desktop-bar/workspace-style.json").read_text())
        self.assertEqual(defaults["style"], "Runes")
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run([sys.executable, str(BAR / "scripts/workspace-style.py"), "current"],
                                    env={**os.environ, "HOME": home, "XDG_CONFIG_HOME": home + "/.config"},
                                    capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), "Runes")
        self.assertIn('local current = "Runes"', (ROOT / "elephant/menus/workspaces.lua").read_text())
        self.assertIn('property string workspaceStyle: "Runes"', (BAR / "shell.qml").read_text())


if __name__ == "__main__":
    unittest.main()
