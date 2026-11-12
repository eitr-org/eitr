"""Eitr's screen-share picker answers only Record's one-time request; the migration opts existing homes in."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
PICKER = ROOT / 'hypr/scripts/share-picker.py'
MIGRATION = ROOT / 'distro/migrations/20261112150000-share-picker.py'
OUTPUTS = '9:DP-3:0:0:2560:1080;7:HDMI-A-1:320:1080:1920:1080;'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


picker = load(PICKER, 'share_picker')
migration = load(MIGRATION, 'share_picker_migration')


class SharePickerTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / 'eitr/share-request.json'
        self.path.parent.mkdir()

    def tearDown(self):
        self.folder.cleanup()

    def request(self, output='HDMI-A-1', remaining=1, expires_in=30):
        self.path.write_text(json.dumps({'output': output, 'remaining': remaining, 'expires': time.time() + expires_in}))

    def test_reads_the_portal_display_list(self):
        self.assertEqual(picker.outputs(OUTPUTS), {'DP-3', 'HDMI-A-1'})
        self.assertEqual(picker.outputs(''), set())

    def test_answers_once_per_screen_source_then_stops(self):
        self.request(remaining=2)
        available = picker.outputs(OUTPUTS)
        self.assertEqual(picker.take_request(self.path, available), 'HDMI-A-1')
        self.assertTrue(self.path.exists())
        self.assertEqual(picker.take_request(self.path, available), 'HDMI-A-1')
        self.assertFalse(self.path.exists())
        self.assertIsNone(picker.take_request(self.path, available))

    def test_expired_missing_or_gone_display_falls_back_to_the_picker(self):
        available = picker.outputs(OUTPUTS)
        self.request(expires_in=-1)
        self.assertIsNone(picker.take_request(self.path, available))
        self.assertFalse(self.path.exists())
        self.request(output='DP-9')
        self.assertIsNone(picker.take_request(self.path, available))
        self.path.write_text('not json')
        self.assertIsNone(picker.take_request(self.path, available))
        self.assertFalse(self.path.exists())

    def run_picker(self, extra):
        fake = Path(self.folder.name) / 'hyprland-share-picker'
        fake.write_text('#!/bin/sh\necho "native $*"\n')
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        code = PICKER.read_text().replace("PICKER = '/usr/bin/hyprland-share-picker'", f"PICKER = {str(fake)!r}")
        script = Path(self.folder.name) / 'picker.py'
        script.write_text(code)
        environment = dict(os.environ, XDG_RUNTIME_DIR=self.folder.name, XDPH_OUTPUT_SHARING_LIST=OUTPUTS, **extra)
        return subprocess.run([sys.executable, str(script), '--allow-token'], env=environment,
                              capture_output=True, text=True, check=True).stdout

    def test_selection_line_or_native_picker(self):
        self.request(output='DP-3')
        self.assertEqual(self.run_picker({}), '[SELECTION]r/screen:DP-3\n')
        self.assertEqual(self.run_picker({}), 'native --allow-token\n')


class MigrationTests(unittest.TestCase):
    def run_migration(self, existing):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'hypr/xdph.conf'
            target.parent.mkdir()
            target.write_text(existing)
            environment = dict(os.environ, XDG_CONFIG_HOME=folder, PATH='/nonexistent')
            subprocess.run([sys.executable, str(MIGRATION)], env=environment, check=True)
            return target.read_text()

    def test_previous_default_gains_the_picker_and_edits_stay(self):
        self.assertEqual(self.run_migration(migration.PREVIOUS), migration.CURRENT)
        self.assertEqual(migration.CURRENT, (ROOT / 'distro/defaults/hypr/xdph.conf').read_text())
        edited = 'screencopy {\n    allow_token_by_default = false\n}\n'
        self.assertEqual(self.run_migration(edited), edited)


if __name__ == '__main__':
    unittest.main()
