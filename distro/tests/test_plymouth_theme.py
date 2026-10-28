import importlib.util
import subprocess
import sys
import tomllib
from pathlib import Path
from PIL import Image
from eitr_bifrost import PHASE_COUNT, FRAME_SECONDS, ADVANCE_NUMERATOR, ADVANCE_DENOMINATOR, phase_color, frame_phase
import unittest

ROOT = Path(__file__).resolve().parents[2]
export_spec = importlib.util.spec_from_file_location("plymouth_export", ROOT / "distro/plymouth/eitr/export.py")
exporter = importlib.util.module_from_spec(export_spec)
export_spec.loader.exec_module(exporter)
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
        self.assertIn("global.ring.visible = visible;", script)
        password = script.split("fun display_password_callback", 1)[1].split("Plymouth.SetDisplayPasswordFunction", 1)[0]
        normal = script.split("fun display_normal_callback", 1)[1]
        self.assertIn("show_progress(0);", password)
        self.assertIn("show_progress(1);", normal)
        self.assertIn("global.runes[index].SetOpacity(visible * 0.18);", script)
        with Image.open(SCRIPT.parent / "wordmark.png") as logo, Image.open(SCRIPT.parent / "passphrase.png") as prompt:
            for height in (480, 720, 1080):
                logo_bottom = height / 2 - 40 + logo.height / 2
                prompt_y = logo_bottom + 48 - 8
                field_bottom = logo_bottom + 48 + prompt.height + 4 + 40
                self.assertGreaterEqual(prompt_y, logo_bottom + 32)
                self.assertLessEqual(field_bottom, height)

    def test_all_wordmark_phases_match_the_shared_terminal_palette(self):
        script = SCRIPT.read_text()
        self.assertIn(f"wordmark.phase_count = {PHASE_COUNT};", script)
        self.assertIn(f"wordmark.ticks_per_frame = {FRAME_SECONDS * 50:g};", script)
        self.assertIn(f"wordmark.advance_numerator = {ADVANCE_NUMERATOR};", script)
        self.assertIn(f"wordmark.advance_denominator = {ADVANCE_DENOMINATOR};", script)
        mask = None
        for phase in range(PHASE_COUNT):
            with Image.open(SCRIPT.parent / f"wordmark-{phase:02d}.png") as image:
                if mask is None: mask = image.getchannel("A").tobytes()
                self.assertEqual(image.getchannel("A").tobytes(), mask)
                for column in (0, 70, 170, 280, 359):
                    expected = exporter.gradient_color(phase - column / exporter.GRADIENT_COLUMN_WIDTH)
                    self.assertEqual(image.getpixel((column, 50))[:3], expected)
                self.assertNotEqual(image.getpixel((0, 50))[:3], image.getpixel((280, 50))[:3])
        self.assertIn("wordmark.blend.SetOpacity(phase - index);", script)
        self.assertNotIn("Math.Int(Math.Int(global.tick", script)
        # A full colour cycle takes 3 seconds: 30 frames of 0.1 s.
        self.assertEqual(frame_phase(0), frame_phase(30))
        self.assertNotEqual(frame_phase(0), frame_phase(15))
        self.assertEqual(phase_color(0), (224, 92, 104))

    def test_gradient_moves_right_and_wraps_smoothly(self):
        for phase in range(PHASE_COUNT):
            # One phase advances the same band twelve pixels to the right.
            self.assertEqual(exporter.gradient_color(phase + 1 - 132 / 12), exporter.gradient_color(phase - 120 / 12))
            self.assertEqual(exporter.gradient_color(phase + PHASE_COUNT), exporter.gradient_color(phase))
            first, second = exporter.gradient_color(phase), exporter.gradient_color(phase + 1)
            self.assertLessEqual(max(abs(start - end) for start, end in zip(first, second)), 16)

    def test_exports_are_reproducible_without_running_plymouth(self):
        result = subprocess.run([sys.executable, str(SCRIPT.parent / "export.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_rune_image_exists(self):
        theme = SCRIPT.parent
        for index in range(24):
            self.assertTrue((theme / f"rune-{index:02d}.png").is_file(), index)


if __name__ == "__main__":
    unittest.main()
