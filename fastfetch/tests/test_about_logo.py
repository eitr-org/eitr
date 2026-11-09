"""Preference fallback, shared settings, layout and reproducible rune exports."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def about_module():
    spec = importlib.util.spec_from_file_location('about_logo_test', ROOT / 'fastfetch/eitr.py')
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class AboutLogoTests(unittest.TestCase):
    def test_selection_and_invalid_preferences(self):
        module = about_module()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            preference = home / 'eitr/style.json'
            preference.parent.mkdir()
            for value in (None, 'emblem', 'runes', 'invalid', [], {}, 42):
                if value is not None:
                    preference.write_text(json.dumps({'aboutLogo': value}))
                with patch.object(module, 'terminal_logo', return_value='$1emblem'), patch.object(module, 'update_channel', return_value=None):
                    config = module.build_config(home, home)
                source = config['logo']['source']
                self.assertEqual('ᚠ' in source, value == 'runes')
                self.assertEqual(config['logo']['padding'], {'left': 2, 'right': 4})
                self.assertEqual(config['logo']['color']['1'], '#509475')
                self.assertEqual(module.build_config(home, home, False)['logo'], {'type': 'none'})
            for invalid in ('{', '[]', '{"version": 99}'):
                preference.write_text(invalid)
                self.assertEqual(module.about_logo(home), 'emblem')

    def test_runes_reserve_width_and_follow_theme_accent(self):
        module = about_module()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / 'eitr').mkdir()
            (home / 'eitr/style.json').write_text('{"aboutLogo":"runes"}')
            (home / 'theme/current').mkdir(parents=True)
            (home / 'theme/current/colors.toml').write_text('[colors]\naccent = "#123456"\n')
            for columns, expected in ((120, 76), (100, 56)):
                with patch.object(module.shutil, 'get_terminal_size', return_value=os.terminal_size((columns, 40))), patch.object(module, 'update_channel', return_value=None):
                    config = module.build_config(home, home)
                self.assertEqual(config['logo']['color']['1'], '#123456')
                self.assertEqual(module.cell_width(config['modules'][0]['format'].replace('{#2}', '').replace('{#}', '').replace('{##123456}', '')), expected)

    def test_write_preserves_other_style_preferences(self):
        import eitr_about_logo
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'style.json'
            target.write_text('{"corners":"square","gaps":"small"}')
            with patch.object(eitr_about_logo, 'config', return_value=target):
                eitr_about_logo.select('runes')
                with self.assertRaises(ValueError):
                    eitr_about_logo.select('unknown')
            self.assertEqual(json.loads(target.read_text()), {'version': 1, 'corners': 'square', 'gaps': 'small', 'aboutLogo': 'runes'})

    @unittest.skipUnless(shutil.which('rsvg-convert') and shutil.which('fc-match')
                         and importlib.util.find_spec('fontTools'),
                         'Rune export requires librsvg, fontconfig and fontTools')
    def test_generator_matches_committed_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for relative in ('branding/scripts/export-rune-logo.py', 'branding/svg/eitr-logo.svg'):
                target = folder / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / relative, target)
            (folder / 'fastfetch/assets').mkdir(parents=True)
            subprocess.run(['python3', str(folder / 'branding/scripts/export-rune-logo.py'), '--preview-dir', str(folder)], check=True, capture_output=True)
            for name in ('eitr-runes.txt',):
                self.assertEqual((folder / 'fastfetch/assets' / name).read_bytes(), (ROOT / 'fastfetch/assets' / name).read_bytes())
            lines = (folder / 'fastfetch/assets/eitr-runes.txt').read_text().splitlines()
            self.assertEqual((len(lines), max(map(len, lines))), (20, 38))
