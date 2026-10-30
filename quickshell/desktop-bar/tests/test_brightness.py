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


class IdleBrightnessTests(unittest.TestCase):
    def test_exact_restore_and_repeated_timeout(self):
        import os
        import json
        targets = [{'kind': 'backlight', 'device': 'panel', 'level': 937},
                   {'kind': 'ddc', 'bus': '7', 'level': 73},
                   {'kind': 'ddc', 'bus': '8', 'level': 1}]
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                patch.object(brightness, 'idle_targets', return_value=iter(targets)), \
                patch.object(brightness, 'idle_set') as setter:
            def set_level(target, level):
                saved = Path(directory) / 'eitr-idle-brightness/levels.json'
                self.assertIn(target, json.loads(saved.read_text()))
            setter.side_effect = set_level
            brightness.idle_brightness('dim')
            self.assertEqual([call.args[1] for call in setter.call_args_list], [281, 22, 1])
            brightness.idle_brightness('dim')
            self.assertEqual(setter.call_count, 3)
            brightness.idle_brightness('restore')
            self.assertEqual([call.args[1] for call in setter.call_args_list][3:], [937, 73, 1])
            brightness.idle_brightness('restore')
            self.assertEqual(setter.call_count, 6)
            self.assertFalse((Path(directory) / 'eitr-idle-brightness/levels.json').exists())

    def test_failed_restore_is_retained(self):
        import os
        target = {'kind': 'ddc', 'bus': '7', 'level': 0}
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                patch.object(brightness, 'idle_targets', return_value=iter([target])), \
                patch.object(brightness, 'idle_set') as setter:
            brightness.idle_brightness('dim')
            setter.assert_called_once_with(target, 1)
            setter.side_effect = OSError('Disconnected')
            brightness.idle_brightness('restore')
            self.assertTrue((Path(directory) / 'eitr-idle-brightness/levels.json').exists())
            setter.side_effect = None
            brightness.idle_brightness('restore')
            setter.assert_called_with(target, 0)

    def test_ddc_unavailable_is_skipped_per_monitor(self):
        import subprocess
        def run(*command):
            if 'detect' in command:
                return 'I2C bus: /dev/i2c-7\nI2C bus: /dev/i2c-8\n'
            if '7' in command:
                raise subprocess.TimeoutExpired(command, 8)
            return 'VCP 10 C 93 200'
        with patch.object(brightness, 'backlight', return_value=None), \
                patch.object(brightness.shutil, 'which', return_value='/mock/ddcutil'), \
                patch.object(brightness, 'run', side_effect=run):
            self.assertEqual(list(brightness.idle_targets()),
                             [{'kind': 'ddc', 'bus': '8', 'level': 93}])

    def test_raw_writes_do_not_round_to_percent(self):
        with patch.object(brightness, 'run') as command:
            brightness.idle_set({'kind': 'backlight', 'device': 'panel'}, 937)
            command.assert_called_with('brightnessctl', '--device', 'panel', 'set', '937')
            brightness.idle_set({'kind': 'ddc', 'bus': '7'}, 73)
            command.assert_called_with('ddcutil', '--bus', '7', 'setvcp', '10', '73')

    def test_idle_config_and_shared_bar_toggle(self):
        import re
        root = Path(__file__).resolve().parents[3]
        config = (root / 'hypr/hypridle.conf').read_text()
        listeners = dict((int(timeout), body) for timeout, body in re.findall(
            r'listener\s*\{\s*timeout\s*=\s*(\d+)([^}]+)\}', config))
        self.assertEqual(set(listeners), {880, 900, 1800, 3600})
        self.assertIn('brightness.py dim', listeners[880])
        self.assertIn('on-resume = eitr-run quickshell/desktop-bar/scripts/brightness.py restore', listeners[880])
        self.assertIn('on-timeout = loginctl lock-session', listeners[900])
        self.assertIn('on-timeout = hyprctl dispatch dpms off', listeners[1800])
        self.assertIn('on-resume = hyprctl dispatch dpms on', listeners[1800])
        self.assertIn('on-timeout = systemctl suspend', listeners[3600])
        self.assertIn('walker/scripts/actions/toggle/idle-lock.sh',
                      (root / 'quickshell/desktop-bar/shell.qml').read_text())

    def test_toggle_stops_and_restores_or_starts_shared_daemon(self):
        import os
        import subprocess
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ('pgrep', 'pkill', 'eitr-run', 'uwsm'):
                script = folder / name
                script.write_text('#!/bin/bash\n'
                                  'printf "%s %s\\n" "${0##*/}" "$*" >> "$TEST_LOG"\n'
                                  'if [[ "${0##*/}" == pgrep ]]; then exit "$TEST_RUNNING"; fi\n')
                script.chmod(0o755)
            log = folder / 'calls'
            environment = {**os.environ, 'PATH': f'{folder}:/usr/bin:/bin',
                           'TEST_LOG': str(log), 'TEST_RUNNING': '0'}
            toggle = root / 'walker/scripts/actions/toggle/idle-lock.sh'
            subprocess.run(['bash', str(toggle)], env=environment, check=True)
            self.assertEqual(log.read_text().splitlines(), [
                'pgrep -x hypridle', 'pkill -x hypridle',
                'eitr-run quickshell/desktop-bar/scripts/brightness.py restore'])
            log.unlink()
            environment['TEST_RUNNING'] = '1'
            subprocess.run(['bash', '-c', 'source "$1"; wait', 'test', str(toggle)],
                           env=environment, check=True)
            self.assertEqual(log.read_text().splitlines(),
                             ['pgrep -x hypridle', 'uwsm app -- eitr-hypridle'])

    def test_resume_waits_for_slow_dim(self):
        import os
        import threading
        dimming = threading.Event()
        resume_started = threading.Event()
        calls = []
        target = {'kind': 'ddc', 'bus': '7', 'level': 73}

        def set_level(control, level):
            calls.append(level)
            if level == 22:
                dimming.set()
                self.assertTrue(resume_started.wait(2))

        def restore():
            resume_started.set()
            brightness.idle_brightness('restore')

        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                patch.object(brightness, 'idle_targets', return_value=iter([target])), \
                patch.object(brightness, 'idle_set', side_effect=set_level):
            dim_thread = threading.Thread(target=brightness.idle_brightness, args=('dim',))
            dim_thread.start()
            self.assertTrue(dimming.wait(2))
            resume_thread = threading.Thread(target=restore)
            resume_thread.start()
            dim_thread.join(3)
            resume_thread.join(3)
            self.assertFalse(dim_thread.is_alive())
            self.assertFalse(resume_thread.is_alive())
            self.assertEqual(calls, [22, 73])

    def test_backlight_snapshot_uses_raw_level_and_no_ddc_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            device = Path(directory) / 'panel'
            device.mkdir()
            (device / 'brightness').write_text('937')
            with patch.object(brightness, 'backlight', return_value=device), \
                    patch.object(brightness.shutil, 'which', side_effect=lambda name: name if name == 'brightnessctl' else None):
                self.assertEqual(list(brightness.idle_targets()),
                                 [{'kind': 'backlight', 'device': 'panel', 'level': 937}])

    def test_failed_dim_does_not_stop_other_displays(self):
        import os
        targets = [{'kind': 'ddc', 'bus': '7', 'level': 73},
                   {'kind': 'ddc', 'bus': '8', 'level': 90}]
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                patch.object(brightness, 'idle_targets', return_value=iter(targets)), \
                patch.object(brightness, 'idle_set', side_effect=[OSError('Unavailable'), None]) as setter:
            brightness.idle_brightness('dim')
            self.assertEqual(setter.call_count, 2)
            setter.side_effect = None
            brightness.idle_brightness('restore')
            self.assertEqual([call.args[1] for call in setter.call_args_list], [22, 27, 73, 90])


class BrightnessReadFallbackTests(unittest.TestCase):
    def test_no_ddc_display_returns_cli_unavailable_payload(self):
        for error in (brightness.subprocess.CalledProcessError(1, ['ddcutil', 'getvcp', '10', '--brief']),
                      brightness.subprocess.TimeoutExpired('ddcutil', 8)):
            with self.subTest(error=error), patch.object(brightness, 'backlight', return_value=None), \
                    patch.object(brightness.shutil, 'which', return_value='/usr/bin/ddcutil'), \
                    patch.object(brightness, 'run', side_effect=error):
                self.assertEqual(brightness.status(), {'available': False, 'kind': '',
                    'name': 'Brightness unavailable', 'value': 0, 'error': str(error)})
