from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "distro/plymouth/eitr/eitr.script"


class PlymouthThemeTests(unittest.TestCase):
    def test_a_rune_stays_lit_only_after_the_progress_passes_it(self):
        script = SCRIPT.read_text()
        # index < progress * count lit the top rune (index 0) from the first moment of every boot.
        self.assertIn("if (index + 1 <= ring.progress * ring.count) light = 0.75;", script)
        self.assertNotIn("if (index < ring.progress * ring.count)", script)

    def test_the_passphrase_prompt_shares_the_accent(self):
        # One colour from power-on to the desktop: the prompt matches the runes and wordmark.
        export = (SCRIPT.parent / "export.py").read_text()
        for asset in ('rgb(accent)).save(HERE / "bullet.png")', 'rgb(accent, 28)).save(HERE / "field.png")',
                      "fill=rgb(accent, 235)"):
            self.assertIn(asset, export)
        self.assertNotIn("foreground", export)

    def test_every_rune_image_exists(self):
        theme = SCRIPT.parent
        for index in range(24):
            self.assertTrue((theme / f"rune-{index:02d}.png").is_file(), index)


if __name__ == "__main__":
    unittest.main()
