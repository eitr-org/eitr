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


class SwayncActivationRemovalTests(unittest.TestCase):
    MIGRATION = ROOT / 'distro/migrations/20261030220000-remove-swaync-activation.py'

    def run_migration(self, text):
        with tempfile.TemporaryDirectory() as directory:
            service = Path(directory) / 'dbus-1/services/org.erikreider.swaync.service'
            if text is not None:
                service.parent.mkdir(parents=True)
                service.write_text(text)
            environment = dict(os.environ, XDG_DATA_HOME=directory,
                               PYTHONPATH=str(ROOT / 'distro/lib'))
            subprocess.run([sys.executable, str(self.MIGRATION)], env=environment, check=True)
            return service.exists()

    def test_the_shipped_file_is_removed(self):
        self.assertFalse(self.run_migration('[D-BUS Service]\nName=org.freedesktop.Notifications\n'
                                            'Exec=/usr/bin/eitr-shell desktop-bar --daemonize\n'))

    def test_a_real_swaync_service_or_no_file_is_left_alone(self):
        self.assertTrue(self.run_migration('[D-BUS Service]\nName=org.freedesktop.Notifications\n'
                                           'Exec=/usr/bin/swaync\n'))
        self.assertFalse(self.run_migration(None))


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


class NeovimTransparentAtStartupMigrationTests(unittest.TestCase):
    MIGRATION = ROOT / 'distro/migrations/20261028200000-nvim-transparent-at-startup.py'

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
        old = current.replace(names['OLD'] + names['ADDED'], names['OLD'])
        self.assertNotEqual(old, current)
        self.assertEqual(self.run_migration(old), current)
        self.assertEqual(self.run_migration(current), current)

    def test_edited_or_missing_files_are_left_alone(self):
        self.assertEqual(self.run_migration('-- my own autocmds\n'), '-- my own autocmds\n')
        self.assertIsNone(self.run_migration(None))


class EitrThemeRenameTests(unittest.TestCase):
    def test_retired_wallpapers_and_fenrir_follow_selected_theme(self):
        migration = ROOT / 'distro/migrations/20261028210000-rename-norse-theme.py'
        names = {'__name__': 'migration_test'}
        import types
        from unittest.mock import patch
        paths = types.ModuleType('eitr_paths')
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            paths.config = paths.cache = paths.data = lambda relative: base / relative
            with patch.dict(sys.modules, eitr_paths=paths):
                exec(compile(migration.read_text().split("update_json(config('eitr/appearance.json')")[0], str(migration), 'exec'), names)
            for theme in ('norse', 'eitr', 'ragnarok', 'nord'):
                names['THEME'] = theme
                for old_theme in ('norse', 'eitr'):
                    for folder in ('backgrounds', 'backgrounds-ultrawide'):
                        for stem in sorted(names['RETIRED'] | {'07-fenrir'}):
                            with self.subTest(theme=theme, old_theme=old_theme, folder=folder, stem=stem):
                                old = f'/usr/share/eitr/themes/{old_theme}/{folder}/{stem}.jpg'
                                expected = '/usr/share/eitr/themes/eitr/backgrounds/02-eitr-runestone.png'
                                if stem == '07-fenrir' and theme == 'ragnarok':
                                    expected = f'/usr/share/eitr/themes/ragnarok/{folder}/05-fenrir.jpg'
                                result = names['renamed'](old)
                                self.assertEqual(result, expected)
                                self.assertEqual(names['renamed'](result), expected)
                for old_theme in ('norse', 'eitr'):
                    for folder, suffix in (('backgrounds', 'png'), ('backgrounds-ultrawide', 'jpg')):
                        runestone = 'eitr-runestone'
                        old = f'/usr/share/eitr/themes/{old_theme}/{folder}/01-{runestone}.{suffix}'
                        expected = f'/usr/share/eitr/themes/eitr/{folder}/02-{runestone}.{suffix}'
                        self.assertEqual(names['renamed'](old), expected)
                        self.assertEqual(names['renamed'](expected), expected)
                self.assertEqual(names['renamed']('/pictures/05-valkyrie.jpg'), '/pictures/05-valkyrie.jpg')

    def test_saved_theme_wallpaper_caches_and_own_theme_follow_rename(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / '.config'
            cache = home / '.cache'
            data = home / '.local/share'
            preference = config / 'eitr/appearance.json'
            preference.parent.mkdir(parents=True)
            wallpaper = '/usr/share/eitr/themes/norse/backgrounds/05-valkyrie.jpg'
            preference.write_text(json.dumps({'theme': 'norse', 'wallpaper': wallpaper, 'other': 42}))
            cache.mkdir()
            (cache / 'current-theme').write_text('norse\n')
            (cache / 'current-wallpaper').write_text(wallpaper + '\n')
            (cache / 'current-wallpaper-image').symlink_to(wallpaper)
            marker = data / 'eitr/themes/mine/own-theme.json'
            marker.parent.mkdir(parents=True)
            marker.write_text(json.dumps({'previous': 'norse', 'name': 'Mine'}))
            environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                               XDG_CACHE_HOME=str(cache), XDG_DATA_HOME=str(data),
                               PYTHONPATH=str(ROOT / 'distro/lib'))
            migration = ROOT / 'distro/migrations/20261028210000-rename-norse-theme.py'
            for attempt in range(2):
                subprocess.run([sys.executable, str(migration)], env=environment, check=True)
                values = json.loads(preference.read_text())
                self.assertEqual(values, {'theme': 'eitr', 'wallpaper': '/usr/share/eitr/themes/eitr/backgrounds/02-eitr-runestone.png', 'other': 42})
                self.assertEqual((cache / 'current-theme').read_text(), 'eitr\n')
                self.assertEqual(os.readlink(cache / 'current-wallpaper-image'), values['wallpaper'])
                self.assertEqual(json.loads(marker.read_text())['previous'], 'eitr')
            preference.write_text(json.dumps({'theme': 'nord', 'wallpaper': '/pictures/mine.jpg'}))
            subprocess.run([sys.executable, str(migration)], env=environment, check=True)
            self.assertEqual(json.loads(preference.read_text()), {'theme': 'nord', 'wallpaper': '/pictures/mine.jpg'})


class NeovimLocalThemeMigrationTests(NeovimShippedThemesMigrationTests):
    MIGRATION = ROOT / 'distro/migrations/20261028220000-nvim-local-theme.py'

    def test_the_previously_shipped_file_becomes_the_current_one(self):
        names = {}
        exec(compile(self.MIGRATION.read_text().split('base = os.environ')[0], str(self.MIGRATION), 'exec'), names)
        current = (ROOT / 'nvim/lua/config/desktop_theme.lua').read_text()
        self.assertEqual(names['NEW'], current)
        self.assertEqual(self.run_migration(names['OLD']), current)
        self.assertEqual(self.run_migration(current), current)
        edited = names['OLD'] + '-- custom settings\n'
        self.assertEqual(self.run_migration(edited), edited)


class GraphiteRemovalTests(unittest.TestCase):
    def test_only_retired_selection_calls_standard_theme_switch(self):
        import json
        import runpy
        migration = ROOT / 'distro/migrations/20261028230000-remove-graphite-theme.py'
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            preference = home / '.config/eitr/appearance.json'
            preference.parent.mkdir(parents=True)
            cache = home / '.cache/current-theme'
            cache.parent.mkdir()
            environment = dict(HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_CACHE_HOME=str(home / '.cache'), EITR_CODE_ROOT=str(ROOT))
            with patch.dict(os.environ, environment), patch('subprocess.run') as switch:
                for saved in ('graphite', 'eitr', 'nord', None):
                    for cached in ('graphite', 'nord', None):
                        for path in (preference, cache):
                            path.unlink(missing_ok=True)
                        if saved:
                            preference.write_text(json.dumps({'theme': saved, 'other': 42}))
                        if cached:
                            cache.write_text(cached + '\n')
                        before = preference.read_bytes() if preference.exists() else None
                        switch.reset_mock()
                        runpy.run_path(str(migration))
                        self.assertEqual(switch.call_count, int((saved or cached) == 'graphite'))
                        if switch.called:
                            args, kwargs = switch.call_args
                            self.assertEqual(args[0], ['bash', str(ROOT / 'walker/scripts/actions/style/apply.sh'), 'eitr'])
                            self.assertTrue(kwargs['check'])
                            self.assertEqual(kwargs['env']['EITR_NO_SESSION'], '1')
                        self.assertEqual(preference.read_bytes() if preference.exists() else None, before)

    @unittest.skipUnless(Path('/usr/share/Kvantum').is_dir(), 'the real theme switch needs the installed Kvantum themes')
    def test_retired_selection_applies_eitr_default_and_preserves_preferences(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / 'config'
            (config / 'swayosd').mkdir(parents=True)
            preference = config / 'eitr/appearance.json'
            preference.parent.mkdir()
            preference.write_text(json.dumps({'theme': 'graphite', 'wallpaper': '/gone.jpg',
                                               'barColor': 'theme', 'other': 42}))
            environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                               XDG_CACHE_HOME=str(home / 'cache'), XDG_DATA_HOME=str(home / 'data'),
                               XDG_STATE_HOME=str(home / 'state'), XDG_RUNTIME_DIR=str(home),
                               EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'),
                               PYTHONPATH=str(ROOT / 'distro/lib'), GSETTINGS_BACKEND='memory',
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
            migration = ROOT / 'distro/migrations/20261028230000-remove-graphite-theme.py'
            for attempt in range(2):
                result = subprocess.run([sys.executable, str(migration)], env=environment,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                values = json.loads(preference.read_text())
                self.assertEqual(values['theme'], 'eitr')
                self.assertEqual(Path(values['wallpaper']).name, '01-primordial-drop.jpg')
                self.assertTrue(Path(values['wallpaper']).is_file())
                self.assertEqual(values['barColor'], 'theme')
                self.assertEqual(values['other'], 42)
                self.assertEqual((config / 'theme/current/neovim.lua').read_text(),
                                 (ROOT / 'themes/eitr/neovim.lua').read_text())
