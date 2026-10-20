import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('wallpaper_export', ROOT / 'tools/export-wallpapers-4k.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class WallpaperExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / 'themes/norse/backgrounds/subject.png'
        self.path.parent.mkdir(parents=True)
        image = Image.new('RGB', (100, 40), 'blue')
        ImageDraw.Draw(image).rectangle((85, 0, 99, 39), fill='red')
        image.save(self.path)
        for name, value in [('ROOT', self.root), ('SIZE', (32, 18))]:
            override = patch.object(exporter, name, value)
            override.start()
            self.addCleanup(override.stop)

    def test_right_hand_subject_survives_crop(self):
        record = exporter.export(self.path, lossless={'themes/norse/backgrounds/subject.png'})
        self.assertEqual(record['source_size'], [100, 40])
        with Image.open(self.path) as image:
            self.assertEqual(image.size, (32, 18))
            self.assertEqual(image.getpixel((31, 9)), (255, 0, 0))
        self.assertIsNone(exporter.export(self.path, lossless={'themes/norse/backgrounds/subject.png'}))

    def test_painted_wallpapers_become_jpeg(self):
        record = exporter.export(self.path)
        jpeg = self.path.with_suffix('.jpg')
        self.assertEqual((record['file'], record['converted_from']),
                         ('themes/norse/backgrounds/subject.jpg', 'themes/norse/backgrounds/subject.png'))
        self.assertFalse(self.path.exists(), 'the PNG is replaced, not kept beside it')
        with Image.open(jpeg) as image:
            self.assertEqual((image.format, image.size), ('JPEG', (32, 18)))
            red, green, blue = image.getpixel((31, 9))
            self.assertTrue(red > 200 and green < 60 and blue < 60)
        self.assertIsNone(exporter.export(jpeg), 'a 4K JPEG is left alone')

    def test_a_4k_png_is_converted_without_a_new_crop(self):
        Image.new('RGB', (32, 18), 'green').save(self.path)
        record = exporter.export(self.path)
        self.assertEqual(set(record), {'file', 'converted_from'}, 'the earlier crop record is kept by main()')

    def test_owner_deletion_during_export_is_not_restored(self):
        save = Image.Image.save

        def save_then_delete(image, filename, **options):
            save(image, filename, **options)
            self.path.unlink()

        with patch.object(Image.Image, 'save', save_then_delete):
            self.assertIsNone(exporter.export(self.path))
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.path.parent.iterdir()), [])

    def test_concurrent_owner_edit_is_preserved(self):
        save = Image.Image.save

        def save_then_edit(image, filename, **options):
            save(image, filename, **options)
            self.path.write_bytes(b'owner replacement')

        with patch.object(Image.Image, 'save', save_then_edit):
            with self.assertRaisesRegex(RuntimeError, 'kept owner version'):
                exporter.export(self.path)
        self.assertEqual(self.path.read_bytes(), b'owner replacement')
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


class UltrawideFramingTests(unittest.TestCase):
    def test_crop_fills_canvas_without_repeating_edge_columns(self):
        specification = importlib.util.spec_from_file_location('ultrawide_export', ROOT / 'tools/export-wallpapers-ultrawide.py')
        ultrawide = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(ultrawide)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = Image.new('RGB', (24, 24))
            for column in range(24):
                for row in range(24):
                    source.putpixel((column, row), (column * 10, row * 10, 0))
            source.save(root / 'source.png')
            record = {'file': 'wide.jpg', 'source': {'file': 'source.png'}, 'framing': 'crop'}
            with patch.object(ultrawide, 'ROOT', root), patch.object(ultrawide, 'SIZE', (64, 24)):
                ultrawide.export(record)
                with Image.open(root / 'wide.jpg') as result:
                    self.assertEqual(result.size, (64, 24))
                    self.assertGreater(result.getpixel((16, 12))[0] - result.getpixel((0, 12))[0], 40)
                    self.assertGreater(result.getpixel((63, 12))[0] - result.getpixel((48, 12))[0], 40)
                    self.assertGreater(result.getpixel((32, 0))[1], 50, 'top is cropped, not padded')
                record['framing'] = 'contain'
                with self.assertRaisesRegex(ValueError, 'Unknown wallpaper framing'):
                    ultrawide.export(record)
