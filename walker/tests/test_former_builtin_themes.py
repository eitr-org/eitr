"""Package ordering, offline migration and local Store apply coverage."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from home_isolation import setUpModule, tearDownModule
from eitr_paths import cache, config, data, read_settings, theme_paths, write_settings
import eitr_former_themes as migration
from eitr_wallpapers import prune
from eitr_theme_packages import ASSET_FOLDERS, Themes, catalog

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT.with_name('eitr-themes')


class FormerBuiltinThemesTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.old = self.root / 'usr/share/eitr/themes'
        self.archive = self.root / 'var/lib/eitr/former-themes'
        self.enterContext(patch.multiple(migration, OLD=self.old, ARCHIVE=self.archive))
        self.home(self.root / 'home')

    def home(self, home):
        home.mkdir()
        self.enterContext(patch.dict(os.environ, HOME=str(home),
            XDG_CONFIG_HOME=str(home / 'config'), XDG_STATE_HOME=str(home / 'state'),
            XDG_DATA_HOME=str(home / 'data'), XDG_CACHE_HOME=str(home / 'cache'),
            XDG_RUNTIME_DIR=str(home / 'runtime'),
            EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'),
            EITR_NO_SESSION='1', GSETTINGS_BACKEND='memory', DBUS_SESSION_BUS_ADDRESS='disabled:'))
        self.enterContext(patch('pathlib.Path.home', return_value=home))

    def seed(self, identifier):
        folder = self.old / identifier
        (folder / 'backgrounds').mkdir(parents=True)
        Image.new('RGB', (8, 8), 'darkred').save(folder / 'preview.png')
        shutil.copyfile(folder / 'preview.png', folder / 'backgrounds/wall.png')
        shutil.copyfile(ROOT / 'themes/eitr/colors.toml', folder / 'colors.toml')
        (folder / 'display-name').write_text(identifier + '\n')
        (folder / 'eitr-theme.json').write_text(json.dumps(dict(schemaVersion=1,
            id=identifier, name=identifier, description='Migration fixture', version='1.0.0', light=False)))
        return folder

    def package_upgrade(self, package):
        # Execute the actual scriptlet against a temporary package tree, then
        # remove exactly the paths owned by that package as ALPM would.
        script = (ROOT / f'distro/pkg/eitr-{package}/eitr-{package}.install').read_text()
        script = script.replace(str(Path('/usr/share/eitr/themes')), str(self.old))
        script = script.replace(str(Path('/var/lib/eitr/former-themes')), str(self.archive))
        subprocess.run(['bash', '-c', script + '\npre_upgrade 2 1'], check=True)
        for theme in self.old.iterdir():
            for file in theme.iterdir():
                artwork = file.name in ASSET_FOLDERS or file.name == 'preview.png'
                if artwork == (package == 'artwork'):
                    shutil.rmtree(file) if file.is_dir() else file.unlink()

    def test_offline_upgrade_preserves_only_referenced_themes_in_either_order(self):
        for order in [('artwork', 'desktop'), ('desktop', 'artwork')]:
            with self.subTest(order=order):
                self.home(self.root / order[0])
                for identifier in ('afterglow', 'asgard', 'helheim', 'midgard'):
                    self.seed(identifier)
                old_wall = self.old / 'afterglow/backgrounds/wall.png'
                old_display = self.old / 'asgard/backgrounds/wall.png'
                old_lock = self.old / 'helheim/backgrounds/wall.png'
                write_settings(config('eitr/appearance.json'), dict(theme='afterglow', wallpaper=str(old_wall)))
                write_settings(config('eitr/wallpapers.json'), {'assignments': {'DP-1': str(old_display)}, 'perDisplay': True})
                lock = data('eitr/lockscreens/custom/lockscreen.json')
                write_settings(lock, {'picture': old_lock.as_uri(), 'greeting': 'Keep me'})
                cache('eitr').mkdir(parents=True)
                cache('current-wallpaper').write_text(str(old_wall) + '\n')
                cache('current-wallpaper-image').symlink_to(old_wall)
                cache('eitr/hyprpaper-monitors.conf').write_text(f'  path = {old_display}\n')
                config('theme').mkdir()
                config('theme/current').symlink_to(self.old / 'afterglow')
                for package in order:
                    self.package_upgrade(package)
                shutil.rmtree(self.old)
                self.assertFalse(old_wall.exists())
                self.assertEqual(prune(), {})
                self.assertEqual(read_settings(config('eitr/wallpapers.json'))['assignments'],
                                 {'DP-1': str(old_display)})

                with patch.object(Themes, 'repository', side_effect=AssertionError('Network used')), \
                        patch.object(Themes, 'fetch_head', side_effect=AssertionError('Network used')):
                    with patch.object(migration, 'write_settings', side_effect=OSError('Interrupted write')):
                        with self.assertRaisesRegex(OSError, 'Interrupted'):
                            migration.migrate()
                    first_install = (data('eitr/themes/afterglow/preview.png')).stat().st_ino
                    migration.migrate()
                    migration.migrate()

                backend = Themes()
                present = theme_paths()
                self.assertEqual(set(present), {'eitr', 'eitr-light', 'afterglow', 'asgard', 'helheim'})
                self.assertEqual(backend.source('afterglow'), {
                    'url': migration.URL, 'commit': migration.CATALOG_BASE, 'folder': 'afterglow', 'official': True,
                })
                self.assertEqual(present['afterglow'].joinpath('preview.png').stat().st_ino, first_install)
                wallpaper = present['afterglow'] / 'backgrounds/wall.png'
                self.assertEqual(config('theme/current').resolve(), present['afterglow'])
                self.assertEqual(read_settings(config('eitr/appearance.json'))['wallpaper'], str(wallpaper))
                self.assertEqual(cache('current-wallpaper-image').resolve(), wallpaper)
                self.assertEqual(cache('current-wallpaper').read_text(), str(wallpaper) + '\n')
                display = present['asgard'] / 'backgrounds/wall.png'
                self.assertEqual(read_settings(config('eitr/wallpapers.json'))['assignments'], {'DP-1': str(display)})
                self.assertEqual(cache('eitr/hyprpaper-monitors.conf').read_text(), f'  path = {display}\n')
                self.assertEqual(read_settings(lock)['picture'], (present['helheim'] / 'backgrounds/wall.png').as_uri())
                self.assertEqual(read_settings(lock)['greeting'], 'Keep me')
                for identifier in ('eitr', 'eitr-light'):
                    with self.assertRaisesRegex(ValueError, 'Built-in'):
                        backend.remove(identifier)
                with self.assertRaisesRegex(ValueError, 'current theme'):
                    backend.remove('afterglow')
                self.assertEqual(backend.remove('asgard'), 'asgard')
                self.assertFalse(present['asgard'].exists())

    def git(self, repository, *arguments):
        return subprocess.check_output(['git', '-C', str(repository), *arguments], text=True).strip()

    def commit(self, repository):
        self.git(repository, 'add', '.')
        self.git(repository, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Fixture')
        return self.git(repository, 'rev-parse', 'HEAD')

    def test_migrated_theme_updates_from_its_catalog_base(self):
        repository = self.root / 'repo'
        repository.mkdir()
        self.git(repository, 'init', '-q')
        index = repository / 'eitr-catalog.json'
        index.write_text('[]')
        base = self.commit(repository)

        original = self.seed('afterglow')
        shutil.copytree(original, repository / 'afterglow')
        index.write_text(json.dumps(catalog(repository)))
        release = self.commit(repository)
        write_settings(config('eitr/appearance.json'), {'theme': 'afterglow'})
        for package in ('artwork', 'desktop'):
            self.package_upgrade(package)
        with patch.object(migration, 'CATALOG_BASE', base):
            migration.migrate()

        backend = Themes(allow_file=True)
        open_repository, open_head = backend.repository, backend.fetch_head
        with patch.object(backend, 'repository', side_effect=lambda address: open_repository(repository.as_uri())), \
                patch.object(backend, 'fetch_head', side_effect=lambda address, **options: open_head(repository.as_uri(), **options)):
            self.assertEqual(backend.check(preview=True), {'afterglow': 1})
            self.assertEqual(backend.update('afterglow'), ['afterglow'])
            self.assertEqual(backend.check(), {'afterglow': 0})
        self.assertEqual(backend.source('afterglow')['commit'], release)

    @unittest.skipUnless((STORE / 'ragnarok/eitr-theme.json').is_file(), 'requires the migrated Store checkout')
    def test_store_apply_matches_former_builtin(self):
        # Use the local Store package through the production Git installer, with
        # official trust enabled for this local transport fixture.
        repository = self.root / 'repo'
        shutil.copytree(STORE / 'ragnarok', repository / 'ragnarok')
        (repository / 'eitr-catalog.json').write_text(json.dumps(catalog(repository)))
        self.git(repository, 'init', '-q')
        self.commit(repository)
        backend = Themes(allow_file=True)
        with patch('eitr_theme_packages.official', return_value=True):
            backend.install(repository.as_uri(), ['ragnarok'])
        installed = backend.folder / 'ragnarok'
        config('swayosd').mkdir(parents=True)
        applied = subprocess.run(['bash', str(ROOT / 'walker/scripts/actions/style/apply.sh'), 'ragnarok'],
                                 capture_output=True, text=True)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)

        current = config('theme/current')
        for name in ('icons.theme', 'vscode.json', 'vscode.vsix', 'neovim.lua',
                     'btop.theme', 'dolphin.theme', 'colors.toml'):
            self.assertEqual((current / name).read_bytes(), (installed / name).read_bytes())
        # The former built-in files, before the Store generated them.
        expected = json.loads(Path(__file__).with_name('ragnarok-built-in-digests.json').read_text())
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((current / name).read_bytes()).hexdigest(), digest, name)
        self.assertEqual(Path(read_settings(config('eitr/appearance.json'))['wallpaper']).name,
                         '01-blood-eclipse.jpg')


if __name__ == '__main__':
    unittest.main()
