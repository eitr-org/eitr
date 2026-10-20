import importlib.util
from pathlib import Path
import tomllib
import unittest

spec = importlib.util.spec_from_file_location(
    'selection_colors', Path(__file__).parents[1] / 'scripts/themes/selection-colors.py')
colors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(colors)


class SelectionColorsTests(unittest.TestCase):
    def test_all_installed_themes(self):
        themes = Path(__file__).parents[2] / 'themes'
        files = sorted(themes.glob('*/colors.toml'))
        self.assertTrue(files)
        for file in files:
            with self.subTest(theme=file.parent.name):
                with file.open('rb') as source:
                    palette = tomllib.load(source)
                selected = colors.selection_colors(palette, (file.parent / 'light.mode').exists())
                for role in ('foreground', 'current'):
                    self.assertGreaterEqual(colors.contrast(selected[role], selected['background']), 4.5)
                    self.assertIn(selected[role], palette.values())

    def test_readable_preferred_color_is_preserved(self):
        palette = {'background': '#101010', 'foreground': '#eeeeee',
                   'accent': '#aaffaa', 'selection_foreground': '#dddddd'}
        selected = colors.selection_colors(palette)
        self.assertEqual(selected['foreground'], '#dddddd')
        self.assertEqual(selected['current'], '#aaffaa')
