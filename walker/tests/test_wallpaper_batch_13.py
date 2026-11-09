"""Approved artwork provenance, framing and theme default regression checks."""
import importlib.util
import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


class Batch13Tests(unittest.TestCase):
    def test_sources_exports_hashes_and_default_order(self):
        batch = json.loads((ROOT / 'themes/artwork-batch-13.json').read_text())
        self.assertEqual(len(batch['images']), 1)
        records = batch['images']
        for record in records:
            self.assertTrue(record['prompt'])
            self.assertTrue(record['input_images'])
            self.assertTrue(record['ultrawide_input_images'])
            self.assertEqual(record['centering'], [0.5, 0.5])
            for prefix in ('native', 'ultrawide_native'):
                path = ROOT / record[prefix + '_source']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record[prefix + '_sha256'])
                with Image.open(path) as image:
                    self.assertEqual(list(image.size), record[prefix + '_size'])
            for key, size in (('file', (3840, 2160)), ('ultrawide_file', (3440, 1440))):
                path = ROOT / record[key]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record[key + '_sha256'])
                with Image.open(path) as image:
                    self.assertEqual(image.size, size)
                    self.assertEqual(image.format, 'JPEG')
        expected_names = {
            'svartalfheim': ['01-feasting-hall', '02-hammer-warriors', '03-forge-canyon'],
            'asgard': ['01-radiant-citadel', '02-bifrost-hall', '03-storm-bridge'],
        }
        for theme, expected in expected_names.items():
            for folder in ('backgrounds', 'backgrounds-ultrawide'):
                names = sorted(path.stem for path in (ROOT / 'themes' / theme / folder).iterdir())
                self.assertEqual(names, expected)

    def test_retired_records_are_excluded_and_unused_sources_removed(self):
        for number, retired in (('06', '03-cloud-fortress'), ('07', '01-cavern-city')):
            batch = json.loads((ROOT / f'themes/artwork-batch-{number}.json').read_text())
            record = next(record for record in batch['images'] if record['name'] == retired)
            self.assertEqual(record['status'], 'removed')
            for key in ('file', 'ultrawide_file', 'native_source', 'ultrawide_native_source'):
                if key in record:
                    self.assertFalse((ROOT / record[key]).exists())

    def test_theme_switch_and_fresh_install_first_wallpaper(self):
        specification = importlib.util.spec_from_file_location(
            'transition', ROOT / 'walker/scripts/actions/wallpaper/transition.py')
        transition = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(transition)
        for theme, first in (('svartalfheim', '01-feasting-hall.jpg'), ('asgard', '01-radiant-citadel.jpg')):
            wallpapers = transition.wallpapers(ROOT / 'themes' / theme / 'backgrounds')
            self.assertEqual(Path(wallpapers[0]).name, first)

    def test_style_input_identifies_the_approved_dusk_master(self):
        batch = json.loads((ROOT / 'themes/artwork-batch-13.json').read_text())
        history = batch['images'][0]['prompt_history'][0]
        self.assertEqual(history['input_images'], ['style-fjord-c.png'])
        self.assertEqual(history['input_source'],
                         'branding/sources/wallpapers/batch-12/eitr-02-dusk-fjord.png')
        self.assertTrue((ROOT / history['input_source']).is_file())
        self.assertFalse(list((ROOT / 'branding').rglob('dwarfs-b.png')))
