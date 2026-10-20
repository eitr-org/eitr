import colorsys
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/themes/palette.py"
sys.path.insert(0, str(SCRIPT.parent))
import palette  # noqa: E402


class PaletteTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.theme = Path(self.temporary.name)
        (self.theme / "colors.toml").write_text(
            'accent = "#112233"\nforeground = "#eeeeee"\nbackground = "#101010"\n'
            'color1 = "#ff0000"\nbroken = "red"\n')

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--dir", str(self.theme), *args],
                              capture_output=True, text=True)

    def test_get_prints_one_line_per_key_and_skips_invalid_values(self):
        result = self.run_cli("get", "accent", "missing", "broken", "color1")
        self.assertEqual(result.stdout.split("\n")[:4], ["#112233", "", "", "#ff0000"])

    def test_light_mode_marker_decides_light_themes(self):
        self.assertEqual(self.run_cli("is-light").returncode, 1)
        (self.theme / "light.mode").touch()
        self.assertEqual(self.run_cli("is-light").returncode, 0)

    def test_fzf_colors_follow_palette_and_need_core_colors(self):
        colors = self.run_cli("fzf-colors").stdout.strip()
        self.assertIn("bg:#101010", colors)
        self.assertIn("hl:#ff0000", colors)
        self.assertEqual(palette.fzf_colors({"foreground": "#ffffff"}), "")

    def test_missing_palette_is_empty(self):
        self.assertEqual(palette.load(self.theme / "absent"), {})

    def test_dark_accent_gets_a_readable_text_shade_of_the_same_hue(self):
        shade = self.run_cli("accent-text").stdout.strip()
        self.assertGreaterEqual(palette.contrast(shade, "#101010"), 4.5)
        hue = lambda color: colorsys.rgb_to_hls(*(value / 255 for value in palette.rgb(color)))[0]
        self.assertAlmostEqual(hue(shade), hue("#112233"), places=2)
        self.assertEqual(palette.accent_text({"accent": "#89b4fa", "foreground": "#cdd6f4",
                                              "background": "#1e1e2e"}), "#89b4fa")

    def test_contrast(self):
        self.assertAlmostEqual(palette.contrast("#000000", "#ffffff"), 21.0)


if __name__ == "__main__":
    unittest.main()
