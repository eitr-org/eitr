"""Logo guards for the Fastfetch About page, using a stand-in for Pillow."""
import importlib.util
from pathlib import Path
import sys
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


if __name__ == "__main__":
    unittest.main()


class VersionTests(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("PIL", None)

    def test_about_shows_the_installed_package_version(self):
        module = load(FakeImage(("R", "G", "B", "A"), None))
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "version").write_text("0.3.0.20261014.035137.g3aaa9c8\n")
            (Path(directory) / "release.json").write_text('{"version": "0.3.0", "stage": "alpha", "codename": "Ymir"}')
            module.code = lambda relative: Path(directory) / relative
            self.assertEqual(module.eitr_version(), '0.3.0 "Ymir" (alpha, build 20261014.035137.g3aaa9c8)')
            (Path(directory) / "version").unlink()
            self.assertEqual(module.eitr_version(), "development checkout")
