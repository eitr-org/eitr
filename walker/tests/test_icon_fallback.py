"""The theme's icons fall back to Breeze, so KDE-style apps never show empty buttons."""
import configparser
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/themes/system.sh"


class IconFallbackTests(unittest.TestCase):
    def run_script(self, light=False):
        folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        config, data, tools = folder / "config", folder / "data", folder / "bin"
        current = config / "theme/current"
        current.mkdir(parents=True)
        (current / "icons.theme").write_text("Yaru-blue\n")
        (current / "dolphin.theme").write_text("example\n")
        if light:
            (current / "light.mode").write_text("")
        kvantum = config / "Kvantum/example"
        kvantum.mkdir(parents=True)
        (kvantum / "example.kvconfig").write_text("[%General]\n")
        tools.mkdir()
        # Stand-ins record what the script asks the desktop to use.
        for name in ("kwriteconfig6", "gsettings"):
            tool = tools / name
            tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{folder}/calls"\n')
            tool.chmod(0o755)
        environment = dict(os.environ, HOME=str(folder), XDG_CONFIG_HOME=str(config),
                           XDG_DATA_HOME=str(data), PATH=f"{tools}:{os.environ['PATH']}")
        subprocess.run(["bash", str(SCRIPT)], env=environment, check=True, capture_output=True)
        return folder, config, data

    def test_apps_use_a_theme_that_falls_back_to_breeze(self):
        folder, config, data = self.run_script()
        theme = configparser.ConfigParser(interpolation=None)
        theme.read(data / "icons/eitr-current/index.theme")
        self.assertEqual(theme["Icon Theme"]["Inherits"], "Yaru-blue,breeze-dark,breeze,hicolor")
        self.assertEqual(theme["Icon Theme"]["Hidden"], "true")
        for settings in (config / "qt6ct/qt6ct.conf", config / "qt5ct/qt5ct.conf"):
            self.assertIn("icon_theme=eitr-current", settings.read_text())
        for settings in (config / "gtk-3.0/settings.ini", config / "gtk-4.0/settings.ini"):
            self.assertIn("gtk-icon-theme-name=eitr-current", settings.read_text())
        calls = (folder / "calls").read_text()
        self.assertIn("--group Icons --key Theme eitr-current", calls)
        self.assertIn("icon-theme eitr-current", calls)

    def test_light_themes_fall_back_to_light_breeze(self):
        _, _, data = self.run_script(light=True)
        text = (data / "icons/eitr-current/index.theme").read_text()
        self.assertIn("Inherits=Yaru-blue,breeze,hicolor", text)


if __name__ == "__main__":
    unittest.main()
