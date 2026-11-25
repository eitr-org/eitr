import importlib.machinery
import importlib.util
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import generated
from generated import refresh_after_upgrade, walker_view


class GeneratedLayoutTests(unittest.TestCase):
    def test_new_layouts_arrive_without_replacing_user_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'share/walker/themes/current'
            source.mkdir(parents=True)
            (source / 'layout.xml').write_text('version one')
            config = root / 'config'
            state = root / 'state'
            with patch.dict(os.environ, {'EITR_CODE_ROOT': str(root / 'share'),
                                         'XDG_CONFIG_HOME': str(config), 'XDG_STATE_HOME': str(state)}):
                walker_view()
                target = config / 'walker/themes/current/layout.xml'
                self.assertTrue(target.is_symlink())
                (source / 'layout.xml').write_text('version two')
                self.assertEqual(target.read_text(), 'version two')
                (source / 'item_new.xml').write_text('new layout')
                walker_view()
                self.assertTrue((target.parent / 'item_new.xml').is_symlink())
                target.unlink()
                target.write_text('user override')
                walker_view()
                self.assertEqual(target.read_text(), 'user override')

    def test_removed_owned_links_are_pruned_not_user_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'share/walker/themes/current'
            source.mkdir(parents=True)
            (source / 'item_old.xml').write_text('old')
            with patch.dict(os.environ, {'EITR_CODE_ROOT': str(root / 'share'),
                                         'XDG_CONFIG_HOME': str(root / 'config'),
                                         'XDG_STATE_HOME': str(root / 'state')}):
                walker_view()
                (source / 'item_old.xml').unlink()
                walker_view()
                self.assertFalse((root / 'config/walker/themes/current/item_old.xml').is_symlink())

    def test_theme_output_regenerates_once_per_package_version_with_a_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'share').mkdir()
            (root / 'share/version').write_text('1.0\n')
            config = root / 'config'
            (config / 'theme/current').mkdir(parents=True)
            (config / 'theme/current/colors.toml').write_text('accent = "#123456"\n')
            (config / 'kitty').mkdir()
            (config / 'kitty/theme.conf').write_text('my tweak\n')
            state = root / 'state'
            with patch.dict(os.environ, {'EITR_CODE_ROOT': str(root / 'share'),
                                         'XDG_CONFIG_HOME': str(config), 'XDG_STATE_HOME': str(state)}), \
                    patch.object(generated.subprocess, 'run') as run:
                self.assertEqual(refresh_after_upgrade(), '1.0')
                self.assertIsNone(refresh_after_upgrade())
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.kwargs['env']['EITR_NO_SESSION'], '1')
                (root / 'share/version').write_text('1.1\n')
                self.assertEqual(refresh_after_upgrade(), '1.1')
                self.assertEqual(run.call_count, 2)
            backups = list((state / 'eitr/generated-backups').glob('*-1.0/kitty/theme.conf'))
            self.assertEqual([backup.read_text() for backup in backups], ['my tweak\n'])

    def test_failed_theme_generation_does_not_stamp_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            colors = root / 'config/theme/current/colors.toml'
            colors.parent.mkdir(parents=True)
            colors.touch()
            stamp = root / 'version'
            stamp.write_text('1.1\n')
            ledger = root / 'state/eitr/session.json'
            ledger.parent.mkdir(parents=True)
            ledger.write_text('{"package":"1.0"}')
            with patch.object(generated, 'code', side_effect=lambda relative: root / relative), \
                    patch.dict(os.environ, {'XDG_CONFIG_HOME': str(root / 'config'),
                                             'XDG_STATE_HOME': str(root / 'state')}), \
                    patch.object(generated.subprocess, 'run') as run:
                run.side_effect = [subprocess.CalledProcessError(1, 'generate.sh'), None]
                with self.assertRaises(subprocess.CalledProcessError):
                    refresh_after_upgrade()
                self.assertEqual(generated.read_settings(ledger)['package'], '1.0')
                self.assertEqual(refresh_after_upgrade(), '1.1')
                self.assertEqual(run.call_count, 2)

    def test_each_preparation_step_has_a_deadline_and_failure_is_logged(self):
        script = Path(__file__).resolve().parents[1] / 'bin/eitr-session'
        loader = importlib.machinery.SourceFileLoader('test_session', str(script))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        session = importlib.util.module_from_spec(spec)
        loader.exec_module(session)
        with tempfile.TemporaryFile(mode='w+') as log, patch.object(session.subprocess, 'run') as run:
            run.side_effect = [subprocess.CompletedProcess([], status) for status in (124, 0, 1, 0, 0, 0, 0)]
            self.assertEqual(session.prepare(log), 1)
            self.assertEqual([call.args[0][-1] for call in run.call_args_list], list(session.STEPS))
            for call in run.call_args_list:
                self.assertEqual(call.args[0][:2], ['timeout', '--kill-after=2s'])
                self.assertGreater(int(call.args[0][2][:-1]), 0)
            log.seek(0)
            self.assertIn('walker-layouts failed (exit 124)', log.read())

    def test_walker_generation_failure_keeps_the_previous_css(self):
        checkout = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            style = root / 'walker/themes/current/style.css'
            style.parent.mkdir(parents=True)
            style.write_text('previous usable stylesheet')
            python = root / 'python3'
            python.write_text('#!/bin/sh\ncase "$1" in *display-primary.py) exit 7 ;; esac\n')
            python.chmod(0o755)
            environment = dict(os.environ, HOME=directory, XDG_CONFIG_HOME=directory,
                               EITR_CODE_ROOT=str(checkout), WALKER_THEME_DIR=str(style.parent),
                               PATH=directory + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['bash', str(checkout / 'walker/scripts/themes/walker.sh')],
                                    env=environment, capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertEqual(style.read_text(), 'previous usable stylesheet')
            self.assertEqual(list(style.parent.glob('.style.*')), [])
