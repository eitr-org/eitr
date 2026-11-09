"""Approved artwork provenance, framing and theme default regression checks."""
import importlib.util
import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


class Batch12Tests(unittest.TestCase):
    def test_sources_exports_hashes_and_default_order(self):
        batch = json.loads((ROOT / 'themes/artwork-batch-12.json').read_text())
        self.assertEqual(len(batch['images']), 3)
        retained = json.loads((ROOT / 'themes/artwork-batch-11.json').read_text())
        records = batch['images'] + [record for record in retained['images']
                                     if record.get('status') != 'removed']
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
        for theme in ('eitr', 'eitr-light'):
            for folder in ('backgrounds', 'backgrounds-ultrawide'):
                names = sorted(path.stem for path in (ROOT / 'themes' / theme / folder).iterdir())
                expected = ['01-dusk-fjord', '02-gates-of-yggdrasil', '03-rune-seal', '04-primordial-drop']
                if theme == 'eitr':
                    expected = ['01-aurora-fjord', '02-dusk-fjord', '03-rune-seal', '04-eitr-runestone']
                self.assertEqual(names, expected)

    def test_theme_switch_and_fresh_install_first_wallpaper(self):
        specification = importlib.util.spec_from_file_location(
            'transition', ROOT / 'walker/scripts/actions/wallpaper/transition.py')
        transition = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(transition)
        for theme, first in (('eitr', '01-aurora-fjord.jpg'), ('eitr-light', '01-dusk-fjord.jpg')):
            wallpapers = transition.wallpapers(ROOT / 'themes' / theme / 'backgrounds')
            self.assertEqual(Path(wallpapers[0]).name, first)

    def test_retired_records_cannot_be_exported_again(self):
        for number in ('09', '10', '11'):
            batch = json.loads((ROOT / f'themes/artwork-batch-{number}.json').read_text())
            for record in batch['images']:
                if record.get('status') == 'removed':
                    self.assertFalse((ROOT / record['file']).exists())
                    self.assertFalse((ROOT / record['ultrawide_file']).exists())
                else:
                    self.assertTrue((ROOT / record['file']).exists())
                    self.assertTrue((ROOT / record['ultrawide_file']).exists())

    def test_shared_dusk_and_undistributed_reference(self):
        for folder in ('backgrounds', 'backgrounds-ultrawide'):
            dark = ROOT / 'themes/eitr' / folder / '02-dusk-fjord.jpg'
            light = ROOT / 'themes/eitr-light' / folder / '01-dusk-fjord.jpg'
            self.assertEqual(dark.read_bytes(), light.read_bytes())
        self.assertFalse(list((ROOT / 'branding').rglob('ref-fjord-style.png')))
