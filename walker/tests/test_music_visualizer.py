import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'walker/scripts/themes'))
spec = importlib.util.spec_from_file_location('cava_theme', ROOT / 'walker/scripts/themes/cava.py')
cava = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cava)


class MusicVisualizerTests(unittest.TestCase):
    def test_colors_preserve_settings(self):
        palette = {'foreground': '#ffffff', 'accent': '#123456'}
        settings = '[general]\nbars = 42\n\n[color]\ngradient = 0\n\n[input]\nmethod = pipewire\n'
        result = cava.generate(palette, settings)
        self.assertIn('bars = 42', result)
        self.assertIn('method = pipewire', result)
        self.assertIn("gradient_color_3 = '#123456'", result)
        self.assertEqual(result.count('[color]'), 1)
        self.assertEqual(cava.generate(palette, result), result)

    def test_menu_and_package(self):
        rows = json.loads((ROOT / 'elephant/menu-rows/tools.json').read_text())
        row = next(row for row in rows if row['text'] == 'Music Visualizer')
        self.assertLessEqual(len(row['subtext']), 72)
        self.assertIn('music-visualizer.sh', row['actions']['open'])
        self.assertIn('cava', (ROOT / 'distro/packages.txt').read_text().splitlines())
