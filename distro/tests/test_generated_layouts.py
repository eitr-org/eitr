from pathlib import Path
import os
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
