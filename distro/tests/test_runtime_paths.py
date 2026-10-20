import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('runtime_paths', ROOT / 'distro/lib/eitr_paths.py')
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)


class RuntimePathTests(unittest.TestCase):
    def test_xdg_ignores_relative_values(self):
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': 'relative'}):
            self.assertEqual(paths.config(), Path.home() / '.config')
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': '/tmp/eitr-path-test'}):
            self.assertEqual(paths.config('eitr/style.json'), Path('/tmp/eitr-path-test/eitr/style.json'))

    def test_rejects_unsafe_code_paths(self):
        for path in ('/etc/passwd', '../escape', 'a/../../b', ''):
            with self.assertRaises(ValueError):
                paths.code(path)

    def test_shell_override_is_deliberate_not_legacy(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CONFIG_HOME': directory}), patch.object(os, 'geteuid', return_value=1000):
            config = Path(directory)
            legacy = config / 'quickshell/desktop-bar'
            legacy.mkdir(parents=True)
            (legacy / 'shell.qml').write_text('legacy')
            self.assertEqual(paths.shell_path('desktop-bar'), paths.ROOT / 'quickshell/desktop-bar')
            override = config / 'eitr/overrides/quickshell/desktop-bar'
            override.mkdir(parents=True)
            (override / 'shell.qml').write_text('override')
            self.assertEqual(paths.shell_path('desktop-bar'), override)

    def test_settings_preserve_unknown_fields_and_reject_future_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            path.write_text('{"family":"mine","future_option":true}')
            paths.write_settings(path, {'size': 24})
            self.assertEqual(json.loads(path.read_text()), {'version': 1, 'family': 'mine', 'future_option': True, 'size': 24})
            path.write_text('{"version":2,"family":"future"}')
            with self.assertRaises(ValueError):
                paths.write_settings(path, {'size': 20})
            self.assertEqual(json.loads(path.read_text())['version'], 2)

    def test_kitty_loader_includes_user_files_relative_to_itself(self):
        # kitty does not expand ${KITTY_CONFIG_DIRECTORY} while reading config;
        # relative includes resolve beside the including user file.
        loader = (Path(__file__).resolve().parents[1] / 'defaults/kitty/kitty.conf').read_text()
        self.assertIn('include /usr/share/eitr/kitty/kitty.conf', loader)
        for name in ('theme.conf', 'fonts.conf', 'local.conf'):
            self.assertIn(f'globinclude {name}\n', loader)
        self.assertNotIn('${', loader)
        shipped = (Path(__file__).resolve().parents[2] / 'kitty/kitty.conf').read_text()
        self.assertNotRegex(shipped, r'(?m)^(?:glob)?include\s+[^/]')
