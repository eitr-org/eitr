"""Settings projections use canonical data and never execute menu actions on reads."""
import re
import importlib.util
from pathlib import Path
import sys
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('settings_system', SCRIPTS / 'settings-system.py')
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class SettingsSystemTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        environment = patch.dict(os.environ, EITR_CODE_ROOT=str(SCRIPTS.parents[2]),
                                 XDG_CONFIG_HOME=temporary.name, LC_ALL='C.UTF-8')
        environment.start()
        self.addCleanup(environment.stop)

    def test_shortcuts_resolve_every_canonical_reference(self):
        reference = settings.shortcut_reference()
        result = settings.shortcuts()['items']
        self.assertEqual(len(result), sum('heading' not in entry for entry in reference))
        self.assertTrue(all(entry['group'] and entry['title'] and entry['detail'] for entry in result))
        terminal = next(entry for entry in result if entry['title'] == 'Open terminal')
        self.assertEqual(terminal['detail'], next(entry['key'] for entry in reference if entry.get('description') == 'Open terminal'))

    def test_security_preserves_all_walker_actions(self):
        import eitr_selfcheck
        import eitr_assistants
        helper = SimpleNamespace(authentication_summary=lambda: {'fingerprint': {'available': True, 'services': []}, 'fido2': {'available': True, 'services': ['sudo']}})
        with patch.object(settings, 'module', return_value=helper), \
                patch.object(eitr_assistants, 'assistant_access', return_value='ask'), \
                patch.object(eitr_selfcheck, 'check_security_firewall', return_value=('info', 'Firewall active', '', '')):
            result = settings.security()['items']
        self.assertEqual([entry['title'] for entry in result], [entry['text'] for entry in settings.rows('security')])
        self.assertEqual(next(entry for entry in result if entry['title'] == 'Firewall')['detail'], 'Firewall active')
        for entry in result:
            self.assertTrue(entry['menu'] or entry['actionMenu'])

    def test_diagnostics_are_explicit_and_reads_are_visibility_scoped(self):
        source = re.sub(r"\s+", " ", (SCRIPTS.parent / 'settings/SettingsSystemPage.qml').read_text())
        self.assertIn('command: ["eitr", "check", "--json"]', source)
        self.assertEqual(source.count('check.running = true'), 1)
        self.assertIn('onClicked: if (view.live && !check.running) check.running = true', source)
        self.assertIn('if (!active || !live) return;', source)
        self.assertIn('Component.onDestruction: DesktopData.releaseOwner(view)', source)
        self.assertIn('ProfilePicture {', source)
        self.assertIn('ChoiceLists.updateChannels', source)
        self.assertIn('menu-action.py', source)

    def test_authentication_reader_ignores_comments_and_never_writes(self):
        helper = settings.module('settings_security_test', 'walker/scripts/actions/system/security.py')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'sudo').write_text('auth sufficient pam_u2f.so # active\n# auth sufficient pam_fprintd.so\n')
            result = helper.authentication_summary(path)
            self.assertEqual(result['fido2']['services'], ['sudo'])
            self.assertEqual(result['fingerprint']['services'], [])
            self.assertTrue(result['fingerprint']['available'])

    def test_git_and_cloud_reads_only_existing_metadata_helpers(self):
        git = SimpleNamespace(load=lambda: {'accounts': {'fixture': {'label': 'Example', 'name': 'Explorer', 'email': 'explorer@example.invalid'}}, 'folders': [{'path': '/projects/example', 'account': 'fixture'}], 'default': 'fixture'})
        accounts = SimpleNamespace(aws_choices=lambda: ['Example\tfixture'])
        contexts = SimpleNamespace(contexts=lambda provider: [{'label': provider}], title=lambda context: context['label'])
        providers = SimpleNamespace(PROVIDERS={'example': {'name': 'Example provider'}}, accounts=lambda provider: ['fixture'], selection=lambda provider, name: {'context': 'fixture-context'})
        modules = {'settings_git': git, 'settings_contexts': contexts, 'settings_cloud_accounts': accounts, 'settings_providers': providers}
        with patch.object(settings, 'module', side_effect=lambda name, relative: modules[name]):
            result = settings.git_cloud()['items']
        self.assertIn('explorer@example.invalid', result[0]['detail'])
        self.assertIn('/projects/example', result[0]['detail'])
        self.assertEqual(result[-1]['detail'], 'fixture · fixture-context')
        self.assertEqual(len(result), 5)
