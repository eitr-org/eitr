from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]


class LogoExportsTests(unittest.TestCase):
    def test_vectors_contain_paths_not_embedded_rasters(self):
        for filename in (ROOT / "svg").glob("*.svg"):
            document = ET.parse(filename)
            self.assertTrue(document.findall(".//{http://www.w3.org/2000/svg}path"))
            self.assertFalse(document.findall(".//{http://www.w3.org/2000/svg}image"))

    def test_png_sizes_and_transparency(self):
        files = list((ROOT / "png").glob("eitr-logo-*.png"))
        self.assertEqual(len(files), 33)
        for filename in files:
            size = int(filename.stem.rsplit("-", 1)[1])
            with Image.open(filename) as image:
                self.assertEqual(image.size, (size, size))
                self.assertEqual(image.mode, "RGBA")
                self.assertEqual(image.getchannel("A").getpixel((0, 0)), 0)

    def test_traced_shape_matches_selected_logo(self):
        with Image.open(ROOT / "source/eitr-logo-master.png") as image:
            source = image.getchannel("A")
            source = source.crop(source.getbbox())
            padding = round(max(source.size) * 0.06)
            side = max(source.size) + 2 * padding
            expected = Image.new("L", (side, side), 0)
            expected.paste(source, ((side - source.width) // 2, (side - source.height) // 2))
            expected = expected.resize((1024, 1024)).point(lambda value: 255 if value >= 128 else 0)
        with Image.open(ROOT / "png/eitr-logo-black-1024.png") as image:
            actual = image.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
        mismatch = sum(ImageChops.difference(expected, actual).histogram()[1:])
        self.assertLess(mismatch / (1024 * 1024), 0.005)

    def test_wordmark_exports_preserve_transparency_and_color_independent_shape(self):
        self.assertEqual((ROOT / "png/eitr-wordmark-black-512.png").read_bytes(),
                         (ROOT.parent / "fastfetch/assets/eitr-wordmark.png").read_bytes())
        master = ET.parse(ROOT / "source/eitr-wordmark-master.svg")
        _, _, width, height = map(float, master.getroot().get("viewBox").split())
        for size in (512, 1024, 2048):
            alpha = None
            for color in ("black", "white", "green"):
                with Image.open(ROOT / f"png/eitr-wordmark-{color}-{size}.png") as image:
                    self.assertEqual(image.size, (size, round(size * height / width)))
                    self.assertEqual(image.mode, "RGBA")
                    current = image.getchannel("A")
                    self.assertIsNotNone(current.getbbox())
                    self.assertEqual(current.getpixel((0, 0)), 0)
                    if alpha is not None:
                        self.assertIsNone(ImageChops.difference(alpha, current).getbbox())
                    alpha = current

    def test_banner_and_icon_dimensions(self):
        for name in ("dark", "light"):
            with Image.open(ROOT / f"banners/eitr-{name}-1920x1080.png") as image:
                self.assertEqual(image.size, (1920, 1080))
        with Image.open(ROOT / "icons/eitr.ico") as image:
            self.assertIn((256, 256), image.ico.sizes())


if __name__ == "__main__":
    unittest.main()
