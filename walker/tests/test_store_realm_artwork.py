"""Palette and source-art contracts for the official Store checkout."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
STORE = Path(os.environ.get('EITR_THEMES_DIR', ROOT.with_name('eitr-themes')))
SOURCES = STORE / 'sources/eitr-realms'
RECORDS = SOURCES / 'themes'
sys.path.insert(0, str(ROOT / 'walker/scripts/themes'))
import palette  # noqa: E402

# The owner's curated wallpaper count per realm theme.
REALM_WALLPAPERS = {"alfheim": 3, "asgard": 3, "helheim": 3, "jotunheim": 3, "midgard": 2,
                    "muspelheim": 3, "niflheim": 3, "ragnarok": 5, "svartalfheim": 3, "vanaheim": 3}


def active(records):
    """Batch records whose wallpaper still ships; removed ones keep only their prompts."""
    return [record for record in records if record.get("status") != "removed"]


@unittest.skipUnless(SOURCES.is_dir(), "requires the migrated official Store checkout")
class RealmArtworkTests(unittest.TestCase):
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
        batch = json.loads((RECORDS / "artwork-batch-05.json").read_text())
        self.assertEqual(sorted(record["theme"] for record in batch["images"]), sorted(expected))
        for name, (roles, ansi) in expected.items():
            with self.subTest(theme=name):
                theme = STORE / name
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
                self.assertEqual(batch["previews"][name], f"{name}/backgrounds/{wallpapers[0]}")
                self.assertEqual((theme / "rgb.color").read_text().strip().lower(), colors["accent"][1:])
                for record in active(batch["images"]):
                    if record["theme"] != name:
                        continue
                    source = STORE / record["native_source"]
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), record["native_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record["native_size"])


    def test_realm_environment_sources_and_exports(self):
        batch = json.loads((RECORDS / "artwork-batch-06.json").read_text())
        approved = json.loads((RECORDS / "artwork-batch-05.json").read_text())
        self.assertEqual(sorted(record["theme"] for record in batch["images"]),
                         sorted(approved["previews"]))
        for record in active(batch["images"]):
            with self.subTest(theme=record["theme"]):
                for prefix in ("native", "ultrawide_native"):
                    if prefix + "_source" not in record:
                        continue
                    source = STORE / record[prefix + "_source"]
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     record[prefix + "_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record[prefix + "_size"])
                for key, size in (("file", (3840, 2160)), ("ultrawide_file", (3440, 1440))):
                    with Image.open(STORE / record[key]) as image:
                        self.assertEqual(image.size, size)


    def test_realm_batch_07_provenance_and_exports(self):
        batch = json.loads((RECORDS / "artwork-batch-07.json").read_text())
        realms = {"alfheim", "asgard", "helheim", "jotunheim", "midgard",
                  "muspelheim", "niflheim", "svartalfheim", "vanaheim"}
        self.assertEqual(len(batch["images"]), 18)
        self.assertLessEqual({record["theme"] for record in batch["images"]}, realms)
        manifests = {
            name: {record["file"]: record for record in
                   json.loads((RECORDS / name).read_text())["images"]}
            for name in ("artwork-4k.json", "artwork-ultrawide.json")}
        sources = set()
        for record in active(batch["images"]):
            with self.subTest(wallpaper=record["file"]):
                self.assertTrue(record["rendering_style"].strip())
                for prefix in ("native", "ultrawide_native"):
                    if prefix + "_source" not in record:
                        continue
                    source = STORE / record[prefix + "_source"]
                    sources.add(source.resolve())
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     record[prefix + "_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record[prefix + "_size"])
                for key, size in (("file", (3840, 2160)), ("ultrawide_file", (3440, 1440))):
                    self.assertEqual(Path(record[key]).stem, record["name"])
                    with Image.open(STORE / record[key]) as image:
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
                                  (SOURCES / "branding/sources/wallpapers/batch-07").glob("*.png")})


    def check_painterly_batch(self, number, theme, names):
        batch = json.loads((RECORDS / f"artwork-batch-{number}.json").read_text())
        self.assertEqual([record["name"] for record in batch["images"]], names)
        sources = set()
        for record in batch["images"]:
            with self.subTest(wallpaper=record["name"]):
                self.assertEqual(record["theme"], theme)
                if record.get("status") != "removed":
                    self.assertIn("owner-approved", record["status"])
                self.assertTrue(record["rendering_style"])
                self.assertTrue(record["prompt"])
                self.assertTrue(record["ultrawide_prompt"])
                for prefix in ("native", "ultrawide_native"):
                    source = STORE / record[prefix + "_source"]
                    sources.add(source.resolve())
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     record[prefix + "_sha256"])
                    with Image.open(source) as image:
                        self.assertEqual(list(image.size), record[prefix + "_size"])
                self.assertNotEqual(record["native_sha256"], record["ultrawide_native_sha256"])
                if record.get("status") == "removed":
                    continue
                for key, size in (("file", (3840, 2160)), ("ultrawide_file", (3440, 1440))):
                    with Image.open(STORE / record[key]) as image:
                        self.assertEqual(image.size, size)
                        self.assertEqual(image.format, "JPEG")
        self.assertEqual(sources, {source.resolve() for source in
                                  (SOURCES / f"branding/sources/wallpapers/batch-{number}").glob("*.png")})


    def test_ragnarok_batch_08_provenance_and_exports(self):
        self.check_painterly_batch("08", "ragnarok",
                                  ["01-blood-eclipse", "02-fenrir-devours-the-sun", "03-dying-yggdrasil"])


if __name__ == "__main__":
    unittest.main()
