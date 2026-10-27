import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'distro/lib'))
sys.path.insert(0, str(ROOT / 'walker/tests'))
from home_isolation import setUpModule, tearDownModule
spec = importlib.util.spec_from_file_location('assistant_chat', ROOT / 'quickshell/desktop-bar/scripts/assistant-chat.py')
chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat)


class AssistantChatTests(unittest.TestCase):
    def test_every_turn_carries_the_summary_and_the_conversation(self):
        # Replies are stateless calls, so the summary goes with every turn.
        turns = [{'role': 'user', 'text': 'Hello'}]
        with patch.object(chat, 'system_summary', return_value={'kernel': 'example'}) as summary:
            self.assertIn('system_summary', chat.prompt(turns))
            self.assertIn('Norse-themed Arch Linux', chat.prompt(turns))
            turns += [{'role': 'assistant', 'text': 'Hi'}, {'role': 'user', 'text': 'Explain'}]
            continued = json.loads(chat.prompt(turns).split('\n', 1)[1])
            self.assertEqual(continued['system_summary'], {'kernel': 'example'})
            self.assertEqual(continued['turns'], turns)
            self.assertEqual(summary.call_count, 3)
            self.assertIn('Norse-themed Arch Linux', continued['Eitr primer'])

    def test_summary_has_only_public_facts(self):
        with patch.dict(os.environ, EITR_CODE_ROOT=str(ROOT)), \
                patch.object(chat, 'installed_highlights', return_value=['Steam']), \
                patch.object(chat, 'connected_hdr', return_value=True):
            summary = chat.system_summary()
        self.assertEqual(set(summary), {'eitr', 'channel', 'kernel', 'cpu', 'gpu', 'ram_gib', 'theme', 'installed_highlights', 'hdr_monitor_connected'})
        for private in ('hostname', 'username', 'email', 'clipboard', 'windows', 'ssid', 'files'):
            self.assertNotIn(private, summary)

    def test_highlights_batch_and_managed_paths_without_executing_tools(self):
        def query(arguments, **kwargs):
            self.assertEqual(arguments[:3], ['pacman', '-Q', '--'])
            self.assertEqual(kwargs['timeout'], 3)
            self.assertNotIn('unrelated-package', arguments)
            present = {'steam', 'gamemode', 'opencode', 'eitr-sunshine'}
            missing = [package for package in arguments[3:] if package not in present]
            return subprocess.CompletedProcess(arguments, 1, 'steam 1.0\n',
                ''.join("error: package '" + package + "' was not found\n" for package in missing))
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(Path, 'home', return_value=Path(temporary)), \
                patch.object(subprocess, 'run', side_effect=query) as run:
            executable = Path(temporary) / '.local/bin/claude'
            executable.parent.mkdir(parents=True)
            executable.touch()
            result = chat.installed_highlights()
            self.assertEqual(set(result), {'Steam', 'GameMode', 'OpenCode', 'Sunshine', 'Claude Code'})
            self.assertEqual(run.call_count, 1)
        with patch.object(subprocess, 'run', side_effect=FileNotFoundError):
            self.assertIsNone(chat.installed_highlights())

    def test_highlights_all_packages_and_query_failures(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(Path, 'home', return_value=Path(temporary)), \
                patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            result = chat.installed_highlights()
            self.assertEqual(set(result), {'Steam', 'GameMode', 'MangoHud', 'gamescope',
                                          'Docker', 'Flatpak', 'OBS', 'LocalSend',
                                          'Moonlight', 'Sunshine', 'Tailscale', 'OpenCode'})
            self.assertEqual(run.call_count, 1)
        for failure in (subprocess.TimeoutExpired('pacman', 3),
                        subprocess.CompletedProcess(['pacman'], 1, '', 'database unavailable')):
            with self.subTest(failure=failure):
                options = {'side_effect': failure} if isinstance(failure, Exception) else {'return_value': failure}
                with patch.object(subprocess, 'run', **options):
                    self.assertIsNone(chat.installed_highlights())

    def test_hdr_reuses_display_detection(self):
        display = chat.load_reference('test_chat_display', 'quickshell/desktop-bar/scripts/display-settings.py')
        from test_display_settings import DisplaySettingsTests
        with tempfile.TemporaryDirectory() as temporary:
            connector = Path(temporary) / 'card0-DP-1'
            connector.mkdir()
            (connector / 'edid').write_bytes(DisplaySettingsTests.edid())
            with patch.object(display, 'DRM_ROOT', Path(temporary)), \
                    patch.object(chat, 'load_reference', return_value=display):
                for status, expected in (('disconnected', False), ('connected', True)):
                    (connector / 'status').write_text(status)
                    self.assertEqual(chat.connected_hdr(), expected)
                (connector / 'edid').write_bytes(b'invalid')
                self.assertFalse(chat.connected_hdr())

    def test_example_prompts_have_overview_shortcuts_and_bounded_context(self):
        for question in ('what is the shortcut for a terminal', 'what interesting things does Eitr have',
                         'can I play games already?', 'how does Eitr work?'):
            with patch.object(chat, 'system_summary', return_value={'installed_highlights': ['Steam']}):
                rendered = chat.prompt([{'role': 'user', 'text': question}])
            payload = json.loads(rendered.split('\n', 1)[1])
            self.assertIn('What Eitr includes', payload['Eitr Handbook excerpts'])
            self.assertIn('SUPER + Enter:', payload['Eitr primer'])
            self.assertIn('Answer shortcut questions from Learn shortcuts', rendered)
            self.assertLessEqual(len(payload['Eitr Handbook excerpts'].encode()), 7168)
            self.assertLess(len(rendered.encode()), 18000)

    def test_readonly_path_and_account_selection(self):
        selected = {'identifier': 'codex'}
        with patch.object(chat, 'selection', return_value=selected), patch.object(chat, 'prompt', return_value='question'), patch.object(chat, 'ask', return_value='answer') as ask:
            self.assertEqual(chat.reply({'identifier': 'codex', 'turns': []}), {'answer': 'answer'})
            ask.assert_called_once_with('codex', 'question', announce=False, process_started=chat.watch_process)
            with self.assertRaises(ValueError):
                chat.reply({'identifier': 'claude', 'turns': []})
        source = (ROOT / 'quickshell/desktop-bar/scripts/assistant-chat.py').read_text()
        self.assertNotIn('open_default(', source)
        self.assertNotIn('FULL_ACCESS_FLAGS', source)

    def test_policy_and_missing_selection(self):
        with patch.object(chat, 'require', side_effect=ValueError('policy')), self.assertRaisesRegex(ValueError, 'policy'):
            chat.selection()
        with patch.object(chat, 'require'), patch.object(chat, 'default_assistant', return_value=''):
            with self.assertRaisesRegex(ValueError, 'Choose a default'):
                chat.selection()

    def test_invalid_turns_and_clean_errors(self):
        for turns in (None, [], [{'role': 'system', 'text': 'bad'}], [{'role': 'user', 'text': ''}]):
            with self.assertRaises(ValueError):
                chat.prompt(turns)
        for failure, expected in ((ValueError('The assistant timed out.'), 'The assistant timed out.'),
                                  (OSError('/private/path'), 'The assistant could not complete the request.')):
            with patch.object(sys, 'argv', ['chat']), patch.object(sys, 'stdin', io.StringIO('{}\n')), patch.object(sys, 'stdout', new_callable=io.StringIO) as output, patch.object(chat, 'reply', side_effect=failure), patch.object(chat.signal, 'signal'):
                chat.main()
                self.assertEqual(json.loads(output.getvalue()), {'error': expected})

    def test_cancel_kills_assistant_process_group(self):
        from unittest.mock import Mock
        process = Mock(pid=12345)
        with patch.object(chat, 'active_process', process), patch.object(chat.os, 'killpg') as kill:
            with self.assertRaises(SystemExit):
                chat.cancel(None, None)
            kill.assert_called_once_with(12345, chat.signal.SIGKILL)
            process.wait.assert_called_once()
