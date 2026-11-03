"""Theme package contracts and sparse transfers against local Git fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule
from eitr_paths import theme_paths
from eitr_theme_packages import Themes, catalog, manifest, validate, official, SOURCE

ROOT = Path(__file__).resolve().parents[2]


class ThemePackagesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.environment = patch.dict(os.environ, dict(HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / '.config'),
            XDG_STATE_HOME=str(self.home / '.local/state'), XDG_DATA_HOME=str(self.home / '.local/share'), XDG_CACHE_HOME=str(self.home / '.cache'),
            EITR_CODE_ROOT=str(self.root / 'builtin')))
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.home_patch = patch('pathlib.Path.home', return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.run_git('init', '-q')
        self.run_git('config', 'user.name', 'Fixture')
        self.run_git('config', 'user.email', 'fixture@example.invalid')
        self.run_git('config', 'uploadpack.allowFilter', 'true')
        self.run_git('config', 'uploadpack.allowAnySHA1InWant', 'true')
        for theme_id in ('alpha', 'beta', 'gamma'):
            self.theme(theme_id)
        self.save()
        import shutil
        shutil.copytree(ROOT / 'themes', self.root / 'builtin/themes',
                        ignore=shutil.ignore_patterns(*[folder.name for folder in (ROOT / 'themes').iterdir() if folder.is_dir()]))
        self.backend = Themes(allow_file=True)
        self.url = self.repo.as_uri()

    def run_git(self, *arguments):
        return subprocess.check_output(['git', *arguments], cwd=self.repo, text=True, stderr=subprocess.PIPE).strip()

    def theme(self, theme_id):
        from PIL import Image
        folder = self.repo / 'themes' / theme_id
        folder.mkdir(parents=True)
        (folder / 'backgrounds').mkdir()
        Image.new('RGB', (8, 8), color={'alpha':'red','beta':'blue','gamma':'green'}[theme_id]).save(folder / 'preview.png')
        Image.new('RGB', (16, 16), color={'alpha':'red','beta':'blue','gamma':'green'}[theme_id]).save(folder / 'backgrounds/wall.png')
        (folder / 'colors.toml').write_text((ROOT / 'themes/eitr/colors.toml').read_text())
        (folder / 'display-name').write_text(theme_id + '\n')
        (folder / 'eitr-theme.json').write_text(json.dumps(dict(schemaVersion=1,id=theme_id,name=theme_id,
            description='Fixture theme',version='1',light=False)))
        return folder

    def save(self):
        (self.repo / 'eitr-catalog.json').write_text(json.dumps(catalog(self.repo)))
        self.run_git('add', '.')
        self.run_git('commit', '-qm', 'Fixture')

    def test_git_address_review_stages_data_only_and_pins_commit(self):
        choices = self.backend.prepare_review(self.url)
        self.assertEqual(len(choices['choices']), 3)
        review = self.backend.prepare_review(self.url, 'alpha')
        self.assertTrue(review['dataOnly'])
        self.assertFalse((self.backend.folder / 'alpha').exists())
        (self.repo / 'themes/alpha/artwork.md').write_text('New upstream description')
        self.save()
        self.assertEqual(self.backend.confirm_review(review['token']), ['alpha'])
        installed = self.backend.folder / 'alpha'
        self.assertEqual((installed / 'display-name').read_text(), 'alpha\n')
        self.assertEqual(json.loads((installed / SOURCE).read_text())['commit'], review['commit'])
        with self.assertRaisesRegex(ValueError, 'expired'):
            self.backend.confirm_review(review['token'])

    def test_git_address_choices_list_rows_and_review_several_themes(self):
        choices = self.backend.prepare_review(self.url)
        self.assertEqual({row['id'] for row in choices['choices']}, {'alpha', 'beta', 'gamma'})
        self.assertTrue(all('size' in row and 'folder' in row for row in choices['choices']))
        review = self.backend.prepare_review(self.url, theme_ids=['alpha', 'gamma'])
        self.assertEqual([spec['id'] for spec in review['specs']], ['alpha', 'gamma'])
        self.assertEqual(self.backend.confirm_review(review['token']), ['alpha', 'gamma'])
        self.assertTrue((self.backend.folder / 'alpha').is_dir())
        self.assertTrue((self.backend.folder / 'gamma').is_dir())
        self.assertFalse((self.backend.folder / 'beta').exists())

    def test_git_address_review_refuses_stage_tampering(self):
        review = self.backend.prepare_review(self.url, 'alpha')
        stage = Path(self.backend._reviews[review['token']]['stage'].name)
        (stage / 'alpha/display-name').write_text('Tampered')
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.backend.confirm_review(review['token'])
        self.assertFalse((self.backend.folder / 'alpha').exists())

    def test_manifest(self):
        folder = self.repo / 'themes/alpha'
        original = (folder / 'eitr-theme.json').read_text()
        for changes in ({'extra':True}, {'id':'../bad'}, {'light':1}, {'schemaVersion':True}, {'description':'x'*73}):
            with self.subTest(changes=changes):
                (folder / 'eitr-theme.json').write_text(json.dumps(json.loads(original) | changes))
                with self.assertRaises(ValueError):
                    manifest(folder)
        (folder / 'eitr-theme.json').write_text(original[:-1]+',"id":"alpha"}')
        with self.assertRaises(ValueError):
            manifest(folder)

    def test_data_refusals(self):
        folder = self.repo / 'themes/alpha'
        bad = folder / 'bad.png'
        bad.symlink_to(folder / 'preview.png')
        with self.assertRaises(ValueError):
            validate(folder)
        bad.unlink()
        bad.write_text('x')
        bad.chmod(0o755)
        with self.assertRaises(ValueError):
            validate(folder)
        bad.unlink()
        for filename in ('bad.sh', 'neovim.lua', 'vscode.vsix', 'own-theme.json', 'icons.theme', 'vscode.json', 'btop.theme', 'dolphin.theme'):
            bad = folder / filename
            bad.write_text('x')
            with self.assertRaises(ValueError):
                validate(folder)
            bad.unlink()
        with patch('eitr_theme_packages.MAX_BYTES', 1):
            with self.assertRaises(ValueError):
                validate(folder)
        with patch('eitr_theme_packages.MAX_FILES', 1):
            with self.assertRaises(ValueError):
                validate(folder)
        (folder / 'vscode.json').write_text('{"name":"bad","extension":"publisher.code"}')
        with self.assertRaises(ValueError):
            validate(folder)

    def test_every_shipped_theme_is_a_valid_package(self):
        import shutil
        generated = {'icons.theme', 'vscode.json', 'neovim.lua', 'btop.theme', 'dolphin.theme', 'vscode.vsix'}
        for source in sorted(folder for folder in (ROOT / 'themes').iterdir() if (folder / 'eitr-theme.json').is_file()):
            with self.subTest(theme=source.name):
                package = self.root / 'packages' / source.name
                shutil.copytree(source, package, ignore=lambda folder, names: [name for name in names
                    if name in generated or (Path(folder) == source and name == 'references')])
                self.assertEqual(validate(package)[0]['id'], source.name)

    def test_palette_accepts_hyprland_borders_only_in_their_keys(self):
        palette = self.repo / 'themes/alpha/colors.toml'
        original = palette.read_text()
        palette.write_text(original + 'hyprland_active_border = "rgba(798186ee) rgba(caccccee) 45deg"\n'
                           'hyprland_inactive_border = "rgb(1e1e1e)"\n')
        validate(self.repo / 'themes/alpha')
        for line in ('hyprland_active_border = "rgba(798186ee); exec"', 'accent2 = "rgb(1e1e1e)"'):
            with self.subTest(line=line):
                palette.write_text(original + line + '\n')
                with self.assertRaises(ValueError):
                    validate(self.repo / 'themes/alpha')

    def test_index_generator(self):
        command = [sys.executable, str(ROOT / 'tools/theme-catalog-index.py'), str(self.repo)]
        subprocess.run(command, check=True)
        subprocess.run([*command, '--check'], check=True)
        from eitr_theme_packages import validate_index
        rows = json.loads((self.repo / 'eitr-catalog.json').read_text())
        self.assertEqual(validate_index([{key: value for key, value in row.items() if key != 'wallpapers'} for row in rows])[0]['id'], 'alpha')
        thumbnail = self.repo / rows[0]['wallpapers'][0]['thumbnail']
        original = thumbnail.read_bytes()
        for damage in ('missing', 'stale', 'extra', 'changed-source'):
            with self.subTest(damage=damage):
                if damage == 'missing': thumbnail.unlink()
                if damage == 'stale': thumbnail.write_bytes(b'bad')
                if damage == 'extra': (thumbnail.parent / 'extra.jpg').write_bytes(original)
                if damage == 'changed-source':
                    from PIL import Image
                    Image.new('RGB', (16, 16), 'purple').save(self.repo / rows[0]['wallpapers'][0]['path'])
                self.assertNotEqual(subprocess.run([*command, '--check'], capture_output=True).returncode, 0)
                subprocess.run(command, check=True)
                subprocess.run([*command, '--check'], check=True)
        (self.repo / 'eitr-catalog.json').write_text('[]')
        self.assertNotEqual(subprocess.run([*command, '--check'], capture_output=True).returncode, 0)

    def blobs(self):
        repository = next(path for path in self.backend.cache.iterdir() if path.is_dir())
        output = subprocess.check_output(['git','cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype)'],
            cwd=repository, text=True, stderr=subprocess.DEVNULL)
        return {line.split()[0] for line in output.splitlines() if line.endswith(' blob')}

    def test_sparse_multi_install_and_list(self):
        self.assertEqual(len(self.backend.index(self.url)['themes']), 3)
        alpha_blob = self.run_git('rev-parse','HEAD:themes/alpha/preview.png')
        gamma_blob = self.run_git('rev-parse','HEAD:themes/gamma/preview.png')
        self.assertNotIn(alpha_blob, self.blobs())
        self.backend.install(self.url, ['alpha', 'beta'])
        self.assertIn(alpha_blob, self.blobs())
        self.assertNotIn(gamma_blob, self.blobs())
        self.assertEqual(set(theme_paths()), {'alpha', 'beta'})
        self.assertEqual([row['kind'] for row in self.backend.installed()], ['third-party']*2)
        with self.assertRaises(ValueError):
            self.backend.install(self.url, ['alpha'])
        picker = subprocess.check_output([sys.executable, str(ROOT / 'quickshell/desktop-bar/scripts/appearance-items.py'), 'theme'],text=True)
        self.assertIn('alpha', picker)

    def test_atomic_failure_and_clashes(self):
        (self.repo / 'themes/beta/bad.sh').write_text('bad')
        self.run_git('add','.')
        self.run_git('commit','-qm','Bad package')
        with self.assertRaises(ValueError):
            self.backend.install(self.url, ['alpha','beta'])
        self.assertFalse((self.backend.folder / 'alpha').exists())
        for parent in (self.root / 'builtin/themes', self.home / '.config/themes', self.backend.folder):
            (parent / 'alpha').mkdir(parents=True)
            with self.assertRaises(ValueError):
                self.backend.install(self.url,['alpha'])
            (parent / 'alpha').rmdir()

    def test_folder_updates_and_current_removal(self):
        self.backend.install(self.url, ['alpha','beta'])
        (self.repo / 'themes/beta/backgrounds/extra.png').write_bytes((self.repo / 'themes/beta/preview.png').read_bytes())
        self.save()
        self.assertEqual(self.backend.check(), {'alpha':0,'beta':1})
        self.backend.update('beta')
        self.assertEqual(self.backend.check(), {'alpha':0,'beta':0})
        marker = self.home / '.cache/current-theme'
        marker.write_text('beta')
        with self.assertRaisesRegex(ValueError,'current theme'):
            self.backend.remove('beta')
        marker.write_text('eitr')
        self.backend.remove('beta')
        self.assertFalse((self.backend.folder / 'beta').exists())

    def test_picker_lookup_and_palette_regeneration(self):
        self.backend.install(self.url, ['alpha'])
        environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'))
        resolved = subprocess.check_output(['bash', '-c', 'source "$EITR_LIBRARY_ROOT/paths.sh"; eitr_theme_dir alpha'],
                                           env=environment, text=True).strip()
        self.assertEqual(resolved, str(self.backend.folder / 'alpha'))
        palette = subprocess.check_output([sys.executable, str(ROOT / 'walker/scripts/themes/palette.py'),
            '--dir', resolved, 'get', 'accent'], env=environment, text=True).strip()
        self.assertEqual(palette, '#b9d77e')
        # Both native pickers consume this shared lookup; copied current palettes
        # are regenerated by package-owned code, without importing theme code.
        current = self.home / '.config/theme/current'
        import shutil
        shutil.copytree(resolved, current)
        generated = subprocess.check_output([sys.executable, str(ROOT / 'walker/scripts/themes/palette.py'),
            'fzf-colors'], env=environment, text=True)
        self.assertIn('#e2eae2', generated)

    def test_classification_and_foreign_repository(self):
        self.backend.install(self.url, ['alpha'])
        builtin = self.root / 'builtin/themes/builtin'
        builtin.mkdir(parents=True)
        (builtin / 'colors.toml').write_text('accent = "#ffffff"')
        (builtin / 'display-name').write_text('Built in')
        own = self.backend.folder / 'mine'
        own.mkdir()
        (own / 'colors.toml').write_text('accent = "#ffffff"')
        (own / 'display-name').write_text('Mine')
        (own / 'own-theme.json').write_text('{}')
        self.assertEqual({row['id']: row['kind'] for row in self.backend.installed()},
                         {'alpha':'third-party', 'builtin':'builtin', 'mine':'own'})
        current = self.home / '.cache/current-theme'
        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_text('alpha')
        rows = {row['id']: row for row in self.backend.installed()}
        self.assertEqual(rows['alpha']['palette'], {key: tomllib.loads(
            (self.backend.folder / 'alpha/colors.toml').read_text())[key]
            for key in ('background', 'foreground', 'accent', *(f'color{number}' for number in range(16)))})
        self.assertTrue(rows['alpha']['current'])
        self.assertFalse(rows['builtin']['current'])
        self.assertEqual(rows['alpha']['previewUrl'], (self.backend.folder / 'alpha/preview.png').as_uri())
        self.assertEqual(rows['alpha']['description'], manifest(self.backend.folder / 'alpha')['description'])
        self.assertEqual(rows['mine']['description'], '')
        with patch('eitr_theme_packages.official', return_value=True):
            self.assertEqual(self.backend.installed()[0]['kind'], 'official')
        with self.assertRaises(ValueError):
            self.backend.install((self.root / 'other').as_uri(), ['alpha'])
        with self.assertRaises(ValueError):
            self.backend.remove('mine')

    def test_rollback_and_failed_update(self):
        self.backend.install(self.url, ['alpha', 'beta'])
        original = (self.backend.folder / 'alpha' / SOURCE).read_bytes()
        (self.repo / 'themes/alpha/backgrounds/new.png').write_bytes((self.repo / 'themes/alpha/preview.png').read_bytes())
        self.save()
        real_rename = Path.rename
        def fail_beta(path, destination):
            if path.name == 'beta' and path.parent.name.startswith('.install-'):
                raise OSError('Injected rename failure')
            return real_rename(path, destination)
        with patch.object(Path, 'rename', fail_beta):
            with self.assertRaises(OSError):
                self.backend.install(self.url, ['alpha', 'beta'], updating=True)
        self.assertEqual((self.backend.folder / 'alpha' / SOURCE).read_bytes(), original)
        self.assertTrue((self.backend.folder / 'beta').is_dir())
        self.assertFalse((self.backend.folder / 'alpha/backgrounds/new.png').exists())

    def test_index_duplicates_and_symlink_tree(self):
        from eitr_theme_packages import validate_index
        rows = catalog(self.repo)
        with self.assertRaises(ValueError):
            validate_index([rows[0], rows[0]])
        (self.repo / 'themes/alpha/backgrounds/link.png').symlink_to('../preview.png')
        self.run_git('add', '.')
        self.run_git('commit', '-qm', 'Symlink')
        with self.assertRaises(ValueError):
            self.backend.install(self.url, ['alpha'])
        self.assertFalse((self.backend.folder / 'alpha').exists())

    def test_trusted_integrations_and_shared_generator(self):
        import shutil
        import importlib.util
        folder = self.repo / 'themes/alpha'
        folder.rename(self.repo / 'themes/catppuccin')
        folder = self.repo / 'themes/catppuccin'
        metadata = json.loads((folder / 'eitr-theme.json').read_text())
        metadata['id'] = 'catppuccin'
        (folder / 'eitr-theme.json').write_text(json.dumps(metadata))
        self.save()
        self.backend.install(self.url, ['catppuccin'])
        installed = self.backend.folder / 'catppuccin'
        self.assertNotIn('catppuccin/nvim', (installed / 'neovim.lua').read_text())
        self.assertNotIn('extension', json.loads((installed / 'vscode.json').read_text()))
        shutil.rmtree(installed)
        with patch('eitr_theme_packages.official', return_value=True):
            self.backend.install(self.url, ['catppuccin'])
            self.backend.update('catppuccin')
        self.assertIn('catppuccin/nvim', (installed / 'neovim.lua').read_text())
        self.assertEqual(json.loads((installed / 'vscode.json').read_text())['extension'],
                         'catppuccin.catppuccin-vsc')
        spec = importlib.util.spec_from_file_location('theme_builder', ROOT / 'themes/build-theme-files.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        integrations = json.loads((ROOT / 'themes/integrations.json').read_text())
        for theme_id, integration in integrations.items():
            temporary = self.root / 'generated' / theme_id
            temporary.mkdir(parents=True)
            shutil.copy(ROOT / 'themes' / theme_id / 'colors.toml', temporary)
            if (ROOT / 'themes' / theme_id / 'light.mode').exists():
                (temporary / 'light.mode').touch()
            builder.write_theme_files(temporary, official=True, integrations_path=ROOT / 'themes/integrations.json')
            for name, contents in builder.files_for(theme_id, integration).items():
                self.assertEqual((temporary / name).read_text(), contents)
                self.assertEqual((ROOT / 'themes' / theme_id / name).read_text(), contents)

    def test_palette_optional_and_strict(self):
        from eitr_theme_packages import validate_index
        rows = catalog(self.repo)
        self.assertEqual(len(rows[0]['palette']), 19)
        legacy = [{key: value for key, value in row.items() if key != 'palette'} for row in rows]
        self.assertEqual(validate_index(legacy), legacy)
        old_palette = {key: rows[0]['palette'][key] for key in ('background', 'foreground', 'accent', *(f'color{number}' for number in range(1, 7)))}
        validate_index([dict(rows[0], palette=old_palette)])
        for palette in (None, [], {'accent': '#ffffff'}, dict(rows[0]['palette'], accent='red'), dict(rows[0]['palette'], extra='#ffffff')):
            with self.assertRaises(ValueError):
                validate_index([dict(rows[0], palette=palette)])

    def test_wallpaper_index_rejects_unscoped_or_malformed_assets(self):
        from eitr_theme_packages import validate_index
        row = catalog(self.repo)[0]
        wallpaper = dict(path='themes/alpha/backgrounds/wall.png', thumbnail='thumbnails/alpha/wall.jpg', size=80)
        validate_index([dict(row, wallpapers=[wallpaper])])
        for changes in ({'path': 'themes/beta/backgrounds/wall.png'}, {'path': 'themes/alpha/backgrounds-ultrawide/wall.png'},
                        {'thumbnail': '../wall.jpg'}, {'thumbnail': 'thumbnails/beta/wall.jpg'}, {'size': True}, {'size': 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_index([dict(row, wallpapers=[wallpaper | changes])])
        with self.assertRaises(ValueError):
            validate_index([dict(row, wallpapers=[wallpaper, wallpaper])])

    def test_builtin_themes_cannot_be_removed(self):
        import shutil
        builtin = self.root / 'builtin/themes'
        shutil.copytree(self.repo / 'themes/alpha', builtin / 'alpha')
        with self.assertRaisesRegex(ValueError, 'Built-in themes cannot be removed'):
            self.backend.remove('alpha')
        self.assertTrue((builtin / 'alpha').exists())
        self.assertIn('alpha', theme_paths())
        self.assertNotIn('hidden', next(row for row in self.backend.installed() if row['id'] == 'alpha'))

    def test_official(self):
        for url in ('https://github.com/eitr-org/eitr-themes.git','git@github.com:eitr-org/eitr-themes.git',
                    'ssh://git@github.com/eitr-org/eitr-themes'):
            self.assertTrue(official(url))
        for url in ('https://github.com.evil/eitr-org/eitr-themes','https://github.com/other/eitr-themes',
                    'https://github.com/eitr-org/eitr-themes-evil'):
            self.assertFalse(official(url))


if __name__ == '__main__':
    unittest.main()
