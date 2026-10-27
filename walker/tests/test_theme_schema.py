import hashlib
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
    def test_realm_palettes_and_wallpaper_contract(self):
        expected = {
            "alfheim": ("0c0a14 15121f 241e36 ece6f5 9d93b3 e04fc3 3fe39a ff6b7a", "ff6b7a 3fe39a c2ee5a 8a8cf5 e04fc3 4fd2c0"),
            "asgard": ("0a0a0b 131315 202024 d8d8d4 8d8d88 ddbd7e 3fe39a c86a5e", "c86a5e 9aa58a b8a06a 8a98a8 a395a8 92a8a4"),
            "helheim": ("0a0a0b 131315 202024 d8d8d4 8d8d88 cfc6b0 b8a06a c86a5e", "c86a5e 9aa58a b8a06a 8a98a8 a395a8 92a8a4"),
            "jotunheim": ("0b0d10 12161b 1d252e dfe6ea 8995a0 a7b1c2 8fb8d0 d0736b", "d0736b 8fbf9f c9b27a 8fb8d0 a99cc9 86c3c9"),
            "midgard": ("0b1015 121a22 1e2a35 d9e2e8 8a9aa6 7ee0b5 4fc3c9 e0716a", "e0716a 7ee0b5 d9a865 6aa7d8 a78bd6 4fc3c9"),
            "muspelheim": ("0e070c 170c14 2a1424 f1e4ea a68e9b a6124d b7c43c f08a4b", "f0505a 9cc72a ccc564 8a7fd0 e95978 6fc2b0"),
            "niflheim": ("0b0d10 12161b 1d252e dfe6ea 8995a0 8fb8d0 c9b27a d0736b", "d0736b 8fbf9f c9b27a 8fb8d0 a99cc9 86c3c9"),
            "ragnarok": ("0a0909 131111 221d1d e4dcd2 9a8f86 a8323a b08d57 d9822b", "c94a4a 8f9a63 b08d57 6d7f99 9a5a7a 6f9590"),
            "svartalfheim": ("0d0e10 15171a 22252a e6dfd0 9a9488 c8894a 6f8597 c4554a", "c4554a 8fa36b d9a865 6f8fb0 9c7aa8 6fa3a3"),
            "vanaheim": ("0d100b 171b13 252d20 dce2d5 929e87 a9b47c d9a865 e0716a", "e0716a 7ee0b5 d9a865 6aa7d8 a78bd6 4fc3c9"),
        }
        batch = json.loads((THEMES / "artwork-batch-05.json").read_text())
        self.assertEqual(sorted(record["theme"] for record in batch["images"]), sorted(expected))
        for name, (roles, ansi) in expected.items():
            with self.subTest(theme=name):
                theme = THEMES / name
                colors = palette.load(theme)
                for key, value in zip(("background", "surface", "raised", "foreground", "muted",
                                       "accent", "second", "alert"), roles.split()):
                    self.assertEqual(colors[key], "#" + value)
                for index, value in enumerate(ansi.split(), 1):
                    self.assertEqual(colors[f"color{index}"], "#" + value)
                for surface in ("background", "surface", "raised"):
                    self.assertGreaterEqual(palette.contrast(colors["foreground"], colors[surface]), 4.5)
                self.assertGreaterEqual(palette.contrast(palette.accent_text(colors), colors["surface"]), 4.5)
                self.assertFalse((theme / "light.mode").exists())
                self.assertEqual(len(list((theme / "backgrounds").glob("*.jpg"))), 2)
                self.assertEqual(len(list((theme / "backgrounds-ultrawide").glob("*.jpg"))), 2)
                self.assertEqual((theme / "rgb.color").read_text().strip().lower(), colors["accent"][1:])
                record = next(record for record in batch["images"] if record["theme"] == name)
                source = ROOT / record["native_source"]
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), record["native_sha256"])
                with Image.open(source) as image:
                    self.assertEqual(list(image.size), record["native_size"])

    def test_realm_environment_sources_and_exports(self):
        batch = json.loads((THEMES / "artwork-batch-06.json").read_text())
        approved = json.loads((THEMES / "artwork-batch-05.json").read_text())
        self.assertEqual(sorted(record["theme"] for record in batch["images"]),
                         sorted(approved["previews"]))
        for record in batch["images"]:
            with self.subTest(theme=record["theme"]):
                self.assertTrue(Path(record["file"]).name.startswith("02-"))
                for prefix in ("native", "ultrawide_native"):
                    if prefix + "_source" not in record:
                        continue
                    source = ROOT / record[prefix + "_source"]
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     record[prefix + "_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record[prefix + "_size"])
                for key, size in (("file", (3840, 2160)), ("ultrawide_file", (3440, 1440))):
                    with Image.open(ROOT / record[key]) as image:
                        self.assertEqual(image.size, size)
                self.assertIn("/01-", approved["previews"][record["theme"]])

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
