"""Static and mocked checks for the lockscreen designs and launcher."""
import ast
import configparser
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / 'themes'
MODULE = ROOT / 'imports/LockscreenComponents'
DESIGNS = sorted(path.parent for path in THEMES.rglob('Main.qml'))


def general(design):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read(design / 'theme.conf')
    return dict(parser['General']) if parser.has_section('General') else {}


class DesignTests(unittest.TestCase):
    def qml_sources(self):
        return [*(design / 'Main.qml' for design in DESIGNS), *MODULE.glob('*.qml')]

    def test_password_submit_is_not_gated_on_quickshell(self):
        # The Quickshell bridge has no hostName, so gating login on the
        # "isQuickshell" check made some designs impossible to unlock.
        for path in self.qml_sources():
            lines = path.read_text().splitlines()
            for number, line in enumerate(lines):
                if re.search(r'\b(sddm|login)\.login\(', line):
                    context = '\n'.join(lines[max(0, number - 3):number + 1])
                    self.assertNotIn('isQuickshell', context, f'{path}:{number + 1}')

    def test_every_design_reaches_login(self):
        controller = (MODULE / 'LoginController.qml').read_text()
        self.assertIn('sddm.login(', controller)
        for design in DESIGNS:
            source = (design / 'Main.qml').read_text()
            for name in re.findall(r'^(\w+Design) \{', source, re.MULTILINE):
                source += (MODULE / f'{name}.qml').read_text()
            self.assertRegex(source, r'\b(sddm\.login|login\.login)\(', design.name)

    def test_bridge_identifies_itself_to_login_controller(self):
        self.assertIn('readonly property bool quickshellLock: true', (ROOT / 'AuthAdapter.qml').read_text())
        self.assertIn('sddm.quickshellLock === true', (MODULE / 'LoginController.qml').read_text())

    def test_backgrounds_come_from_theme_config(self):
        for design in DESIGNS:
            source = (design / 'Main.qml').read_text()
            self.assertNotIn('import QtMultimedia', source, design.name)
            if 'config.background' in source:
                background = general(design).get('background')
                if design.name == 'theme-wallpaper':
                    # The login screen reads the copy desktop-login-select stores.
                    self.assertEqual(background, '/var/lib/eitr/login-wallpaper.jpg')
                    self.assertTrue(general(design).get('fallback', '').startswith('/usr/share/eitr/themes/'))
                    continue
                self.assertTrue(background, f'{design.name} needs background= in theme.conf')
                self.assertTrue((design / background).is_file(), f'{design.name}: {background}')

    def test_shared_module_files_are_registered(self):
        registered = {line.split()[-1] for line in (MODULE / 'qmldir').read_text().splitlines()[1:] if line.strip()}
        self.assertEqual(registered, {path.name for path in MODULE.glob('*.qml')})

    def test_login_designs_import_their_bundled_module_copy(self):
        spec = importlib.util.spec_from_file_location('install_login', ROOT / 'scripts/install-login.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            for design in DESIGNS:
                (destination / 'Main.qml').write_text((design / 'Main.qml').read_text())
                installer.use_bundled_module(destination)
                source = (destination / 'Main.qml').read_text()
                self.assertNotRegex(source, r'(?m)^import LockscreenComponents\b', design.name)
                if 'Design {' in source:
                    self.assertIn('import "LockscreenComponents"', source, design.name)

    def test_material_variants_share_one_design(self):
        light, dark = THEMES / 'material-you', THEMES / 'material-you-dark'
        self.assertEqual((light / 'Main.qml').read_text(), (dark / 'Main.qml').read_text())
        self.assertEqual(general(light).get('themeMode'), 'light')
        self.assertEqual(general(dark).get('themeMode'), 'dark')


class SettingsTests(unittest.TestCase):
    def run_settings(self, *args):
        return subprocess.run(['python3', str(ROOT / 'scripts/settings.py'), *args],
                              capture_output=True, text=True)

    def test_selection_falls_back_to_the_helper_the_sudo_rule_allows(self):
        spec = importlib.util.spec_from_file_location('lock_settings', ROOT / 'scripts/settings.py')
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        with tempfile.TemporaryDirectory() as directory:
            packaged, previous = Path(directory) / 'packaged', Path(directory) / 'previous'
            packaged.write_text('')
            previous.write_text('')
            calls = []

            def sudo(args, **kwargs):
                calls.append(args[2])
                failed = args[2] == str(packaged)
                return subprocess.CompletedProcess(args, 1 if failed else 0, '', 'a password is required' if failed else '')

            with patch.object(settings, 'LOGIN_HELPERS', (packaged, previous)), \
                    patch.object(settings, 'STATE', Path(directory) / 'selected'), \
                    patch.object(settings.subprocess, 'run', side_effect=sudo), \
                    patch.object(settings.sys, 'argv', ['settings.py', 'select', 'nothing']):
                settings.main()
            self.assertEqual(calls, [str(packaged), str(previous)])
            self.assertEqual((Path(directory) / 'selected').read_text(), 'nothing\n')

    def test_missing_design_argument_is_a_usage_error(self):
        result = self.run_settings('select')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Usage', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_listed_designs_have_main_qml(self):
        listed = [line.split('\t')[0] for line in self.run_settings('list').stdout.splitlines()]
        self.assertEqual(sorted(listed), sorted(str(d.relative_to(THEMES)) for d in DESIGNS))

    def test_display_names_match_shipped_designs(self):
        source = ast.parse((ROOT / 'scripts/settings.py').read_text())
        names = next(ast.literal_eval(node.value) for node in source.body
                     if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'NAMES' for target in node.targets))
        self.assertEqual(set(names), {str(design.relative_to(THEMES)) for design in DESIGNS})


class ThemeWallpaperTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('wallpaper_settings', ROOT / 'scripts/settings.py')
        self.settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.settings)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name)
        for name, value in (
            ('cache', lambda relative: self.home / 'cache' / relative),
            ('user_config', lambda relative: self.home / 'config' / relative),
            ('code', lambda relative: self.home / 'package' / relative),
            ('STATE', self.home / 'config/lockscreen/selected'),
        ):
            override = patch.object(self.settings, name, value)
            override.start()
            self.addCleanup(override.stop)
        self.cache = self.home / 'cache'
        self.cache.mkdir()

    def test_config_follows_wallpaper_changes_and_encodes_paths(self):
        for name in ('first wallpaper #1.png', 'second wallpaper.webp'):
            wallpaper = self.home / name
            wallpaper.touch()
            (self.cache / 'current-wallpaper').write_text(str(wallpaper) + '\n')
            self.assertEqual(self.settings.theme_wallpaper(), wallpaper)
            self.assertEqual(self.settings.design_config('theme-wallpaper')['background'], wallpaper.as_uri())

    def test_missing_wallpaper_uses_current_theme_then_packaged_fallback(self):
        (self.cache / 'current-wallpaper').write_text('/nonexistent/wallpaper.png\n')
        theme = self.home / 'config/theme/current/backgrounds/01.png'
        theme.parent.mkdir(parents=True)
        theme.touch()
        self.assertEqual(self.settings.theme_wallpaper(), theme)
        theme.unlink()
        fallback = self.home / 'package/themes/eitr/backgrounds/02-eitr-runestone.png'
        fallback.parent.mkdir(parents=True)
        fallback.touch()
        self.assertEqual(self.settings.theme_wallpaper(), fallback)
        fallback.unlink()
        self.assertEqual(self.settings.design_config('theme-wallpaper')['background'], '')

    def test_cached_image_link_is_supported(self):
        wallpaper = self.home / 'selected.png'
        wallpaper.touch()
        (self.cache / 'current-wallpaper-image').symlink_to(wallpaper)
        self.assertEqual(self.settings.theme_wallpaper(), wallpaper)

    def test_selecting_theme_wallpaper_gives_the_login_screen_a_copy(self):
        helper = self.home / 'login-helper'
        helper.touch()
        wallpaper = self.home / 'current.png'
        from PIL import Image
        Image.new('RGB', (64, 36), 'teal').save(wallpaper)
        (self.cache / 'current-wallpaper').write_text(str(wallpaper))
        calls = []

        def run(command, **kwargs):
            calls.append((command, kwargs.get('input')))
            return subprocess.CompletedProcess(command, 0, '', '')
        with patch.object(self.settings, 'LOGIN_HELPERS', (helper,)), \
                patch.object(self.settings.subprocess, 'run', side_effect=run), \
                patch.object(sys, 'argv', ['settings.py', 'select', 'theme-wallpaper']):
            self.settings.main()
        self.assertEqual([command for command, _ in calls],
                         [['sudo', '-n', str(helper), '--wallpaper'], ['sudo', '-n', str(helper), 'theme-wallpaper']])
        self.assertTrue(calls[0][1].startswith(b'\xff\xd8\xff'), 'a JPEG on stdin, never a path')
        self.assertEqual(self.settings.STATE.read_text(), 'theme-wallpaper\n')

    def test_wallpaper_changes_refresh_the_copy_only_for_theme_wallpaper(self):
        helper = self.home / 'login-helper'
        helper.touch()
        with patch.object(self.settings, 'LOGIN_HELPERS', (helper,)), \
                patch.object(self.settings, 'give_login_wallpaper') as give:
            self.settings.STATE.parent.mkdir(parents=True, exist_ok=True)
            self.settings.STATE.write_text('clockwork/tape\n')
            self.settings.refresh_login_wallpaper()
            give.assert_not_called()
            self.settings.STATE.write_text('theme-wallpaper\n')
            self.settings.refresh_login_wallpaper()
            give.assert_called_once_with(helper)

    def test_menu_preview_resolves_current_wallpaper(self):
        wallpaper = self.home / 'current.png'
        wallpaper.touch()
        (self.cache / 'current-wallpaper').write_text(str(wallpaper))
        with patch.object(sys, 'argv', ['settings.py', 'preview', 'theme-wallpaper']), \
                patch('builtins.print') as output:
            self.settings.main()
        output.assert_called_once_with(wallpaper)


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp)
        home = self.temp / 'home'
        (home / '.config/quickshell').mkdir(parents=True)
        (home / '.config/quickshell/lockscreen').symlink_to(ROOT)
        (home / '.config/lockscreen').mkdir()
        (home / '.config/lockscreen/selected').write_text('material-you\n')
        runtime = self.temp / 'runtime'
        runtime.mkdir()
        bin_dir = self.temp / 'bin'
        bin_dir.mkdir()
        self.log = self.temp / 'calls.log'
        real_python = shutil.which('python3')
        fakes = {
            'eitr-shell': 'echo "eitr-shell $*" >> "$CALLS"; exit "${FAKE_QUICKSHELL:-0}"',
            'eitr-hyprlock': 'echo hyprlock >> "$CALLS"',
            'flock': 'exit "${FAKE_FLOCK:-0}"',
            'pgrep': '[[ "$1" == -x ]] && exit "${FAKE_HYPRLOCK:-1}"; exit "${FAKE_OTHER_LOCK:-1}"',
            'quickshell': 'echo "quickshell $*" >> "$CALLS"; exit "${FAKE_QUICKSHELL:-0}"',
            'hyprlock': 'echo hyprlock >> "$CALLS"',
            'notify-send': 'exit 0',
            'python3': f'[[ -n "${{FAKE_PYTHON_FAIL:-}}" ]] && exit 1; exec "{real_python}" "$@"',
        }
        for name, body in fakes.items():
            path = bin_dir / name
            path.write_text('#!/usr/bin/env bash\n' + body + '\n')
            path.chmod(0o755)
        self.env = {'HOME': str(home), 'XDG_RUNTIME_DIR': str(runtime), 'CALLS': str(self.log),
                    'EITR_CODE_ROOT': str(ROOT.parents[1]),
                    'PATH': f'{bin_dir}:{os.environ["PATH"]}'}

    def launch(self, *args, **overrides):
        env = {**self.env, **overrides}
        result = subprocess.run(['bash', str(ROOT / 'scripts/launch.sh'), *args],
                                env=env, capture_output=True, text=True)
        calls = self.log.read_text().splitlines() if self.log.exists() else []
        return result, calls

    def test_normal_unlock_does_not_start_hyprlock(self):
        result, calls = self.launch('lock')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['eitr-shell lockscreen'])

    def test_quickshell_failure_falls_back_to_hyprlock(self):
        _, calls = self.launch('lock', FAKE_QUICKSHELL='1')
        self.assertEqual(calls, ['eitr-shell lockscreen', 'hyprlock'])

    def test_failure_with_another_lock_instance_does_not_double_lock(self):
        _, calls = self.launch('lock', FAKE_QUICKSHELL='1', FAKE_OTHER_LOCK='0')
        self.assertEqual(calls, ['eitr-shell lockscreen'])

    def test_settings_failure_still_locks(self):
        _, calls = self.launch('lock', FAKE_PYTHON_FAIL='1')
        self.assertEqual(calls, ['hyprlock'])

    def test_existing_lock_is_left_alone(self):
        _, calls = self.launch('lock', FAKE_FLOCK='1')
        self.assertEqual(calls, [])
        _, calls = self.launch('lock', FAKE_HYPRLOCK='0')
        self.assertEqual(calls, [])

    def test_active_reports_held_lock(self):
        self.assertEqual(self.launch('active')[0].returncode, 1)
        (Path(self.env['XDG_RUNTIME_DIR']) / 'desktop-lockscreen.lock').touch()
        self.assertEqual(self.launch('active', FAKE_FLOCK='1')[0].returncode, 0)
        self.assertEqual(self.launch('active')[0].returncode, 1)
        self.assertEqual(self.launch('active', FAKE_HYPRLOCK='0')[0].returncode, 0)


if __name__ == '__main__':
    unittest.main()
