import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'distro/lib'))
spec = importlib.util.spec_from_file_location('assistant_chat', ROOT / 'quickshell/desktop-bar/scripts/assistant-chat.py')
chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat)


class AssistantChatTests(unittest.TestCase):
    def test_every_turn_carries_the_summary_and_the_conversation(self):
        # Replies are stateless calls, so the summary goes with every turn.
        turns = [{'role': 'user', 'text': 'Hello'}]
        with patch.object(chat, 'system_summary', return_value={'kernel': 'example'}) as summary:
            self.assertIn('system_summary', chat.prompt(turns))
            turns += [{'role': 'assistant', 'text': 'Hi'}, {'role': 'user', 'text': 'Explain'}]
            continued = json.loads(chat.prompt(turns).split('\n', 1)[1])
            self.assertEqual(continued['system_summary'], {'kernel': 'example'})
            self.assertEqual(continued['turns'], turns)
            self.assertEqual(summary.call_count, 2)

    def test_summary_has_only_public_facts(self):
        with patch.dict(os.environ, EITR_CODE_ROOT=str(ROOT)):
            summary = chat.system_summary()
        self.assertEqual(set(summary), {'eitr', 'channel', 'kernel', 'cpu', 'gpu', 'ram_gib', 'theme'})
        for private in ('hostname', 'username', 'email', 'clipboard', 'windows', 'ssid', 'files'):
            self.assertNotIn(private, summary)

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
