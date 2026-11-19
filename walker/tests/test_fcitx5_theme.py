"""fcitx5 classicui theme generation from Eitr theme colors and font preference."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from home_isolation import setUpModule, tearDownModule  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/themes/fcitx5.py"

DARK_PALETTE = """mode = "dark"
background = "#000000"
surface = "#0b110e"
foreground = "#e2eae2"
muted = "#91a397"
accent = "#b9d77e"
"""

LIGHT_PALETTE = """mode = "light"
background = "#f1f6f1"
surface = "#e3ede7"
foreground = "#17291e"
muted = "#404d43"
accent = "#3e5212"
"""


class Fcitx5ThemeTests(unittest.TestCase):
    def run_generator(self, root, *args):
        env = {key: value for key, value in os.environ.items() if not key.startswith("XDG_")}
        packaged = root / "packaged-theme"
        packaged.mkdir(exist_ok=True)
        (packaged / "prev.svg").write_text("<svg/>\n")
        (packaged / "next.svg").write_text("<svg/>\n")
        env.update(
            HOME=str(root),
            XDG_CONFIG_HOME=str(root / "config"),
            XDG_DATA_HOME=str(root / "data"),
            XDG_STATE_HOME=str(root / "state"),
            EITR_NO_SESSION="1",
            EITR_FCITX5_PACKAGED_THEME=str(packaged),
        )
        subprocess.run(["python3", str(SCRIPT), *args], env=env, check=True, timeout=20)
        return root / "data/fcitx5/themes/eitr/theme.conf", root / "config/fcitx5/conf/classicui.conf"

    def test_generates_dark_and_light_themes_with_contrast_and_font(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            theme_dir = root / "config/theme/current"
            theme_dir.mkdir(parents=True)
            (theme_dir / "colors.toml").write_text(DARK_PALETTE)
            (root / "config/eitr").mkdir(parents=True)
            (root / "config/eitr/font.json").write_text(json.dumps({"version": 1, "family": "Noto Sans"}))

            theme_conf, classicui = self.run_generator(root, "--activate")
            text = theme_conf.read_text()
            self.assertIn("Name=Eitr\n", text)
            self.assertIn("NormalColor=#e2eae2\n", text)
            self.assertIn("HighlightCandidateColor=#000000\n", text)
            self.assertIn("HighlightBackgroundColor=#b9d77e\n", text)
            self.assertIn("Color=#0b110e\nBorderColor=#b9d77e\n", text)
            self.assertIn("Color=#91a397\n", text)
            self.assertTrue((theme_conf.parent / "prev.svg").is_symlink())
            self.assertIn("Theme=eitr\n", classicui.read_text())
            self.assertIn("DarkTheme=eitr\n", classicui.read_text())
            self.assertIn('Font="Noto Sans 11"\n', classicui.read_text())

            # Switching to a light theme regenerates readable highlight text and preserves custom Theme if chosen.
            classicui.write_text("Theme=custom-theme\nDarkTheme=default-dark\nFont=\"Old 10\"\n")
            (theme_dir / "colors.toml").write_text(LIGHT_PALETTE)
            self.run_generator(root)
            light_text = theme_conf.read_text()
            self.assertIn("NormalColor=#17291e\n", light_text)
            self.assertIn("HighlightCandidateColor=#f1f6f1\n", light_text)
            self.assertIn("Color=#e3ede7\nBorderColor=#3e5212\n", light_text)
            updated_ui = classicui.read_text()
            self.assertIn("Theme=custom-theme\n", updated_ui)
            self.assertIn("DarkTheme=eitr\n", updated_ui)
            self.assertIn('Font="Noto Sans 11"\n', updated_ui)

    def test_missing_palette_writes_nothing_and_generators_include_fcitx5(self):
        with tempfile.TemporaryDirectory() as folder:
            theme_conf, _ = self.run_generator(Path(folder))
            self.assertFalse(theme_conf.exists())
        self.assertIn("fcitx5.py", (ROOT / "walker/scripts/themes/generate.sh").read_text())
        self.assertIn("fcitx5.py", (ROOT / "walker/scripts/actions/style/fonts.py").read_text())


if __name__ == "__main__":
    unittest.main()
