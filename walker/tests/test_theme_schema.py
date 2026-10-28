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


# The owner's curated wallpaper count per realm theme.
REALM_WALLPAPERS = {"alfheim": 3, "asgard": 4, "helheim": 3, "jotunheim": 3, "midgard": 2,
                    "muspelheim": 3, "niflheim": 3, "ragnarok": 4, "svartalfheim": 3, "vanaheim": 3}


def active(records):
    """Batch records whose wallpaper still ships; removed ones keep only their prompts."""
    return [record for record in records if record.get("status") != "removed"]


class ThemeSchemaTests(unittest.TestCase):
    def test_realm_palettes_and_wallpaper_contract(self):
        expected = {
            "alfheim": ("191721 252231 373044 f0eaf6 ada2ba d5b9f2 8eddd3 e895a7", "e895a7 a9d6b3 e6ce96 a3bdf0 d5b9f2 8eddd3"),
            "asgard": ("141820 1d2330 2c3545 e9edf4 98a4b5 e4b968 8faed8 e67e80", "e67e80 9ccb9b e4b968 8faed8 c6a1da 85c9d7"),
            "helheim": ("15171a 212529 32383a dfe3dc 9ca8a0 a3bd79 b193ba cf818b", "cf818b a3bd79 d0ba82 91a9c5 b193ba 8ebeb6"),
            "jotunheim": ("121a24 1d2937 2c3c4d e5edf5 9bafc1 78b6cd b7a0d9 e48d9c", "e48d9c 94c7b6 e1c18d 85aee1 b7a0d9 78c5d2"),
            "midgard": ("171a1d 22282d 343e45 e5e8e8 9ca7ac 83a6c7 bfa17b da8582", "da8582 91b69c d8be85 83a6c7 be9cbf 80bdbe"),
            "muspelheim": ("1d1314 2b1c1c 432a27 f4e6df bda39c f28b59 e9bd63 f07870", "f07870 b4c486 e9bd63 91abce d29bbf 8ec8c2"),
            "niflheim": ("101b25 1b2a36 2a3d4b e7f3f7 9fb7c6 91d5e6 a6c1f0 de94a5", "de94a5 9acdbd dbd49f a6c1f0 c5b0e2 91d5e6"),
            "ragnarok": ("120f13 21191e 38272d f2e7e2 ac999e c44750 e7ad67 e16a72", "8f202b a4bd8d e7ad67 9ca9d5 c69ac6 8ac8cc"),
            "svartalfheim": ("191715 29231f 3c322b ede5db b0a398 d49a65 8ab7ad e17f72", "e17f72 9dbb89 e0bd78 8eadcb b79ac6 8ab7ad"),
            "vanaheim": ("101a17 1b2822 2c3e33 e3ede2 94aa9c 83b88e d5ad72 df827b", "df827b 83b88e d5ad72 83afa8 c6a0c8 8bcbc0"),
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
                wallpapers = sorted(path.name for path in (theme / "backgrounds").glob("*.jpg"))
                self.assertEqual(len(wallpapers), REALM_WALLPAPERS[name])
                self.assertEqual([wallpaper[:3] for wallpaper in wallpapers],
                                 [f"{number:02}-" for number in range(1, len(wallpapers) + 1)])
                self.assertEqual(sorted(path.name for path in (theme / "backgrounds-ultrawide").glob("*.jpg")),
                                 wallpapers)
                self.assertEqual(batch["previews"][name], f"themes/{name}/backgrounds/{wallpapers[0]}")
                self.assertEqual((theme / "rgb.color").read_text().strip().lower(), colors["accent"][1:])
                for record in active(batch["images"]):
                    if record["theme"] != name:
                        continue
                    source = ROOT / record["native_source"]
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), record["native_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record["native_size"])

    def test_realm_environment_sources_and_exports(self):
        batch = json.loads((THEMES / "artwork-batch-06.json").read_text())
        approved = json.loads((THEMES / "artwork-batch-05.json").read_text())
        self.assertEqual(sorted(record["theme"] for record in batch["images"]),
                         sorted(approved["previews"]))
        for record in active(batch["images"]):
            with self.subTest(theme=record["theme"]):
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

    def test_realm_batch_07_provenance_and_exports(self):
        batch = json.loads((THEMES / "artwork-batch-07.json").read_text())
        realms = {"alfheim", "asgard", "helheim", "jotunheim", "midgard",
                  "muspelheim", "niflheim", "svartalfheim", "vanaheim"}
        self.assertEqual(len(batch["images"]), 18)
        self.assertLessEqual({record["theme"] for record in batch["images"]}, realms)
        manifests = {
            name: {record["file"]: record for record in
                   json.loads((THEMES / name).read_text())["images"]}
            for name in ("artwork-4k.json", "artwork-ultrawide.json")}
        sources = set()
        for record in active(batch["images"]):
            with self.subTest(wallpaper=record["file"]):
                self.assertTrue(record["rendering_style"].strip())
                for prefix in ("native", "ultrawide_native"):
                    if prefix + "_source" not in record:
                        continue
                    source = ROOT / record[prefix + "_source"]
                    sources.add(source.resolve())
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     record[prefix + "_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record[prefix + "_size"])
                for key, size in (("file", (3840, 2160)), ("ultrawide_file", (3440, 1440))):
                    self.assertEqual(Path(record[key]).stem, record["name"])
                    with Image.open(ROOT / record[key]) as image:
                        self.assertEqual(image.size, size)
                        self.assertEqual(image.format, "JPEG")
                export = manifests["artwork-4k.json"][record["file"]]
                self.assertEqual(export["source"], record["native_source"])
                self.assertEqual(export["source_sha256"], record["native_sha256"])
                wide = manifests["artwork-ultrawide.json"][record["ultrawide_file"]]
                self.assertEqual(wide["source"]["file"],
                                 record.get("ultrawide_native_source", record["native_source"]))
                self.assertEqual(wide["framing"], "crop")
                for centering in (record["centering"], record["ultrawide_centering"]):
                    self.assertEqual(len(centering), 2)
                    self.assertTrue(all(0 <= coordinate <= 1 for coordinate in centering))
        self.assertEqual(sources, {source.resolve() for source in
                                  (ROOT / "branding/sources/wallpapers/batch-07").glob("*.png")})

    def test_ragnarok_batch_08_provenance_and_exports(self):
        batch = json.loads((THEMES / "artwork-batch-08.json").read_text())
        self.assertEqual([record["name"] for record in batch["images"]],
                         ["01-blood-eclipse", "02-fenrir-devours-the-sun", "03-dying-yggdrasil"])
        sources = set()
        for record in batch["images"]:
            with self.subTest(wallpaper=record["name"]):
                self.assertEqual(record["theme"], "ragnarok")
                self.assertIn("owner-approved", record["status"])
                self.assertTrue(record["rendering_style"])
                self.assertTrue(record["prompt"])
                self.assertTrue(record["ultrawide_prompt"])
                for prefix in ("native", "ultrawide_native"):
                    source = ROOT / record[prefix + "_source"]
                    sources.add(source.resolve())
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     record[prefix + "_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record[prefix + "_size"])
                self.assertNotEqual(record["native_sha256"], record["ultrawide_native_sha256"])
                for key, size in (("file", (3840, 2160)), ("ultrawide_file", (3440, 1440))):
                    with Image.open(ROOT / record[key]) as image:
                        self.assertEqual(image.size, size)
                        self.assertEqual(image.format, "JPEG")
        self.assertEqual(sources, {source.resolve() for source in
                                  (ROOT / "branding/sources/wallpapers/batch-08").glob("*.png")})

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
