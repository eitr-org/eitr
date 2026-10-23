"""Logo guards for the Fastfetch About page, using a stand-in for Pillow."""
import importlib.util
from pathlib import Path
import sys
import re
import tempfile
import types
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "eitr.py"


class FakeImage:
    def __init__(self, bands, bbox):
        self.bands, self.bbox = bands, bbox

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def getbands(self):
        return self.bands

    def getchannel(self, band):
        return self

    def getbbox(self):
        return self.bbox


def load(image):
    pil = types.ModuleType("PIL")
    pil.Image = types.SimpleNamespace(open=lambda path: image)
    sys.modules["PIL"] = pil
    spec = importlib.util.spec_from_file_location("eitr_fastfetch", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LogoTests(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("PIL", None)

    def test_logo_without_alpha_is_skipped(self):
        module = load(FakeImage(("R", "G", "B"), (0, 0, 1, 1)))
        self.assertIsNone(module.terminal_logo("logo.png"))

    def test_fully_transparent_logo_is_skipped(self):
        module = load(FakeImage(("R", "G", "B", "A"), None))
        self.assertIsNone(module.terminal_logo("logo.png"))

    def test_unrenderable_logo_falls_back_to_no_logo(self):
        module = load(FakeImage(("L",), None))
        with tempfile.TemporaryDirectory() as home:
            logo = Path(home) / "fastfetch/assets/eitr-logo.png"
            logo.parent.mkdir(parents=True)
            logo.write_bytes(b"")
            config = module.build_config(Path(home), Path(home))
        self.assertEqual(config["logo"], {"type": "none"})
        self.assertNotIn("Rune Liquid", str(config["modules"]))


class SolidMask(FakeImage):
    """A fully opaque mask of a given size, enough for terminal_logo to sample."""
    def __init__(self, width, height):
        super().__init__(("R", "G", "B", "A"), (0, 0, width, height))
        self.width, self.height = width, height

    def crop(self, bounds):
        return SolidMask(bounds[2] - bounds[0], bounds[3] - bounds[1])

    def resize(self, size, method=None):
        return SolidMask(*size)

    def getpixel(self, point):
        return 255


class ProportionTests(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("PIL", None)

    def test_the_logo_keeps_its_proportions_on_terminal_cells(self):
        module = load(SolidMask(200, 100))
        sys.modules["PIL"].Image.Resampling = types.SimpleNamespace(LANCZOS=None)
        # Half a cell per sample: a 2:1 logo on 0.5-ratio cells is 34 wide and 8 rows (16 samples) tall.
        module.cell_ratio = lambda: 0.5
        rows = module.terminal_logo(Path("wide.png")).removeprefix("$1").splitlines()
        self.assertEqual((len(rows[0]), len(rows)), (34, 8))
        explicit = module.terminal_logo(Path("wide.png"), 24, 10).removeprefix("$1").splitlines()
        self.assertEqual((len(explicit[0]), len(explicit)), (24, 5))


class VersionTests(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("PIL", None)

    def test_about_shows_the_installed_package_version(self):
        module = load(FakeImage(("R", "G", "B", "A"), None))
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "version").write_text("0.3.0.20261014.035137.g3aaa9c8\n")
            (Path(directory) / "release.json").write_text('{"version": "0.3.0", "stage": "alpha", "codename": "Ymir"}')
            module.code = lambda relative: Path(directory) / relative
            self.assertEqual(module.eitr_version(), '0.3.0 "Ymir" (alpha)')
            (Path(directory) / "version").unlink()
            self.assertEqual(module.eitr_version(), "development checkout")


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.module = load(FakeImage(("L",), None))

    def tearDown(self):
        sys.modules.pop("PIL", None)

    def test_boxes_and_palette_follow_the_current_theme_without_wordmark(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            current = home / "theme/current"
            current.mkdir(parents=True)
            (current / "colors.toml").write_text('[colors]\ncolor2="#123456"\ncolor4="#abcdef"\ncolor3="#654321"\n')
            (current / "display-name").write_text("Test theme")
            config = self.module.build_config(home, home, image=False)
        modules = config["modules"]
        rendered = str(modules)
        for title in ("Hardware", "Software", "Time"):
            self.assertIn(title, rendered)
        for color in ("#123456", "#abcdef", "#654321"):
            self.assertIn(color, rendered)
        self.assertIn("Test theme", rendered)
        self.assertNotIn("wordmark", rendered)
        self.assertNotIn("█", rendered)
        self.assertEqual(rendered.count("●"), 16)
        self.assertEqual(config["logo"], {"type": "none"})
        borders = [item["format"] for item in modules if isinstance(item, dict)
                   and item.get("type") == "custom" and "─" in item.get("format", "")]
        self.assertEqual(len(borders), 6)
        # Every border is equally wide on screen once Fastfetch's {#...} colour codes are left out.
        visible = {self.module.cell_width(re.sub(r"\{#[^}]*\}", "", border)) for border in borders}
        self.assertEqual(len(visible), 1)
        disk = next(item for item in modules if isinstance(item, dict) and item["type"] == "disk")
        self.assertEqual(disk["folders"], "/")
        self.assertIn("{filesystem}", disk["format"])

    def test_long_values_are_cut_to_the_box_without_a_right_border(self):
        output = "logo ┌──────────┐\nlogo │ \x1b[31m界界界界界界界\x1b[m\nlogo └──────────┘"
        result = self.module.align_boxes(output)
        lines = result.splitlines()
        # The row stays within the box (top and bottom borders are 17 cells) and has no closing │.
        self.assertEqual([self.module.cell_width(line) for line in (lines[0], lines[2])], [17, 17])
        self.assertLessEqual(self.module.cell_width(lines[1]), 16)
        self.assertIn("…", lines[1])
        self.assertIn("\x1b[31m", lines[1])
        self.assertFalse(self.module.ANSI.sub("", lines[1]).rstrip().endswith("│"))

    def test_short_values_are_padded_and_combining_marks_take_no_extra_cell(self):
        fitted = self.module.fit_cells("e\u0301", 5)
        self.assertEqual(self.module.cell_width(fitted), 5)
        self.assertNotIn("…", fitted)
        self.assertEqual(self.module.ANSI.sub("", fitted), "e\u0301    ")

    def test_age_prefers_root_birth_time_and_handles_missing_log(self):
        from unittest.mock import patch
        with patch.object(self.module.subprocess, "run", return_value=types.SimpleNamespace(stdout="100000")), \
                patch.object(self.module.time, "time", return_value=100000 + 86400 * 4):
            self.assertEqual(self.module.os_age(), "4 days")
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(self.module.subprocess, "run", return_value=types.SimpleNamespace(stdout="0")):
            log = Path(directory) / "pacman.log"
            log.write_text("bad line\n[2020-03-02T00:00:00+00:00] later\n[2020-03-01T00:00:00+00:00] earlier\n")
            with patch.object(self.module.time, "time", return_value=1583193600):
                self.assertEqual(self.module.os_age(log=log), "2 days")
            log.unlink()
            self.assertEqual(self.module.os_age(log=log), "Unavailable")


if __name__ == "__main__":
    unittest.main()
