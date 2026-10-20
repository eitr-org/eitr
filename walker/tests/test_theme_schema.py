import os
from pathlib import Path
import json
import re
import subprocess
import sys
import tomllib
import unittest
from PIL import Image

import menu_data

ROOT = Path(__file__).resolve().parents[2]
THEMES = ROOT / "themes"
sys.path.insert(0, str(ROOT / "walker/scripts/themes"))
import palette  # noqa: E402

REQUIRED = {"backgrounds", "btop.theme", "colors.toml", "display-name", "dolphin.theme",
            "icons.theme", "neovim.lua", "preview.png", "rgb.color", "vscode.json"}
OPTIONAL = {"artwork.md", "backgrounds-ultrawide", "light.mode", "motion", "references", "vscode.vsix"}
COLOR_KEYS = {"accent", "background", "foreground", "cursor", "selection_background",
              "selection_foreground", *(f"color{index}" for index in range(16))}
# Base themes shipped by kvantum-theme-catppuccin-git.
KVANTUM_THEME = re.compile(r"^catppuccin-(latte|frappe|macchiato|mocha)-(rosewater|flamingo|pink|mauve|red|"
                           r"maroon|peach|yellow|green|teal|sky|sapphire|blue|lavender)$")


def theme_dirs():
    return sorted(path for path in THEMES.iterdir() if path.is_dir())


class ThemeSchemaTests(unittest.TestCase):
    def test_generated_integration_files_are_up_to_date(self):
        # icons.theme, vscode.json, neovim.lua and btop.theme come from integrations.json and colors.toml.
        result = subprocess.run([sys.executable, str(THEMES / "build-theme-files.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((THEMES / "IMPORT-LICENSE").exists(), "no imported theme files remain")

    def test_wallpapers_are_4k_and_retired_themes_are_absent(self):
        for name in ('everforest', 'tokyo-night', 'flexoki-light'):
            self.assertFalse((THEMES / name).exists(), name)
        for theme in theme_dirs():
            for path in (theme / 'backgrounds').iterdir():
                if path.name.startswith('.'):
                    continue
                with self.subTest(wallpaper=str(path)), Image.open(path) as image:
                    self.assertEqual(image.size, (3840, 2160))

    def test_each_wallpaper_has_one_ultrawide_version(self):
        manifest = json.loads((THEMES / "artwork-ultrawide.json").read_text())
        recorded = {record["file"] for record in manifest["images"]}
        for theme in theme_dirs():
            wallpapers = {path.stem for path in (theme / "backgrounds").iterdir() if not path.name.startswith(".")}
            ultrawide = theme / "backgrounds-ultrawide"
            variants = {path.stem for path in ultrawide.iterdir()} if ultrawide.is_dir() else set()
            with self.subTest(theme=theme.name):
                self.assertEqual(variants, wallpapers, "run tools/export-wallpapers-ultrawide.py")
                for name in variants:
                    path = ultrawide / f"{name}.jpg"
                    self.assertIn(path.relative_to(THEMES.parent).as_posix(), recorded)
                    with Image.open(path) as image:
                        self.assertEqual(image.size, (3440, 1440))

    def test_every_theme_has_required_and_only_known_files(self):
        self.assertTrue(theme_dirs())
        for theme in theme_dirs():
            with self.subTest(theme=theme.name):
                names = {path.name for path in theme.iterdir() if path.name != ".DS_Store"}
                self.assertEqual(REQUIRED - names, set())
                self.assertEqual(names - REQUIRED - OPTIONAL, set())
                self.assertTrue(any((theme / "backgrounds").iterdir()))
                self.assertTrue((theme / "display-name").read_text().strip())

    def test_palettes_are_complete_and_light_mode_matches_luminance(self):
        for theme in theme_dirs():
            with self.subTest(theme=theme.name):
                colors = palette.load(theme)
                self.assertEqual(COLOR_KEYS - set(colors), set())
                light_palette = palette.luminance(colors["background"]) > palette.luminance(colors["foreground"])
                self.assertEqual(palette.is_light(theme), light_palette)

    def test_dolphin_theme_resolves_to_matching_kvantum_flavor(self):
        for theme in theme_dirs():
            with self.subTest(theme=theme.name):
                name = (theme / "dolphin.theme").read_text().strip()
                match = KVANTUM_THEME.match(name)
                self.assertTrue(match or (ROOT / "Kvantum" / f"{name}#").is_dir(), name)
                if match:
                    self.assertEqual(match.group(1) == "latte", palette.is_light(theme), name)

    def test_elephant_actions_reference_existing_scripts(self):
        for name, data in menu_data.static_menus().items():
            for entry in data.get("entries", []):
                for command in (entry.get("actions") or {}).values():
                    for match in re.finditer(r"(\S*)\s*\$HOME/\.config/(\S+)", command):
                        interpreter, relative = match.groups()
                        script = ROOT / relative
                        with self.subTest(menu=name, script=relative):
                            self.assertTrue(script.is_file())
                            if Path(interpreter).name not in {"bash", "python3", "sh"}:
                                self.assertTrue(os.access(script, os.X_OK))

    def test_elephant_lua_modules_reference_existing_repo_files(self):
        for source in [*ROOT.joinpath("elephant").rglob("*.lua"), *ROOT.joinpath("walker/scripts/menus").glob("*.lua")]:
            for relative in re.findall(r'"/\.config/((?:elephant|walker)/[^"]+\.(?:lua|sh|py))"', source.read_text()):
                with self.subTest(source=source.name, path=relative):
                    self.assertTrue((ROOT / relative).is_file())


if __name__ == "__main__":
    unittest.main()
