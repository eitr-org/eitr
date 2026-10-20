import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'brightness', Path(__file__).parents[1] / 'scripts/brightness.py')
brightness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brightness)


class BrightnessTests(unittest.TestCase):
    def test_native_backlight_preferred_over_firmware_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, kind in [('acpi_video0', 'firmware'), ('intel_backlight', 'raw')]:
                device = root / name
                device.mkdir()
                (device / 'type').write_text(kind)
                (device / 'max_brightness').write_text('1000')
            with patch.object(brightness, 'Path', return_value=SimpleNamespace(glob=root.glob)):
                self.assertEqual(brightness.backlight().name, 'intel_backlight')

    def test_ddc_status_normalizes_monitor_range(self):
        with patch.object(brightness, 'backlight', return_value=None), \
                patch.object(brightness.shutil, 'which', return_value='/usr/bin/ddcutil'), \
                patch.object(brightness, 'run', return_value='VCP 10 C 75 150'):
            self.assertEqual(brightness.status()['value'], 50)

    def test_ddc_set_uses_monitor_range(self):
        calls = []

        def run(*command):
            calls.append(command)
            return 'VCP 10 C 75 150'

        with patch.object(brightness, 'backlight', return_value=None), \
                patch.object(brightness.shutil, 'which', return_value='/usr/bin/ddcutil'), \
                patch.object(brightness, 'run', side_effect=run):
            brightness.set_brightness(50, 150)
        self.assertIn(('ddcutil', 'setvcp', '10', '75'), calls)
        self.assertNotIn(('ddcutil', 'getvcp', '10', '--brief'), calls)

    def test_laptop_uses_brightnessctl(self):
        with patch.object(brightness, 'backlight', return_value=SimpleNamespace(name='intel_backlight')), \
                patch.object(brightness.shutil, 'which', return_value='/usr/bin/brightnessctl'), \
                patch.object(brightness, 'run') as command, \
                patch.object(brightness, 'status', return_value={'value': 40}):
            brightness.set_brightness(40)
        command.assert_called_once_with('brightnessctl', '--device', 'intel_backlight', 'set', '40%')
