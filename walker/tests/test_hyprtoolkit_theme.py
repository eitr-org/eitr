"""Hyprland's own dialogs (the screen-share picker) follow the theme through hyprtoolkit.conf."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/themes/hyprtoolkit.py'
PALETTE = '''background = "#101b25"
surface = "#1b2a36"
raised = "#2a3d4b"
foreground = "#e7f3f7"
bright_foreground = "#edf6f9"
accent = "#91d5e6"
second = "#a6c1f0"
'''


class HyprtoolkitThemeTests(unittest.TestCase):
    def run_generator(self, config):
        environment = {key: value for key, value in os.environ.items() if not key.startswith('XDG_')}
        environment.update(XDG_CONFIG_HOME=str(config), XDG_STATE_HOME=str(config / 'state'),
                           XDG_DATA_HOME=str(config / 'data'), HOME=str(config))
        subprocess.run(['python3', str(SCRIPT)], env=environment, check=True, timeout=30)
        return config / 'hypr/hyprtoolkit.conf'

    def test_writes_theme_colours_font_and_corners(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder)
            (config / 'theme/current').mkdir(parents=True)
            (config / 'theme/current/colors.toml').write_text(PALETTE)
            text = self.run_generator(config).read_text()
            for line in ('background = rgb(101b25)', 'base = rgb(1b2a36)', 'alternate_base = rgb(2a3d4b)',
                         'text = rgb(e7f3f7)', 'accent = rgb(91d5e6)', 'rounding_large = 9',
                         'rounding_small = 4', 'font_size = 13', 'icon_theme = eitr-current'):
                self.assertIn(line + '\n', text)
            self.assertRegex(text, r'\nfont_family = \S')

    def test_own_file_is_left_alone_and_no_theme_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder)
            self.assertFalse(self.run_generator(config).exists())
            (config / 'theme/current').mkdir(parents=True)
            (config / 'theme/current/colors.toml').write_text(PALETTE)
            (config / 'hypr').mkdir()
            (config / 'hypr/hyprtoolkit.conf').write_text('accent = rgb(ff0000)\n')
            self.assertEqual(self.run_generator(config).read_text(), 'accent = rgb(ff0000)\n')


if __name__ == '__main__':
    unittest.main()
