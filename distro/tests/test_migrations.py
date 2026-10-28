import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import migrations

ROOT = Path(__file__).resolve().parents[2]


class MigrationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / 'share/migrations').mkdir(parents=True)
        self.state = self.root / 'state'
        patcher = patch.dict(os.environ, {'EITR_CODE_ROOT': str(self.root / 'share'),
                                          'XDG_STATE_HOME': str(self.state)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def migration(self, name, body):
        path = self.root / 'share/migrations' / name
        path.write_text(body)
        return path

    def test_pending_migrations_run_once_in_name_order(self):
        log = self.root / 'order'
        self.migration('20270102000000-second.py', f'open({str(log)!r}, "a").write("second\\n")\n')
        self.migration('20270101000000-first.py', f'open({str(log)!r}, "a").write("first\\n")\n')
        self.migration('notes.py', 'raise SystemExit(1)\n')
        self.assertEqual(migrations.run_pending(), ['20270101000000-first.py', '20270102000000-second.py'])
        self.assertEqual(migrations.run_pending(), [])
        self.assertEqual(log.read_text(), 'first\nsecond\n')

    def test_a_failure_stops_the_run_and_retries_later(self):
        self.migration('20270101000000-broken.py', 'raise SystemExit(3)\n')
        later = self.migration('20270102000000-later.py', 'pass\n')
        real_run = migrations.subprocess.run
        notices = []

        def run(command, **kwargs):
            if command[0] == 'notify-send':
                notices.append(command)
                return migrations.subprocess.CompletedProcess(command, 0)
            return real_run(command, **kwargs)

        with patch.object(migrations.subprocess, 'run', side_effect=run):
            self.assertEqual(migrations.run_pending(), [])
        self.assertEqual(len(notices), 1)
        self.assertFalse(migrations.marker(later).exists())
        self.assertIn('exit 3', (self.state / 'eitr/migrations.log').read_text())

    def test_fresh_homes_mark_every_shipped_migration_done(self):
        self.migration('20270101000000-old-shape.py', 'raise SystemExit(1)\n')
        migrations.mark_all()
        self.assertEqual(migrations.run_pending(), [])

    def test_migrations_ship_in_the_package_runtime(self):
        from layout import Layout
        layout = Layout(ROOT)
        self.assertTrue(layout.classify('distro/migrations/20270101000000-example.py')['runtime'])
        self.assertFalse(layout.classify('distro/migrations/README.md')['runtime'])



class LockscreenRenameTests(unittest.TestCase):
    def run_migration(self, selected, migration='20261014160000-rename-lockscreen-designs.py'):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)
            state = config / 'lockscreen/selected'
            if selected is not None:
                state.parent.mkdir(parents=True)
                state.write_text(selected + '\n')
            environment = dict(os.environ, XDG_CONFIG_HOME=str(config), PYTHONPATH=str(ROOT / 'distro/lib'))
            subprocess.run([sys.executable, str(ROOT / 'distro/migrations' / migration)],
                           env=environment, check=True)
            return state.read_text().strip() if state.exists() else None

    def test_renamed_designs_follow_their_new_ids(self):
        self.assertEqual(self.run_migration('last-of-us'), 'ivy-window')
        self.assertEqual(self.run_migration('nier-automata'), 'sandstone')

    def test_other_selections_and_missing_state_stay_unchanged(self):
        self.assertEqual(self.run_migration('clockwork/tape'), 'clockwork/tape')
        self.assertIsNone(self.run_migration(None))

    def test_retired_designs_move_to_the_default(self):
        for retired in ('ivy-window', 'sandstone', 'clockwork/orbital', 'sword'):
            self.assertEqual(self.run_migration(retired, '20261016210000-retired-lockscreen-designs.py'),
                             'clockwork/tape', retired)
        self.assertEqual(self.run_migration('girl-pillow', '20261016210000-retired-lockscreen-designs.py'),
                         'girl-pillow')

    def test_package_hook_renames_the_login_selection(self):
        hook = (ROOT / 'distro/pkg/eitr-desktop/eitr-desktop.install').read_text()
        self.assertIn('desktop-lockscreen-last-of-us', hook)
        self.assertIn('desktop-lockscreen-ivy-window', hook)
        self.assertIn('desktop-lockscreen-nier-automata', hook)
        self.assertIn('desktop-lockscreen-sandstone', hook)


class ZshrcLoaderTests(unittest.TestCase):
    MIGRATION = ROOT / 'distro/migrations/20261014190000-zshrc-local-loader-status.py'

    def run_migration(self, text):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            if text is not None:
                (home / '.zshrc').write_text(text)
            subprocess.run([sys.executable, str(self.MIGRATION)], env=dict(os.environ, HOME=str(home)), check=True)
            return (home / '.zshrc').read_text() if (home / '.zshrc').exists() else None

    def test_old_loader_becomes_the_shipped_if_statement(self):
        shipped = (ROOT / 'distro/defaults/home/.zshrc').read_text()
        old = shipped.split('# An if statement')[0] + ('[[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh" ]] && '
                                                          'source "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh"\n')
        self.assertEqual(self.run_migration(old), shipped)

    def test_edited_or_missing_zshrc_is_left_alone(self):
        self.assertEqual(self.run_migration('alias ll=ls\n'), 'alias ll=ls\n')
        self.assertIsNone(self.run_migration(None))

    def test_shipped_loader_starts_shells_successfully_without_local_file(self):
        loader = (ROOT / 'distro/defaults/home/.zshrc').read_text().splitlines()[-4:]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(['bash', '-c', '\n'.join(loader) + '\necho status=$?'],
                                    env=dict(os.environ, XDG_CONFIG_HOME=directory), capture_output=True, text=True)
        self.assertIn('status=0', result.stdout)


if __name__ == '__main__':
    unittest.main()


class NeovimSnacksTransparencyMigrationTests(unittest.TestCase):
    MIGRATION = ROOT / 'distro/migrations/20261028150000-nvim-snacks-transparent.py'

    def run_migration(self, text):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'nvim/lua/config/autocmds.lua'
            if text is not None:
                target.parent.mkdir(parents=True)
                target.write_text(text)
            subprocess.run([sys.executable, str(self.MIGRATION)], env=dict(os.environ, XDG_CONFIG_HOME=directory), check=True)
            return target.read_text() if target.exists() else None

    def test_the_previously_shipped_file_becomes_the_current_one(self):
        current = (ROOT / 'nvim/lua/config/autocmds.lua').read_text()
        names = {}
        exec(compile(self.MIGRATION.read_text().split('base = os.environ')[0], str(self.MIGRATION), 'exec'), names)
        old = current.replace(names['NEW'], names['OLD'])
        self.assertNotEqual(old, current)
        self.assertEqual(self.run_migration(old), current)
        self.assertEqual(self.run_migration(current), current)

    def test_edited_or_missing_files_are_left_alone(self):
        self.assertEqual(self.run_migration('-- my own autocmds\n'), '-- my own autocmds\n')
        self.assertIsNone(self.run_migration(None))


class NeovimShippedThemesMigrationTests(unittest.TestCase):
    MIGRATION = ROOT / 'distro/migrations/20261027020000-nvim-shipped-themes.py'

    def run_migration(self, text):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'nvim/lua/config/desktop_theme.lua'
            if text is not None:
                target.parent.mkdir(parents=True)
                target.write_text(text)
            subprocess.run([sys.executable, str(self.MIGRATION)], env=dict(os.environ, XDG_CONFIG_HOME=directory), check=True)
            return target.read_text() if target.exists() else None

    def test_the_previously_shipped_file_becomes_the_current_one(self):
        current = (ROOT / 'nvim/lua/config/desktop_theme.lua').read_text()
        names = {}
        exec(compile(self.MIGRATION.read_text().split('base = os.environ')[0], str(self.MIGRATION), 'exec'), names)
        old = current.replace(names['NEW'], names['OLD'])
        self.assertNotEqual(old, current)
        self.assertEqual(self.run_migration(old), current)
        self.assertEqual(self.run_migration(current), current)

    def test_edited_or_missing_files_are_left_alone(self):
        self.assertEqual(self.run_migration('-- my own theme loader\n'), '-- my own theme loader\n')
        self.assertIsNone(self.run_migration(None))
