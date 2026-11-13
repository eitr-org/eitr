"""The login screen runs its design on one display only: the largest, black elsewhere."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def main_display(name, screens):
    script = (ROOT / "login/LoginDisplay.js").read_text().replace(".pragma library", "")
    call = f"console.log(JSON.stringify(isMain({json.dumps(name)}, {json.dumps(screens)})));"
    result = subprocess.run(["node", "-e", script + "\n" + call], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def screen(name, width, height, x=0, y=0):
    return {"name": name, "width": width, "height": height, "virtualX": x, "virtualY": y}


@unittest.skipUnless(shutil.which("node"), "node required")
class LoginDisplayTests(unittest.TestCase):
    def test_the_largest_display_shows_the_login_screen(self):
        screens = [screen("HDMI-A-1", 1920, 1080, 320, 1080), screen("DP-3", 2560, 1080)]
        self.assertTrue(main_display("DP-3", screens))
        self.assertFalse(main_display("HDMI-A-1", screens))

    def test_ties_go_left_then_up(self):
        screens = [screen("RIGHT", 1920, 1080, 1920), screen("LEFT", 1920, 1080, 0)]
        self.assertTrue(main_display("LEFT", screens))
        self.assertFalse(main_display("RIGHT", screens))
        stacked = [screen("LOWER", 1920, 1080, 0, 1080), screen("UPPER", 1920, 1080, 0, 0)]
        self.assertTrue(main_display("UPPER", stacked))

    def test_it_never_leaves_every_display_black(self):
        self.assertTrue(main_display("ONLY", [screen("ONLY", 1920, 1080)]))
        self.assertTrue(main_display("", [screen("A", 1920, 1080), screen("B", 2560, 1440)]))
        self.assertTrue(main_display("UNKNOWN", [screen("A", 1920, 1080), screen("B", 2560, 1440)]))
        self.assertTrue(main_display("A", []))


class StagedLoginTests(unittest.TestCase):
    def test_every_staged_design_runs_behind_the_display_wrapper(self):
        spec = importlib.util.spec_from_file_location("install_login", ROOT / "scripts/install-login.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as directory:
            manifest = installer.stage(Path(directory))
            for design, theme in manifest.items():
                staged = Path(directory) / "usr/share/sddm/themes" / theme
                self.assertEqual((staged / "Main.qml").read_text(), (ROOT / "login/Main.qml").read_text(), design)
                self.assertTrue((staged / "LoginDisplay.js").is_file(), design)
                self.assertTrue((staged / "Design.qml").is_file(), design)
                self.assertIn("MainScript=Main.qml", (staged / "metadata.desktop").read_text(), design)
        wrapper = (ROOT / "login/Main.qml").read_text()
        self.assertIn('source: "Design.qml"', wrapper)
        self.assertIn("active: display.main", wrapper)
        # Decided once the window is shown on its display, and the keyboard follows it there.
        self.assertIn("Window.window.visible", wrapper)
        self.assertIn("requestActivate()", wrapper)
        # Designs pass focus to their password field only when their root gains it.
        self.assertIn("onLoaded: item.forceActiveFocus()", wrapper)
        self.assertIn("design.item.forceActiveFocus()", wrapper)


if __name__ == "__main__":
    unittest.main()
