"""Session menu commands and defensive list selection, without real assistants."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('ai_session_runner', ROOT / 'walker/scripts/actions/ai-assistant.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

EXPECTED = {
    'claude': {'new': [], 'new-named': ['-n', 'VALUE'], 'continue-last': ['--continue'],
               'resume-picker': ['-r'], 'resume-name': ['-r', 'VALUE']},
    'codex': {'new': [], 'continue-last': ['resume', '--last'], 'resume-picker': ['resume'],
              'resume-name': ['resume', 'VALUE']},
    'gemini': {'new': [], 'continue-last': ['--resume', 'latest'], 'resume-picker': ['--resume', 'VALUE'],
               'resume-number': None},
    'grok': {'new': [], 'continue-last': ['--continue'], 'resume-picker': ['--resume', 'VALUE'],
             'resume-id': ['--resume', 'VALUE']},
    'copilot': {'new': [], 'new-named': ['--name', 'VALUE'], 'continue-last': ['--continue'],
                'resume-picker': ['--resume'], 'resume-name': ['--resume', 'VALUE']},
    'agy': {'new': [], 'continue-last': ['--continue'], 'resume-id': ['--conversation', 'VALUE']},
    'opencode': {'new': [], 'new-named': ['--session', 'VALUE'], 'continue-last': ['--continue'],
                 'resume-picker': ['--session', 'VALUE'], 'resume-id': ['--session', 'VALUE']},
    'pi': {'new': []},
}


class SessionMenuTests(unittest.TestCase):
    def test_every_row_has_a_known_action_and_expected_order(self):
        for assistant, actions in EXPECTED.items():
            rows = json.loads((ROOT / f'elephant/menu-rows/ai-{assistant}.json').read_text())
            self.assertEqual(rows[0]['text'], 'Accounts')
            self.assertEqual(rows[1]['text'], 'New')
            titles = [row['text'] for row in rows[2:]]
            self.assertEqual(titles, sorted(titles, key=str.casefold))
            actual = set()
            for row in rows[1:]:
                self.assertTrue(row['subtext'])
                actual.add(row['actions']['open'].split()[-1])
            self.assertEqual(actual, {assistant + '-' + action for action in actions})

    def run_action(self, temporary, assistant, action, value):
        home = Path(temporary)
        code = home / 'code'
        for folder in ['walker/scripts/menus', 'walker/scripts/actions', 'walker/bin/menu-path', 'distro/lib']:
            (code / folder).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'walker/scripts/menus/ai-tools.sh', code / 'walker/scripts/menus/ai-tools.sh')
        scripts = {
            'walker/scripts/menus/choose-folder.sh': '#!/bin/bash\nprintf "%s\\n" "$HOME"\n',
            'walker/bin/walker-dmenu': '#!/bin/bash\nprintf "%s\\n" "$TEST_VALUE"\n',
            'distro/lib/i18n.sh': 'eitr_gettext() { printf "%s" "$1"; }\n',
            'walker/bin/menu-path/kitty': '#!/bin/bash\n[[ "$1" == --directory ]] || exit 9\ncd -- "$2" || exit 9\nshift 2\nexec "$@"\n',
            'walker/bin/zsh': '#!/bin/bash\ncommand=${2%; exec zsh}\nexec bash -c "$command"\n',
            'walker/scripts/actions/ai-assistant.py':
                'import os,sys,json\n'
                'if sys.argv[1] == "session-picker": print(os.environ["TEST_VALUE"])\n'
                'else:\n'
                ' with open(os.environ["HOME"]+"/command", "w") as output: json.dump(sys.argv[1:], output)\n',
        }
        for name, content in scripts.items():
            path = code / name
            path.write_text(content)
            path.chmod(0o755)
        result = subprocess.run(['bash', str(code / 'walker/scripts/menus/ai-tools.sh'), assistant + '-' + action],
                                env={**os.environ, 'HOME': str(home), 'EITR_CODE_ROOT': str(code),
                                     'EITR_LIBRARY_ROOT': str(code / 'distro/lib'), 'TEST_VALUE': value,
                                     'PATH': str(code / 'walker/bin') + ':/usr/bin:/bin'},
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = home / 'command'
        return json.loads(path.read_text()) if path.exists() else None

    def test_every_action_builds_expected_argv_without_evaluating_values(self):
        value = 'a name; $(touch NEVER) `touch NEVER` "quoted" -flag'
        for assistant, actions in EXPECTED.items():
            for action, arguments in actions.items():
                with self.subTest(assistant=assistant, action=action), tempfile.TemporaryDirectory() as temporary:
                    actual = self.run_action(temporary, assistant, action, value)
                    expected = (['resume-number', 'gemini'] if arguments is None else
                                ['run', assistant, *[value if argument == 'VALUE' else argument for argument in arguments]])
                    self.assertEqual(actual, expected)
                    self.assertFalse((Path(temporary) / 'NEVER').exists())

    def test_empty_name_or_picker_cancels(self):
        for assistant, actions in EXPECTED.items():
            for action, arguments in actions.items():
                if arguments and 'VALUE' in arguments:
                    with self.subTest(assistant=assistant, action=action), tempfile.TemporaryDirectory() as temporary:
                        self.assertIsNone(self.run_action(temporary, assistant, action, ''))


class SessionPickerTests(unittest.TestCase):
    def test_lists_use_account_aware_runner_with_expected_flags(self):
        commands = {'gemini': ['--list-sessions'], 'grok': ['sessions', 'list'],
                    'opencode': ['session', 'list', '--format', 'json']}
        for assistant, arguments in commands.items():
            with patch.object(RUNNER.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '[]')) as run:
                self.assertEqual(RUNNER.list_sessions(assistant), '[]')
                self.assertEqual(run.call_args.args[0][2:], ['run', assistant, *arguments])


    def test_gemini_numbered_title_and_date(self):
        self.assertEqual(RUNNER.session_rows('gemini',
                         'Available sessions for this project (1):\n  2. Fix $(anything) (yesterday) [abc-123]\n'),
                         [('2', '2. Fix $(anything) (yesterday) [abc-123]')])
        self.assertEqual(RUNNER.session_rows('gemini', '2. malicious\nnot a session'), [])

    def test_grok_table_with_summary_and_ansi(self):
        identifier = '12345678-1234-1234-1234-123456789abc'
        rows = RUNNER.session_rows('grok', f'SESSION ID CREATED UPDATED STATUS\n\x1b[32m{identifier}\x1b[0m  Oct 28 Oct 28 idle\n\t  A title\n')
        self.assertEqual(rows, [(identifier, identifier + ' Oct 28 Oct 28 idle — A title')])

    def test_opencode_json_skips_bad_records_and_flattens_labels(self):
        rows = RUNNER.session_rows('opencode', json.dumps([
            {'id': 'ses_123', 'title': 'Title\n$(no execution)', 'updated': 0},
            None, {'id': '--bad'}, {'id': 5}, {'id': 'bad\nvalue'}]))
        self.assertEqual(len(rows), 1)
        self.assertIn('Title $(no execution)', rows[0][1])
        with self.assertRaises(ValueError):
            RUNNER.session_rows('opencode', '{broken')

    def test_picker_accepts_only_exact_rows_and_handles_empty_and_failed_lists(self):
        for selection, status in [('1. 2. Title (today) [abc]', 0), ('custom', 1), ('', 1)]:
            with patch.object(RUNNER, 'list_sessions', return_value=' 2. Title (today) [abc]\n'), \
                 patch.object(RUNNER.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, selection)), \
                 patch('builtins.print'):
                self.assertEqual(RUNNER.session_picker('gemini'), status)
        for output in ['', 'unrecognized output']:
            with patch.object(RUNNER, 'list_sessions', return_value=output), patch.object(RUNNER.subprocess, 'run') as run:
                self.assertEqual(RUNNER.session_picker('gemini'), 1)
                self.assertEqual(run.call_args.args[0][0], 'notify-send')
        with patch.object(RUNNER, 'list_sessions', side_effect=ValueError), patch.object(RUNNER.subprocess, 'run'):
            self.assertEqual(RUNNER.session_picker('gemini'), 1)

    def test_gemini_terminal_number_validation_and_cancel(self):
        for number, expected in [('2', ['--resume', '2']), ('', None), ('3', None), ('2; touch BAD', None)]:
            with patch.object(RUNNER, 'list_sessions', return_value=' 2. Title (today) [abc]\n'), \
                 patch('eitr_terminal.read_line_or_escape', return_value=number), \
                 patch('eitr_terminal.wait_for_escape'), patch.object(RUNNER, 'launch', return_value=0) as launch, \
                 patch('builtins.print'):
                RUNNER.resume_number()
                if expected:
                    launch.assert_called_once_with('gemini', expected)
                else:
                    launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
