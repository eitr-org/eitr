"""Glow persistence, Settings discovery and pixels from production bar surfaces."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageChops
from layout_render import copy_runtime, render_environment, render, capture_path, EDGES
from test_bar_settings import bar_settings

BAR = Path(__file__).resolve().parents[1]


class BarGlowTests(unittest.TestCase):
    def test_preference_defaults_round_trip_and_validation(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bar_settings, 'SETTINGS', Path(directory) / 'bar.json'):
            self.assertEqual(bar_settings.read_settings()['glow'], 'no')
            bar_settings.SETTINGS.write_text('{"dock":"no"}')
            for value in ('yes', 'no'):
                bar_settings.save_settings({'glow': value})
                self.assertEqual(bar_settings.read_settings()['glow'], value)
                self.assertEqual(bar_settings.read_settings()['dock'], 'no')
            with self.assertRaises(ValueError):
                bar_settings.save_settings({'glow': True})
            arguments = [bar_settings.DEFAULTS[key] for key in bar_settings.DEFAULTS if key != 'blur-strength']
            arguments[-1] = 'yes'
            with patch('sys.argv', ['bar-settings.py', 'set-all', *arguments]), patch('builtins.print'):
                self.assertEqual(bar_settings.main(), 0)
            self.assertEqual(bar_settings.read_settings()['glow'], 'yes')

    def test_settings_search_and_default(self):
        catalog = (BAR / 'settings/SettingsCatalog.js').read_text()
        self.assertIn('"id": "bar-glow", "label": "Glow", "page": "bar", "tab": "look"', catalog)
        page = (BAR / 'settings/SettingsBarPage.qml').read_text()
        self.assertIn('objectName: "setting-bar-glow"', page)
        self.assertIn('checked: styleModel.barGlow', page)
        self.assertIn('property bool barGlow: false', (BAR / 'shell.qml').read_text())

    def test_production_surface_pixels(self):
        with tempfile.TemporaryDirectory(prefix='eitr-glow-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            environment = render_environment(directory)
            for layout in ('full', 'centered', 'tabs', 'islands', 'dynamic'):
                for edge, light in [(edge, False) for edge in EDGES] + [("top", True)]:
                    capture = capture_path('GLOW', directory, f'{layout}-{edge}-{"light" if light else "dark"}')
                    fixture = (BAR / 'tests/fixtures/layout/glow.qml.in').read_text()
                    for key, value in {'LAYOUT': json.dumps(layout), 'LIGHT': str(light).lower(), 'EDGE': json.dumps(edge), 'CAPTURE': json.dumps(str(capture))}.items():
                        fixture = fixture.replace(key, value)
                    window = (BAR / 'bar/BarWindow.qml').read_text()
                    transform = window.split('id: barContents', 1)[1].split('        transform: ', 1)[1].split('        width:', 1)[0].strip()
                    transform = transform.replace('host.', 'shell.').replace('bar.', 'strip.').replace('autoHide.progress', 'slide.progress')
                    fixture = fixture.replace('SLIDE_TRANSFORM', 'transform: ' + transform)
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    code, output = render(path, environment, 15)
                    self.assertEqual(code, 0, output)
                    for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Unable to assign', 'Error:'):
                        self.assertNotIn(error, output)
                    default = Image.open(str(capture) + '-default.png').convert('RGB')
                    off = Image.open(str(capture) + '-off.png').convert('RGB')
                    on = Image.open(str(capture) + '-on.png').convert('RGB')
                    self.assertIsNone(ImageChops.difference(default, off).getbbox())
                    # Below every layout's 30 px surface and 6 px island gap:
                    # no foreground content can account for these changed pixels.
                    region = {'top': (0, 37, 900, 55), 'bottom': (0, 85, 900, 103),
                              'left': (37, 0, 55, 900), 'right': (85, 0, 103, 900)}[edge]
                    difference = ImageChops.difference(off, on).crop(region)
                    self.assertIsNotNone(difference.getbbox(), (layout, edge, light, output))
                    sliding = Image.open(str(capture) + '-sliding.png').convert('RGB')
                    hidden = Image.open(str(capture) + '-hidden.png').convert('RGB')
                    self.assertIsNotNone(ImageChops.difference(on, sliding).getbbox())
                    self.assertIsNotNone(ImageChops.difference(sliding, hidden).getbbox())
