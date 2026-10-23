import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("eitr_about", ROOT / "fastfetch/eitr.py")
ABOUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ABOUT)


class AboutTests(unittest.TestCase):
    def test_missing_theme_has_safe_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            config = ABOUT.build_config(Path(directory), Path(directory), False)
        self.assertEqual(config["logo"]["type"], "none")
        self.assertTrue(any(isinstance(module, dict) and module.get("format") == "Default"
                            and "Theme" in module["key"] for module in config["modules"]))

    def test_theme_is_read_again_and_nested_palette_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            theme = root / "theme/current"
            theme.mkdir(parents=True)
            (theme / "display-name").write_text("Test Light\n")
            palette = theme / "colors.toml"
            palette.write_text('[colors]\naccent = "#112233"\ncolor0 = "#abcdef"\n')
            first = ABOUT.build_config(root, root, False)
            self.assertIn("#112233", first["modules"][1]["key"])
            self.assertIn("{##abcdef}", first["modules"][-1]["format"])
            palette.write_text('accent = "#445566"\n')
            self.assertIn("#445566", ABOUT.build_config(root, root, False)["modules"][1]["key"])

    def test_invalid_color_cannot_inject_terminal_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            theme = root / "theme/current"
            theme.mkdir(parents=True)
            (theme / "colors.toml").write_text('accent = "invalid"\n')
            self.assertIn("#509475", ABOUT.build_config(root, root, False)["modules"][1]["key"])

    def test_selected_logo_renders_seventeen_rows(self):
        logo = ABOUT.terminal_logo(ROOT / "fastfetch/assets/eitr-logo.png")
        self.assertEqual(len(logo.splitlines()), 17)
        self.assertIn("▀", logo)

    def test_shared_wordmark_is_not_rendered_in_about(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "fastfetch/assets"
            assets.mkdir(parents=True)
            for name in ("eitr-logo.png", "eitr-wordmark.png"):
                (assets / name).write_bytes(b"")
            with patch.object(ABOUT, "code", side_effect=lambda relative: root / relative), \
                    patch.object(ABOUT, "terminal_logo", return_value=None) as render:
                config = ABOUT.build_config(root, root)
            render.assert_called_once_with(assets / "eitr-logo.png")
            self.assertIn("Hardware", config["modules"][0]["format"])
            self.assertEqual(config["modules"][0]["key"], " ")


if __name__ == "__main__":
    unittest.main()
