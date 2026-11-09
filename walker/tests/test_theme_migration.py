"""Deferred former-built-in migration and readers, with no network or live desktop."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule
import eitr_theme_migration as migration
from eitr_paths import cache, config, state, theme_paths
from eitr_theme_packages import Themes, catalog, SOURCE
import migrations

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'distro/migrations/20261103120000-extra-theme-packages.py'


class ThemeMigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        environment = dict(HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / 'config'),
                           XDG_CACHE_HOME=str(self.home / 'cache'), XDG_DATA_HOME=str(self.home / 'data'),
                           XDG_STATE_HOME=str(self.home / 'state'), EITR_CODE_ROOT=str(ROOT))
        patcher = patch.dict(os.environ, environment)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('pathlib.Path.home', return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.root / 'repository'
        self.repo.mkdir()
        self.url = self.repo.as_uri()
        from PIL import Image
        for theme in migration.THEMES:
            folder = self.repo / theme
            (folder / 'backgrounds').mkdir(parents=True)
            shutil.copy(ROOT / 'themes/eitr/colors.toml', folder / 'colors.toml')
            (folder / 'display-name').write_text(theme)
            Image.new('RGB', (8, 8), 'green').save(folder / 'preview.png')
            Image.new('RGB', (16, 16), 'green').save(folder / 'backgrounds/wall.png')
            (folder / 'eitr-theme.json').write_text(json.dumps(dict(schemaVersion=1, id=theme,
                name=theme, description='Migration fixture', version='1', light=False)))
        (self.repo / 'eitr-catalog.json').write_text(json.dumps(catalog(self.repo)))
        for arguments in [('init', '-q'), ('config', 'uploadpack.allowFilter', 'true'),
                          ('config', 'uploadpack.allowAnySHA1InWant', 'true'), ('add', '.'),
                          ('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture')]:
            subprocess.run(['git', *arguments], cwd=self.repo, check=True, capture_output=True)
        self.backend = Themes(allow_file=True, git_timeout=2)
        config('theme').mkdir(parents=True)
        shutil.copytree(ROOT / 'themes/eitr', config('theme/current'))
        config('theme/current/display-name').write_text('Nord\n')
        config('eitr').mkdir()
        self.preference = config('eitr/appearance.json')
        self.preference.write_text(json.dumps({'theme': 'nord', 'wallpaper': str(config('theme/current/backgrounds/01-aurora-fjord.jpg')), 'other': 42}))
        cache().mkdir()
        cache('current-theme').write_text('nord\n')
        self.before = {path: path.read_bytes() for path in config().rglob('*') if path.is_file()}

    def retry(self):
        return migration.retry(backend=self.backend, url=self.url)

    def assert_appearance_unchanged(self):
        self.assertEqual({path: path.read_bytes() for path in config().rglob('*') if path.is_file()}, self.before)
        self.assertEqual(cache('current-theme').read_text(), 'nord\n')

    def test_all_twelve_current_first_one_repository_and_completed_removal_stays_removed(self):
        with patch.object(migrations, 'shipped', return_value=[SCRIPT]):
            self.assertEqual(migrations.run_pending(), [SCRIPT.name])
        with patch.object(self.backend, 'repository', wraps=self.backend.repository) as repository, \
                patch.object(self.backend, 'git', wraps=self.backend.git) as git:
            installed = self.retry()
        self.assertEqual(repository.call_count, 1)
        self.assertEqual(sum(call.args[1] == 'clone' for call in git.call_args_list), 1)
        self.assertEqual(sum(call.args[1] == 'fetch' for call in git.call_args_list), 1)
        self.assertEqual(installed[0], 'nord')
        self.assertEqual(set(installed), set(migration.THEMES))
        self.assertFalse(migration.pending().exists())
        self.assert_appearance_unchanged()
        self.backend.remove('moss')
        with patch.object(migrations, 'shipped', return_value=[SCRIPT]):
            self.assertEqual(migrations.run_pending(), [])
        self.assertEqual(self.retry(), [])
        self.assertFalse((self.backend.folder / 'moss').exists())

    def test_already_present_themes_are_skipped(self):
        self.backend.install(self.url, ['moss', 'daylight'])
        shutil.copytree(self.repo / 'nord', config('themes/nord'))
        migration.enqueue()
        installed = self.retry()
        self.assertEqual(set(installed), set(migration.THEMES) - {'moss', 'daylight', 'nord'})
        self.assertFalse(migration.pending().exists())

    def test_offline_does_not_block_later_migration_and_next_login_retries(self):
        later = self.root / '20261103130000-later.py'
        later.write_text('pass\n')
        with patch.object(migrations, 'shipped', return_value=[SCRIPT, later]):
            self.assertEqual(migrations.run_pending(), [SCRIPT.name, later.name])
        with patch.object(self.backend, 'repository', side_effect=subprocess.TimeoutExpired('git', 2)):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.retry()
        self.assertTrue(migration.pending().exists())
        self.assertTrue(migrations.marker(later).exists())
        self.assert_appearance_unchanged()
        self.assertEqual(set(self.retry()), set(migration.THEMES))
        self.assertFalse(migration.pending().exists())

    def test_partial_progress_is_persisted_before_failed_download(self):
        migration.enqueue()
        self.backend.install(self.url, ['moss'])
        with patch.object(self.backend, 'install', side_effect=OSError('Offline')):
            with self.assertRaises(OSError):
                self.retry()
        self.backend.remove('moss')
        self.assertNotIn('moss', self.retry())
        self.assertFalse((self.backend.folder / 'moss').exists())

    def test_fresh_adoption_never_enqueues_or_downloads(self):
        with patch.object(migrations, 'shipped', return_value=[SCRIPT]):
            migrations.mark_all()
            self.assertEqual(migrations.run_pending(), [])
        with patch.object(migration.subprocess, 'Popen') as worker:
            migration.start_retry()
        worker.assert_not_called()
        self.assertEqual(self.retry(), [])
        self.assertFalse(self.backend.folder.exists())

    def test_background_start_never_waits(self):
        migration.enqueue()
        with patch.object(migration.subprocess, 'Popen') as worker:
            migration.start_retry()
        self.assertTrue(worker.call_args.kwargs['start_new_session'])

    def test_missing_current_folder_readers_and_cursor_auto(self):
        self.assertNotIn('nord', theme_paths())
        self.assertNotIn('nord', {row['id'] for row in self.backend.installed()})
        result = subprocess.run([sys.executable, str(ROOT / 'quickshell/desktop-bar/scripts/appearance-items.py'), 'theme'],
                                capture_output=True, text=True, check=True)
        self.assertNotIn('nord', {row['value'] for row in json.loads(result.stdout)['items']})
        result = subprocess.run([sys.executable, str(ROOT / 'distro/bin/eitr'), 'theme', 'list'],
                                capture_output=True, text=True, check=True)
        self.assertNotIn('nord', result.stdout)
        commands = self.root / 'bin'
        commands.mkdir()
        notice = commands / 'notify-send'
        notice.write_text('#!/bin/sh\nexit 0\n')
        notice.chmod(0o755)
        result = subprocess.run(['bash', str(ROOT / 'walker/scripts/actions/style/apply.sh'), 'nord'],
            env=dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'], EITR_NO_SESSION='1'),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assert_appearance_unchanged()
        cursor = runpy.run_path(str(ROOT / 'walker/scripts/actions/style/cursor.py'), run_name='cursor_test')
        self.assertEqual(cursor['resolve']({'color':'auto', 'family':'bibata'}), 'Bibata-Modern-Classic')
        config('theme/current/light.mode').touch()
        self.assertEqual(cursor['resolve']({'color':'auto', 'family':'bibata'}), 'Bibata-Modern-Ice')
        import eitr_own_style
        self.assertTrue(eitr_own_style.reference_integration(True)['neovim']['eitr'])

    @unittest.skipUnless(shutil.which('luajit'), 'Walker uses LuaJIT')
    def test_walker_menu_omits_missing_current_source(self):
        commands = self.root / 'bin'
        commands.mkdir()
        (commands / 'eitr-paths').symlink_to(ROOT / 'distro/bin/eitr-launch')
        script = self.root / 'walker-menu.lua'
        script.write_text("""
local entries = dofile(os.getenv('EITR_CODE_ROOT') .. '/elephant/theme-entries.lua')('dark')()
assert(#entries == 12)
for _, entry in ipairs(entries) do
    assert(entry.Value ~= 'nord')
    local preview = assert(io.open(entry.Preview, 'r'))
    preview:close()
end
""")
        environment = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'],
                           EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'))
        subprocess.run(['luajit', str(script)], env=environment, check=True, capture_output=True)

    def test_login_defers_regeneration_and_starts_retry_after_settings(self):
        migration.enqueue()
        with patch('generated.walker_view'), patch('generated.refresh_after_upgrade') as refresh, \
                patch('migrations.run_pending'), patch('subprocess.run'), \
                patch('subprocess.Popen') as launched:
            runpy.run_path(str(ROOT / 'distro/bin/eitr-session'), run_name='session_test')
        refresh.assert_not_called()
        self.assertEqual(launched.call_count, 2)
        self.assertEqual(launched.call_args.args[0][-1], str(ROOT / 'distro/lib/eitr_theme_migration.py'))
        self.assert_appearance_unchanged()

    def test_offline_fetch_fails_fast_and_keeps_retry_state(self):
        import time
        migration.enqueue()
        missing_repository = (self.root / 'offline').as_uri()
        started = time.monotonic()
        with self.assertRaises(subprocess.CalledProcessError):
            migration.retry(backend=self.backend, url=missing_repository)
        self.assertLess(time.monotonic() - started, 2)
        self.assertTrue(migration.pending().exists())
        self.assert_appearance_unchanged()

    def test_package_listing_uses_official_address_and_cli_sees_installed_packages(self):
        # Redirect only the transport to a file fixture, retaining production URL trust checks.
        real_git = self.backend.git
        def fixture_git(root, *arguments, **options):
            return real_git(root, *(self.url if argument == migration.URL else argument
                                    for argument in arguments), **options)
        self.backend.git = fixture_git
        migration.enqueue()
        migration.retry(backend=self.backend)
        for theme in migration.THEMES:
            record = json.loads((self.backend.folder / theme / SOURCE).read_text())
            self.assertEqual(record['url'], migration.URL)
        self.assertTrue(all(row['kind'] == 'official' for row in self.backend.installed() if row['id'] in migration.THEMES))
        result = subprocess.run([sys.executable, str(ROOT / 'distro/bin/eitr'), 'theme', 'list'],
                                capture_output=True, text=True, check=True)
        self.assertIn('nord', result.stdout)

    def test_worker_swallows_offline_failure_without_notifications(self):
        migration.enqueue()
        with patch('eitr_theme_packages.Themes', return_value=self.backend), \
                patch.object(self.backend, 'repository', side_effect=subprocess.TimeoutExpired('git', 2)), \
                patch('subprocess.Popen') as launched:
            runpy.run_path(str(ROOT / 'distro/lib/eitr_theme_migration.py'), run_name='__main__')
        launched.assert_not_called()
        self.assertTrue(migration.pending().exists())
        self.assert_appearance_unchanged()

    def test_own_theme_returns_to_installed_extra_and_handles_its_removal(self):
        import eitr_own_style
        self.backend.install(self.url, ['nord'])
        picture = next(config('theme/current/backgrounds').glob('*.jpg'))
        directory = eitr_own_style.create_theme('Mine', str(picture), previous='nord')
        self.assertEqual(eitr_own_style.fallback_theme(directory.name), 'nord')
        cache('current-theme').write_text('eitr\n')
        self.backend.remove('nord')
        self.assertEqual(eitr_own_style.fallback_theme(directory.name), 'eitr')
