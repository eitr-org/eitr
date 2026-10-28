import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/appearance-items.py"


class AppearanceCategoryTests(unittest.TestCase):
    def test_theme_categories_and_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            themes = home / ".config/themes"
            for name, light in (("dark-a", False), ("dark-b", False), ("light-a", True)):
                theme = themes / name
                theme.mkdir(parents=True)
                (theme / "preview.png").touch()
                (theme / 'colors.toml').touch()
                if light:
                    (theme / "light.mode").touch()
            cache = home / ".cache"
            cache.mkdir()
            (cache / "current-theme").write_text("dark-b\n")

            def load(mode):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), mode],
                    env={**os.environ, "HOME": str(home), "XDG_CACHE_HOME": str(cache),
                         "EITR_CODE_ROOT": str(home / '.config')},
                    capture_output=True, text=True, check=True,
                )
                return json.loads(result.stdout)["items"]

            categories = load("theme-category")
            self.assertEqual([item["name"] for item in categories], ["Dark", "Light"])
            self.assertEqual([item["current"] for item in categories], [True, False])
            self.assertTrue(categories[0]["image"].endswith("/dark-b/preview.png"))
            assets = home / ".config/quickshell/desktop-bar/assets/appearance"
            assets.mkdir(parents=True)
            for name in ("dark", "light"):
                Image.new("RGB", (320, 180)).save(assets / f"{name}.jpg")
            custom_categories = load("theme-category")
            self.assertEqual([item["image"] for item in custom_categories],
                             [(assets / f"{name}.jpg").as_uri() for name in ("dark", "light")])
            self.assertEqual([item["current"] for item in custom_categories], [True, False])
            self.assertTrue(all("aspectRatio" not in item for item in custom_categories))
            for name in ("dark", "light"):
                Image.new("RGB", (320, 180)).save(assets / f"{name}.png")
            self.assertEqual([item["image"] for item in load("theme-category")],
                             [(assets / f"{name}.png").as_uri() for name in ("dark", "light")])
            self.assertEqual([item["name"] for item in load("theme-dark")], ["Dark A", "Dark B"])
            self.assertEqual([item["value"] for item in load("theme-dark")], ["dark-a", "dark-b"])
            self.assertEqual([item["name"] for item in load("theme-light")], ["Light A"])
            (themes / "dark-b/display-name").write_text("Custom Theme\n")
            renamed = load("theme-dark")[1]
            self.assertEqual(renamed["name"], "Custom Theme")
            self.assertEqual(renamed["value"], "dark-b")
            self.assertTrue(renamed["current"])
            (themes / "dark-b/display-name").write_text("\n")
            self.assertEqual(load("theme-dark")[1]["name"], "Dark B")


if __name__ == "__main__":
    unittest.main()
