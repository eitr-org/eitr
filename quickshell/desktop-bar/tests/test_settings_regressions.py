"""Offscreen regressions for shared Settings controls and bar popup geometry."""
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from layout_render import BAR, copy_runtime, render_environment, render, capture_path


class SettingsRegressionTests(unittest.TestCase):
    def test_portal_rule_is_scoped_to_picture_chooser(self):
        rule = (BAR.parents[1] / 'hypr/hyprland.lua').read_text().split('name = "eitr-picture-chooser",', 1)[1].split('})', 1)[0]
        for value in ('class = "^(xdg-desktop-portal-gtk)$"', 'title = "^.* · Eitr$"',
                      'float = true', 'center = true', 'size = { 900, 640 }', 'stay_focused = true'):
            self.assertIn(value, rule)
        self.assertIn('Eitr.I18n.tr("Choose a picture") + " · Eitr"', (BAR / 'settings/SettingsSystemHost.qml').read_text())

    def test_controls_offscreen(self):
        with tempfile.TemporaryDirectory(prefix='settings-regression-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            output = capture_path('SETTINGS', directory, 'regression').parent
            fixture = (BAR / 'tests/fixtures/settings/regressions.qml.in').read_text().replace('OUTPUT', str(output))
            (folder / 'fixture.qml').write_text(fixture)
            code, result = render(folder / 'fixture.qml', render_environment(folder, (1280, 1000)), 90)
            self.assertEqual(code, 0, result)
            self.assertIn('REGRESSIONS_OK', result)
            for diagnostic in ('FAIL!', 'TypeError:', 'ReferenceError:', 'Binding loop', 'Unable to assign', 'ERROR qml:'):
                self.assertNotIn(diagnostic, result)
            for corner in ('square', 'rounded', 'extra-rounded'):
                for family in ('Settings', 'Handbook', 'EitrStore'):
                    with Image.open(output / f'sidebar-{corner}-{family}.png') as picture:
                        self.assertEqual(picture.convert('RGB').getpixel((24, 190)), (25, 27, 37))
            for layout in ('unified', 'centered', 'notch', 'islands', 'dynamic', 'drop'):
                for edge in ('top', 'bottom', 'left', 'right'):
                    self.assertTrue((output / f'dropdown-{layout}-{edge}.png').is_file())
            for panel in range(4):
                for edge in ('top', 'bottom', 'left', 'right'):
                    self.assertTrue((output / f'dynamic-{panel}-{edge}.png').is_file())
