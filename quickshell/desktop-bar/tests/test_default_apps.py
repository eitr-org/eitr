import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('default_apps', SCRIPTS / 'default-apps.py')
apps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apps)


class DefaultAppsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'config').mkdir()
        self.environment = patch.dict(os.environ, XDG_DATA_HOME=str(self.root / 'data'),
                                      XDG_DATA_DIRS=str(self.root / 'system'), XDG_CONFIG_HOME=str(self.root / 'config'))
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def desktop(self, root, name, content):
        path = self.root / root / 'applications' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[Desktop Entry]\nType=Application\nName=Fixture\nExec=true %U\n' + content)

    def test_handler_filter_precedence_and_hidden_mask(self):
        self.desktop('system', 'nested/view.desktop', 'MimeType=image/png;image/jpeg;\n')
        self.desktop('system', 'hidden.desktop', 'MimeType=image/png;\n')
        self.desktop('data', 'hidden.desktop', 'Hidden=true\n')
        self.desktop('data', 'missing.desktop', 'TryExec=eitr-no-such-executable\nMimeType=image/png;\n')
        self.assertEqual(list(apps.applications()), ['nested-view.desktop'])
        with patch.object(apps, 'run') as run:
            apps.select('images', 'nested-view.desktop')
        self.assertEqual(run.call_args_list[0].args[0], ['xdg-mime', 'default', 'nested-view.desktop', 'image/png'])
        self.assertEqual(run.call_count, 2)

    def test_rejects_invalid_handlers_without_writes(self):
        self.desktop('data', 'editor.desktop', 'MimeType=text/plain;\n')
        with patch.object(apps, 'run') as run:
            for kind, identifier in [('browser', 'editor.desktop'), ('unknown', 'editor.desktop'), ('pdf', '../bad.desktop')]:
                with self.assertRaises(ValueError):
                    apps.select(kind, identifier)
            run.assert_not_called()

    def test_terminal_delegates_shared_preference(self):
        with patch.object(apps, 'run', side_effect=[json.dumps({'choices': [{'value': 'kitty', 'available': True}]}), '']) as run:
            apps.select('terminal', 'kitty')
        self.assertEqual(run.call_args.args[0], ['python3', str(apps.TERMINAL), 'set', 'terminal', 'kitty'])

    def test_real_xdg_mime_writes_only_temporary_home(self):
        self.desktop('data', 'editor.desktop', 'MimeType=text/plain;\n')
        with patch.dict(os.environ, XDG_CURRENT_DESKTOP=''):
            apps.select('editor', 'editor.desktop')
            self.assertEqual(subprocess.check_output(['xdg-mime', 'query', 'default', 'text/plain'], text=True).strip(), 'editor.desktop')
        self.assertIn('editor.desktop', (self.root / 'config/mimeapps.list').read_text())

    def test_summary_resolves_names_and_installed_choices_once(self):
        self.desktop('data', 'editor.desktop', 'MimeType=text/plain;\n')
        def read(arguments):
            if arguments[0] == 'xdg-mime':
                return 'editor.desktop' if arguments[-1] == 'text/plain' else ''
            return json.dumps({'current': 'kitty', 'choices': [{'value': 'kitty', 'label': 'Kitty', 'available': True}, {'value': 'ghostty', 'label': 'Ghostty', 'available': False}]})
        with patch.object(apps, 'run', side_effect=read) as run:
            result = apps.summary()['items']
        self.assertEqual(len(result), 9)
        editor = next(entry for entry in result if entry['kind'] == 'editor')
        self.assertEqual(editor['name'], 'Fixture')
        self.assertEqual(editor['choices'], [{'value': 'editor.desktop', 'label': 'Fixture'}])
        self.assertEqual(result[-1]['choices'], [{'value': 'kitty', 'label': 'Kitty', 'available': True}])
        self.assertEqual(run.call_count, 9)
