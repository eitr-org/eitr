import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
from adoption import identity


class AdoptionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.home = self.base / 'home'
        self.share = self.base / 'share'
        self.home.mkdir()
        self.share.mkdir()
        (self.share / 'defaults').mkdir()
        (self.share / 'defaults/loader').write_text('shipped loader\n')
        (self.share / 'user-defaults.json').write_text(json.dumps({'version': 1, 'layout_version': 2,
            'entries': [{'source': 'distro/defaults/loader', 'target': '${XDG_CONFIG_HOME}/app/loader', 'update': False}]}))
        self.legacy = self.home / '.config/app/code.qml'
        self.legacy.parent.mkdir(parents=True)
        self.legacy.write_text('old code\n')
        self.preference = self.home / '.config/eitr/cursor.json'
        self.preference.parent.mkdir()
        self.preference.write_text('{"family":"breeze","custom":true}\n')
        (self.share / 'legacy-layout.json').write_text(json.dumps({'version': 1,
            'files': {'app/code.qml': {'class': 'C', **identity(self.legacy)}}}))
        self.environment = {**os.environ, 'HOME': str(self.home),
                            'XDG_CONFIG_HOME': str(self.home / '.config'),
                            'XDG_STATE_HOME': str(self.home / '.local/state'),
                            'PYTHONPATH': str(ROOT / 'distro/lib')}

    def run_cli(self, *args):
        return subprocess.run(['python3', str(ROOT / 'distro/bin/eitr-config'),
                               '--defaults', str(self.share), *args], env=self.environment,
                              text=True, capture_output=True, timeout=15)

    def test_dry_run_has_no_writes(self):
        result = self.run_cli('adopt-layout', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.legacy.exists())
        self.assertFalse((self.home / '.local/state').exists())
        self.assertNotIn('breeze', result.stdout)

    def test_changed_code_requires_explicit_decision(self):
        self.legacy.write_text('my edit\n')
        result = self.run_cli('adopt-layout', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.legacy.exists())
        self.assertFalse((self.home / '.local/state').exists())
        result = self.run_cli('adopt-layout', '--apply', '--archive-component', 'app')
        self.assertEqual(result.returncode, 0, result.stderr)
        backup = next((self.home / '.local/state/eitr/layout-backups').glob('*/files/0'))
        self.assertEqual(backup.read_text(), 'my edit\n')

    def test_apply_rerun_and_undo_preserve_preferences(self):
        result = self.run_cli('adopt-layout', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.legacy.exists())
        self.assertEqual(json.loads(self.preference.read_text()), {'version': 1, 'family': 'breeze', 'custom': True})
        self.assertEqual((self.home / '.config/app/loader').read_text(), 'shipped loader\n')
        marker = self.home / '.local/state/eitr/layout.json'
        transaction = json.loads(marker.read_text())['transaction']
        result = self.run_cli('adopt-layout', '--apply')
        self.assertIn('no files changed', result.stdout)
        result = self.run_cli('undo-layout', transaction)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.legacy.read_text(), 'old code\n')
        self.assertEqual(self.preference.read_text(), '{"family":"breeze","custom":true}\n')

    def test_future_preference_schema_aborts_before_retirement(self):
        self.preference.write_text('{"version":2,"family":"future"}')
        result = self.run_cli('adopt-layout', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.legacy.exists())

    def test_symlink_parent_is_not_followed(self):
        self.legacy.unlink()
        self.legacy.parent.rmdir()
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'code.qml').write_text('outside')
        self.legacy.parent.symlink_to(outside)
        result = self.run_cli('adopt-layout', '--apply', '--archive-component', 'app')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((outside / 'code.qml').read_text(), 'outside')

    def test_undo_refuses_new_user_edits(self):
        self.assertEqual(self.run_cli('adopt-layout', '--apply').returncode, 0)
        transaction = json.loads((self.home / '.local/state/eitr/layout.json').read_text())['transaction']
        loader = self.home / '.config/app/loader'
        loader.write_text('new user edit')
        self.assertNotEqual(self.run_cli('undo-layout', transaction).returncode, 0)
        self.assertEqual(loader.read_text(), 'new user edit')

    def test_kept_code_cannot_call_retired_home_code(self):
        helper = self.home / '.config/tool/scripts/run.sh'
        helper.parent.mkdir(parents=True)
        helper.write_text('echo helper\n')
        self.legacy.write_text('exec ~/.config/tool/scripts/run.sh\n')
        (self.share / 'legacy-layout.json').write_text(json.dumps({'version': 1, 'files': {
            'app/code.qml': {'class': 'C', **identity(self.legacy)},
            'tool/scripts/run.sh': {'class': 'C', **identity(helper)}}}))
        result = self.run_cli('adopt-layout', '--dry-run', '--keep-component', 'app')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('.config/tool/scripts', result.stdout)
        result = self.run_cli('adopt-layout', '--dry-run', '--keep-component', 'app', '--keep-component', 'tool')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_loader_replaces_its_legacy_file_in_place_and_empty_folders_go(self):
        loader = self.home / '.config/app/loader'
        loader.write_text('legacy loader\n')
        nested = self.home / '.config/tool/scripts/run.sh'
        nested.parent.mkdir(parents=True)
        nested.write_text('echo\n')
        (self.share / 'legacy-layout.json').write_text(json.dumps({'version': 1, 'files': {
            'app/code.qml': {'class': 'C', **identity(self.legacy)},
            'app/loader': {'class': 'C', **identity(loader)},
            'tool/scripts/run.sh': {'class': 'C', **identity(nested)}}}))
        inode = loader.stat().st_ino
        result = self.run_cli('adopt-layout', '--apply')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(loader.read_text(), 'shipped loader\n')
        self.assertNotEqual(loader.stat().st_ino, inode)
        self.assertFalse((self.home / '.config/tool').exists())
        transaction = json.loads((self.home / '.local/state/eitr/layout.json').read_text())['transaction']
        result = self.run_cli('undo-layout', transaction)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(loader.read_text(), 'legacy loader\n')
        self.assertEqual(nested.read_text(), 'echo\n')

    def test_user_added_files_in_code_folders_are_kept_and_reported(self):
        mine = self.legacy.parent / 'my-helper.sh'
        mine.write_text('echo mine\n')
        result = self.run_cli('adopt-layout', '--apply')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f'kept {mine}', result.stdout)
        self.assertEqual(mine.read_text(), 'echo mine\n')

    def test_old_user_unit_copies_give_way_to_packaged_units(self):
        from adoption import PACKAGED_UNITS
        self.assertEqual(sorted(PACKAGED_UNITS), sorted(path.name for path in (ROOT / 'systemd/user').iterdir()))
        units = self.home / '.config/systemd/user'
        (units / 'timers.target.wants').mkdir(parents=True)
        timer = units / 'nightlight-auto.timer'
        timer.write_text('[Timer]\nOnCalendar=hourly\n')
        link = units / 'timers.target.wants/nightlight-auto.timer'
        link.symlink_to(timer)
        tools = self.base / 'tools'
        tools.mkdir()
        (tools / 'systemctl').write_text('#!/bin/sh\nexit 0\n')
        (tools / 'systemctl').chmod(0o755)
        self.environment['PATH'] = f"{tools}:{self.environment['PATH']}"
        result = self.run_cli('adopt-layout', '--apply')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f'replace {timer}', result.stdout)
        self.assertFalse(timer.exists())
        self.assertEqual(os.readlink(link), '/usr/lib/systemd/user/nightlight-auto.timer')
        transaction = json.loads((self.home / '.local/state/eitr/layout.json').read_text())['transaction']
        self.assertEqual(self.run_cli('undo-layout', transaction).returncode, 0)
        self.assertEqual(timer.read_text(), '[Timer]\nOnCalendar=hourly\n')
        self.assertEqual(os.readlink(link), str(timer))
