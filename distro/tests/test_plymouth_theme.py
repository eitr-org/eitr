import subprocess
import sys
import tomllib
from pathlib import Path
from PIL import Image
from eitr_bifrost import PHASE_COUNT, FRAME_SECONDS, ADVANCE_NUMERATOR, ADVANCE_DENOMINATOR, phase_color, frame_phase
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "distro/plymouth/eitr/eitr.script"


class PlymouthThemeTests(unittest.TestCase):
    def test_a_rune_stays_lit_only_after_the_progress_passes_it(self):
        script = SCRIPT.read_text()
        # index < progress * count lit the top rune (index 0) from the first moment of every boot.
        self.assertIn("if (index + 1 <= ring.progress * ring.count) light = 0.75;", script)
        self.assertNotIn("if (index < ring.progress * ring.count)", script)

    def test_gold_runes_and_neutral_prompt_remain_readable(self):
        palette = tomllib.loads((ROOT / "themes/norse/colors.toml").read_text())
        foreground = tuple(bytes.fromhex(palette["foreground"][1:]))
        for name, expected in (("rune-00.png", (196, 145, 79)), ("bullet.png", (196, 145, 79)),
                               ("passphrase.png", foreground)):
            with Image.open(SCRIPT.parent / name) as image:
                pixels = list(image.convert("RGBA").get_flattened_data())
                opaque = max(pixels, key=lambda pixel: pixel[3])
                self.assertEqual(opaque[:3], expected)
                self.assertGreater(opaque[3], 200)
        script = SCRIPT.read_text()
        self.assertIn("global.ring.visible = 1;", script)
        with Image.open(SCRIPT.parent / "wordmark.png") as logo, Image.open(SCRIPT.parent / "passphrase.png") as prompt:
            for height in (480, 720, 1080):
                ring_bottom = height / 2 - 40 + logo.height / 2 + 90
                prompt_y = ring_bottom + 40 - 8
                field_bottom = ring_bottom + 40 + prompt.height + 4 + 40
                self.assertGreaterEqual(prompt_y, ring_bottom + 26)
                self.assertLessEqual(field_bottom, height)

    def test_all_wordmark_phases_match_the_shared_terminal_palette(self):
        script = SCRIPT.read_text()
        self.assertIn(f"wordmark.phase_count = {PHASE_COUNT};", script)
        self.assertIn(f"wordmark.ticks_per_frame = {FRAME_SECONDS * 50:g};", script)
        self.assertIn(f"wordmark.advance_numerator = {ADVANCE_NUMERATOR};", script)
        self.assertIn(f"wordmark.advance_denominator = {ADVANCE_DENOMINATOR};", script)
        for phase in range(PHASE_COUNT):
            with Image.open(SCRIPT.parent / f"wordmark-{phase:02d}.png") as image:
                pixel = max(image.convert("RGBA").get_flattened_data(), key=lambda pixel: pixel[3])
                self.assertEqual(pixel, phase_color(phase) + (255,))
        self.assertEqual(frame_phase(0), frame_phase(96))
        self.assertEqual(phase_color(0), (224, 92, 104))

    def test_exports_are_reproducible_without_running_plymouth(self):
        result = subprocess.run([sys.executable, str(SCRIPT.parent / "export.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_rune_image_exists(self):
        theme = SCRIPT.parent
        for index in range(24):
            self.assertTrue((theme / f"rune-{index:02d}.png").is_file(), index)


if __name__ == "__main__":
    unittest.main()
