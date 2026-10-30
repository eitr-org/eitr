"""Assistant context and startup checks; never execute a real assistant."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule
import eitr_assistant_context as context
import eitr_assistants as assistants


class ContextTests(unittest.TestCase):
    def test_retrieval_and_budget(self):
        for question, expected in [('how do I change the theme', 'appearance:'),
                                   ('docker ps permission denied', '## Docker')]:
            turns = [{'role': 'user', 'text': question}]
            result = context.excerpts(turns, locale='en')
            self.assertIn(expected, result)
            self.assertLessEqual(len(result.encode()), 7168)
            self.assertLessEqual(len(context.excerpts(turns, budget=80).encode()), 80)

    def test_locale_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'fr').mkdir()
            (root / 'one.md').write_text('# Theme\n## Theme\nEnglish theme')
            (root / 'two.md').write_text('# Docker\n## Docker\nEnglish docker')
            (root / 'fr/one.md').write_text('# Theme\n## Theme\nFrench theme')
            with patch.object(context, 'code', return_value=root):
                result = context.excerpts([{'role': 'user', 'text': 'theme docker'}], locale='fr')
                self.assertIn('French theme', result)
                self.assertIn('English docker', result)
                self.assertNotIn('English theme', result)

    def test_overview_translation_and_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'fr').mkdir()
            (root / 'getting-started.md').write_text(
                '<!-- eitr-overview -->English overview<!-- /eitr-overview -->')
            translated = root / 'fr/getting-started.md'
            translated.write_text('<!-- eitr-overview -->French overview<!-- /eitr-overview -->')
            with patch.object(context, 'code', return_value=root):
                self.assertEqual(context.overview(locale='fr'), 'French overview')
                translated.write_text('# Incomplete translation')
                self.assertEqual(context.overview(locale='fr'), 'English overview')
                translated.unlink()
                self.assertEqual(context.overview(locale='fr'), 'English overview')

    def test_chat_overview_always_present_and_budgeted(self):
        for locale in ('en', 'pt_BR', 'es', 'fr', 'de'):
            for question in ('what interesting things does Eitr have', 'can I play games already?',
                             'how does Eitr work?', 'what is the shortcut for a terminal'):
                turns = [{'role': 'user', 'text': question}]
                result = context.chat_excerpts(turns, locale=locale)
                self.assertTrue(result.startswith(context.overview(locale=locale)))
                self.assertEqual(result.count('<!-- eitr-overview -->'), 0)
                self.assertLessEqual(len(result.encode()), 7168)
                for budget in (0, 1, 80, 2500):
                    self.assertLessEqual(len(context.chat_excerpts(turns, locale=locale, budget=budget).encode()), budget)

    def test_primer_reads_shortcuts(self):
        with patch.object(context, 'code') as source:
            source.return_value.read_text.return_value = '  SUPER + A                 Example assistant'
            self.assertIn('SUPER + A: Example assistant', context.primer())
        self.assertIn('SUPER + F1: Toggle EITR handbook', context.primer())
        self.assertIn('SUPER + Print: Frozen selection', context.primer())
        self.assertIn('SUPER + D (hold): Dictate', context.primer())
        self.assertIn('Media Next: Next media', context.primer())
        self.assertLess(len(context.primer().encode()), 8000)

    def test_primer_menu_and_channel_references_match_sources(self):
        for menu, labels in (
                ('main', ['Apps', 'Install', 'Plugins', 'Settings', 'Development', 'Tools', 'Learn']),
                ('settings', ['Connectivity', 'Devices & Input', 'Style', 'System', 'Security', 'Dotfiles'])):
            rows = json.loads(context.code('elephant/menu-rows/' + menu + '.json').read_text())
            names = {row['text'] for row in rows}
            for label in labels:
                self.assertIn(label, names)
                self.assertIn(label, ' '.join(context.PRIMER.split()))
        maintenance = context.code(context.BOOK + '/maintenance.md').read_text()
        for channel in ('stable', 'testing'):
            self.assertIn('eitr channel ' + channel, maintenance)
            self.assertIn(channel, context.PRIMER.casefold())

    def test_only_latest_two_user_turns(self):
        turns = [{'role': 'user', 'text': 'docker'}, {'role': 'assistant', 'text': 'docker'},
                 {'role': 'user', 'text': 'zzzz'}, {'role': 'user', 'text': 'qqqq'}]
        self.assertEqual(context.excerpts(turns, locale='en'), '')

    def test_trust_preserves_bytes_permissions_backup_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'config.json'
            original = b'{ "existing": [1, 2], "trustedFolders": ["/other"] }\n'
            path.write_bytes(original)
            path.chmod(0o640)
            assistants.trust_json(path, ['trustedFolders'], '/home/example', array=True)
            first = path.read_bytes()
            self.assertIn(b'"existing": [1, 2]', first)
            self.assertEqual(json.loads(first)['trustedFolders'], ['/other', '/home/example'])
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            backup = path.with_name('config.json.eitr-backup')
            self.assertEqual(backup.read_bytes(), original)
            assistants.trust_json(path, ['trustedFolders'], '/home/example', array=True)
            self.assertEqual(path.read_bytes(), first)
            self.assertEqual(backup.read_bytes(), original)

    def test_default_claude_trust_changes_only_home_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            path = home / '.claude.json'
            original = '{ "projects": {"/other": {"hasTrustDialogAccepted": false}}, "theme": "dark" }'
            path.write_text(original)
            with patch.object(Path, 'home', return_value=home):
                assistants.interactive_context('claude', {})
                first = path.read_bytes()
                assistants.interactive_context('claude', {})
            self.assertEqual(path.read_bytes(), first)
            settings = json.loads(first)
            self.assertEqual(settings['projects']['/other'], {'hasTrustDialogAccepted': False})
            self.assertTrue(settings['projects'][str(home)]['hasTrustDialogAccepted'])
            self.assertIn('"theme": "dark"', first.decode())
            self.assertEqual(path.with_name('.claude.json.eitr-backup').read_text(), original)

    def test_unknown_json_and_symlink_are_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'config.json'
            for text in ('bad', '{"trustedFolders":false}', '{"trustedFolders":[],"trustedFolders":[]}'):
                path.write_text(text)
                assistants.trust_json(path, ['trustedFolders'], '/home/example', array=True)
                self.assertEqual(path.read_text(), text)
            link = Path(temporary) / 'link.json'
            link.symlink_to(path)
            assistants.trust_json(link, ['trustedFolders'], '/home/example', array=True)
            self.assertFalse(link.with_name('link.json.eitr-backup').exists())

    def test_headless_launch_does_not_change_directory_or_trust(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(Path, 'home', return_value=Path(temporary)), \
                patch('eitr_ai_accounts.environment', return_value={}), \
                patch.object(assistants, 'executable', return_value=Path('/stub/assistant')), \
                patch.object(assistants, 'interactive_context') as startup, \
                patch.object(assistants.os, 'chdir') as change, \
                patch.object(assistants.os, 'execve') as execute:
            assistants.launch('claude', ['--print', 'question'], interactive=False)
            startup.assert_not_called()
            change.assert_not_called()
            self.assertEqual(execute.call_args.args[1], ['/stub/assistant', '--print', 'question'])
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_launch_home_and_selected_account(self):
        for identifier in assistants.STARTUP_SUPPORT:
            with self.subTest(identifier=identifier), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary)
                account = home / 'selected'
                env = {'CLAUDE_CONFIG_DIR': str(account), 'COPILOT_HOME': str(account)}
                with patch.object(Path, 'home', return_value=home), \
                        patch('eitr_ai_accounts.environment', return_value=env), \
                        patch.object(assistants, 'executable', return_value=Path('/stub/assistant')), \
                        patch.object(assistants, 'assistant_access', return_value='full'), \
                        patch.object(assistants.os, 'chdir') as change, \
                        patch.object(assistants.os, 'execve') as execute:
                    assistants.launch(identifier, ['question'], trusted=True)
                    change.assert_called_once_with(home)
                    arguments = execute.call_args.args[1]
                    self.assertEqual(arguments[-1], 'question')
                    option = {'claude': '--append-system-prompt', 'codex': '-c',
                              'gemini': '--skip-trust', 'grok': '--rules', 'pi': '--append-system-prompt'}.get(identifier)
                    if option:
                        self.assertIn(option, arguments)
                    if identifier in ('claude', 'codex', 'grok', 'pi'):
                        self.assertIn('offline Eitr Handbook', ' '.join(arguments))
                    if identifier in ('claude', 'copilot'):
                        self.assertTrue(list(account.glob('*.json')))
                    self.assertFalse((home / '.claude.json').exists())
                    self.assertFalse((home / '.copilot').exists())
