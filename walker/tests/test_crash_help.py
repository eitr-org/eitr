import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('crash_help', ROOT / 'walker/scripts/actions/system/crash-help.py')
crashes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crashes)


def event(uid=None):
    return {'MESSAGE_ID': crashes.MESSAGE_ID, 'COREDUMP_UID': str(os.getuid() if uid is None else uid),
            'COREDUMP_EXE': '/usr/bin/example', 'COREDUMP_SIGNAL_NAME': 'SIGSEGV',
            'COREDUMP_PID': '123', 'COREDUMP_TIMESTAMP': '12345678', '_BOOT_ID': 'abcd',
            '__REALTIME_TIMESTAMP': str(int(time.time() * 1_000_000))}


class CrashHelpTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        cursor = patch.object(crashes, 'cursor_file', return_value=Path(directory.name) / 'cursor')
        cursor.start()
        self.addCleanup(cursor.stop)
        ended = patch.object(crashes, 'shutdown_file', return_value=Path(directory.name) / 'session-end')
        ended.start()
        self.addCleanup(ended.stop)
    def test_only_own_new_crashes_and_rate_limit_and_ignore(self):
        with patch.object(crashes, 'preferences', return_value={'enabled': True, 'ignored': []}):
            recent = {}
            self.assertFalse(crashes.eligible(event(os.getuid() + 1), recent, 1000))
            self.assertTrue(crashes.eligible(event(), recent, 1000))
            self.assertFalse(crashes.eligible(event(), recent, 1001))
            self.assertTrue(crashes.eligible(event(), recent, 1300))
        for settings in ({'enabled': False}, {'enabled': True, 'ignored': ['/usr/bin/example']}):
            with patch.object(crashes, 'preferences', return_value=settings):
                self.assertFalse(crashes.eligible(event(), {}, 1000))

    def test_summary_contains_only_program_signal_and_backtrace(self):
        info = 'Command Line: private arguments\nEnvironment: secret\nStack trace of thread 123:\n #0 0x123 crash (lib.so)\nStorage: /private/core\n'
        with patch.object(crashes.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=info)) as run:
            summary = crashes.crash_summary(event())
            self.assertIn('example', summary)
            self.assertIn('SIGSEGV', summary)
            self.assertIn('#0 0x123', summary)
            for private in ('secret', 'private', 'Storage', 'Command Line'):
                self.assertNotIn(private, summary)
            arguments = run.call_args.args[0]
            self.assertIn('info', arguments)
            self.assertNotIn('dump', arguments)
            self.assertIn('COREDUMP_UID=' + str(os.getuid()), arguments)
            self.assertIn('COREDUMP_TIMESTAMP=12345678', arguments)

    def test_ai_is_optional_and_nothing_is_sent_automatically(self):
        with patch.object(crashes, 'crash_summary', return_value='summary'), \
                patch.object(crashes, 'preferences', return_value={'enabled': True}), \
                patch.object(crashes, 'default_assistant', return_value=''), \
                patch.object(crashes.subprocess, 'run', return_value=SimpleNamespace(stdout='ignore')) as run, \
                patch.object(crashes.subprocess, 'Popen') as open_report, \
                patch.object(crashes, 'open_default') as ask:
            crashes.notify(event())
            self.assertFalse(any(argument.startswith('--action=ai=') for argument in run.call_args.args[0]))
            ask.assert_not_called()
            open_report.assert_not_called()

    def test_explicit_ai_action_and_report_attachment(self):
        for action in ('ai', 'report'):
            with patch.object(crashes, 'crash_summary', return_value='safe summary'), \
                    patch.object(crashes, 'preferences', return_value={'enabled': True}), \
                    patch.object(crashes, 'default_assistant', return_value='copilot'), \
                    patch.object(crashes.subprocess, 'run', return_value=SimpleNamespace(stdout=action)), \
                    patch.object(crashes.subprocess, 'Popen') as report, patch.object(crashes, 'open_default') as ask:
                crashes.notify(event())
                if action == 'ai':
                    self.assertEqual(ask.call_args.args[0][0], '-i')
                    self.assertIn('Do not change the system unless I agree.', ask.call_args.args[0][1])
                    report.assert_not_called()
                else:
                    self.assertEqual(report.call_args.args[0][-2:], ['--crash-summary', 'safe summary'])
                    ask.assert_not_called()

    def test_toggle_defaults_on_and_preserves_ignored_programs(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(Path, 'home', return_value=Path(directory)):
            self.assertTrue(crashes.preferences()['enabled'])
            crashes.toggle()
            self.assertFalse(crashes.preferences()['enabled'])
            crashes.toggle()
            self.assertTrue(crashes.preferences()['enabled'])

    def test_old_welcome_opt_out_and_program_mute_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(Path, 'home', return_value=Path(directory)):
            previous = Path(directory) / '.local/state/eitr/problem-reports.json'
            previous.parent.mkdir(parents=True)
            previous.write_text('{"offer": false}')
            self.assertFalse(crashes.preferences()['enabled'])
            with patch.object(crashes, 'crash_summary', return_value='summary'), \
                    patch.object(crashes.subprocess, 'run', return_value=SimpleNamespace(stdout='mute')):
                crashes.toggle()
                crashes.notify(event())
            self.assertEqual(crashes.preferences()['ignored'], ['/usr/bin/example'])
            crashes.toggle()
            crashes.toggle()
            self.assertEqual(crashes.preferences()['ignored'], ['/usr/bin/example'])

    def test_watcher_deduplicates_records_without_starting_real_processes(self):
        import io
        first = {**event(), '__CURSOR': 'first'}
        repeated = {**event(), '__CURSOR': 'repeated'}
        process = SimpleNamespace(stdout=io.StringIO('\n'.join(json.dumps(row) for row in [first, first, repeated])),
                                  returncode=0, terminate=lambda: None, wait=lambda: None)

        class ImmediateThread:
            def __init__(self, target, args, **kwargs):
                self.target, self.args = target, args

            def start(self):
                self.target(*self.args)

        with patch.object(crashes.subprocess, 'Popen', return_value=process), \
                patch.object(crashes, 'preferences', return_value={'enabled': True, 'ignored': []}), \
                patch.object(crashes, 'notify') as notify, patch.object(crashes.threading, 'Thread', ImmediateThread):
            crashes.watch()
            notify.assert_called_once_with(first)

    def test_a_crash_that_ended_the_session_is_offered_at_the_next_login(self):
        import io

        class ImmediateThread:
            def __init__(self, target, args, **kwargs):
                self.target, self.args = target, args

            def start(self):
                self.target(*self.args)

        self.assertEqual(crashes.journal_start(), ['--lines=0'])
        old = {**event(), '__CURSOR': 'old', '__REALTIME_TIMESTAMP': str(int((time.time() - 2 * 86400) * 1_000_000))}
        recent = {**event(), '__CURSOR': 'recent'}
        process = SimpleNamespace(stdout=io.StringIO('\n'.join(json.dumps(row) for row in [old, recent])),
                                  returncode=0, terminate=lambda: None, wait=lambda: None)
        with patch.object(crashes.subprocess, 'Popen', return_value=process) as popen, \
                patch.object(crashes, 'preferences', return_value={'enabled': True, 'ignored': []}), \
                patch.object(crashes, 'notify') as notify, patch.object(crashes.threading, 'Thread', ImmediateThread):
            crashes.watch()
        self.assertIn('--lines=0', popen.call_args.args[0])
        notify.assert_called_once_with(recent)
        self.assertEqual(crashes.journal_start(), ['--after-cursor=recent'])

    def test_crashes_after_a_deliberate_logout_are_not_offered(self):
        ended = time.time()
        before = {**event(), '__REALTIME_TIMESTAMP': str(int((ended - 1) * 1_000_000))}
        during = {**event(), '__REALTIME_TIMESTAMP': str(int((ended + 1) * 1_000_000))}
        later = {**event(), '__REALTIME_TIMESTAMP': str(int((ended + 2 * crashes.SHUTDOWN_SECONDS) * 1_000_000))}
        with patch.object(crashes, 'compositor_running', return_value=True):
            crashes.session_ending(ended)
        self.assertFalse(crashes.during_shutdown(before))
        self.assertTrue(crashes.during_shutdown(during))
        self.assertFalse(crashes.during_shutdown(later))

    def test_a_compositor_crash_does_not_hide_the_crashes_that_follow(self):
        with patch.object(crashes, 'compositor_running', return_value=False):
            crashes.session_ending(time.time())
        self.assertFalse(crashes.shutdown_file().exists())
        self.assertFalse(crashes.during_shutdown(event()))
