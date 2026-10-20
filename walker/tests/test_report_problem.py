import json
import contextlib
import io
import sys
import tempfile
from home_isolation import setUpModule, tearDownModule
import importlib.util
from pathlib import Path
import subprocess
import tomllib
import unittest
from unittest.mock import patch
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('report_problem', ROOT / 'walker/scripts/actions/system/report-problem.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportProblemTests(unittest.TestCase):
    def test_redaction_removes_identity_but_keeps_diagnostics(self):
        text = ('/home/alex/.config/hypr/local.lua failed for alex on alex-laptop\n'
                'alex@example.org 192.168.1.20 fe80::1c2b:3a4f:5d6e:7f80 aa:bb:cc:dd:ee:ff\n'
                'quickshell 0.2.1 hyprland 0.52.0 alexander')
        result = report.redact(text, user='alex', host='alex-laptop', home='/home/alex')
        for secret in ('/home/alex', 'alex-laptop', 'example.org', '192.168', 'fe80', 'aa:bb'):
            self.assertNotIn(secret, result)
        self.assertIn('~/.config/hypr/local.lua failed for <user> on <host>', result)
        self.assertIn('quickshell 0.2.1 hyprland 0.52.0', result)
        self.assertEqual(report.redact('Date: Wed Aug 5 05:36:31 2026 2001:db8:0:0:0:0:0:1', user='x', host='y', home='/z'),
                         'Date: Wed Aug 5 05:36:31 2026 <ip>')
        self.assertIn('alexander', result)

    def test_collection_never_uploads_and_tolerates_missing_tools(self):
        def run(arguments, **kwargs):
            self.assertNotIn(arguments[0], {'curl', 'wget', 'gh', 'scp', 'ssh'})
            raise FileNotFoundError(arguments[0])

        with patch.object(report.subprocess, 'run', side_effect=run):
            text = report.collect()
        self.assertIn('# EITR problem report', text)
        self.assertIn('(unavailable:', text)

    def test_email_and_issue_links_carry_a_short_summary(self):
        text = '# EITR problem report\nEITR version: 0.5.0\n' + 'filler line\n' * 300 + \
               '## Crashes (last 7 days)\nSIGSEGV /usr/bin/Hyprland\n## Next\nmore\n'
        email = report.email_link(text, Path('eitr-problem-report-1.txt'))
        self.assertTrue(email.startswith('mailto:reports@eitr.info?subject=Eitr%20problem%20report&body='))
        self.assertIn('eitr-problem-report-1.txt', unquote(email))
        self.assertIn('/usr/bin/Hyprland', unquote(email), 'the crash list survives shortening')
        issue = report.issue_link(text)
        self.assertTrue(issue.startswith('https://github.com/eitr-org/eitr/issues/new?'))
        for link in (email, issue):
            self.assertLess(len(link), 6000, 'long links are cut by mail apps and GitHub')

    def test_sending_opens_only_what_the_user_picks(self):
        opened = []
        answers = iter(['1', '2', '4', '9', ''])
        with patch('builtins.input', side_effect=lambda prompt='': next(answers)), \
                patch.object(report, 'open_link', side_effect=lambda link: opened.append(link) or True), \
                patch('builtins.print'):
            report.send('# EITR problem report\n', Path('/tmp/report.txt'))
        self.assertEqual(len(opened), 3)
        self.assertTrue(opened[0].startswith('mailto:reports@eitr.info'))
        self.assertTrue(opened[1].startswith('https://github.com/'))
        self.assertEqual(opened[2], 'file:///tmp/report.txt', "4 opens the saved report to read it")
        self.assertNotIn("print(report)", Path(report.__file__).read_text(), "the terminal is not flooded with it")

    def test_collection_includes_crashes_and_the_previous_boot(self):
        source = (ROOT / 'walker/scripts/actions/system/report-problem.py').read_text()
        for section in ('Crashes (last 7 days)', 'Latest crash', 'Latest Hyprland crash report',
                        'Errors (user journal, previous boot)', 'Installation', 'Recent package changes'):
            self.assertIn(section, source)

    def test_menu_entry_lives_under_information_in_order(self):
        menu = {"entries": json.loads((ROOT / 'elephant/menu-rows/system-information.json').read_text())}
        names = [entry['text'] for entry in menu['entries']]
        self.assertIn('Report a Problem', names)
        self.assertEqual(names, sorted(names, key=str.casefold))
        entry = next(entry for entry in menu['entries'] if entry['text'] == 'Report a Problem')
        self.assertIn('kitty --hold', entry['actions']['open'])
        self.assertIn('report-problem.py', entry['actions']['open'])


    def test_crash_summary_is_attached_to_the_private_report_before_review(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(Path, 'home', return_value=Path(directory)), \
                patch.object(report, 'collect', return_value='diagnostics'), \
                patch.object(sys, 'argv', ['report-problem.py', '--crash-summary', 'Program: example\nSignal: SIGSEGV']), \
                patch.object(sys.stdin, 'isatty', return_value=False), contextlib.redirect_stdout(io.StringIO()):
            report.main()
            saved = next((Path(directory) / 'Documents').glob('eitr-problem-report-*.txt'))
            self.assertIn('Program: example\nSignal: SIGSEGV', saved.read_text())
            self.assertIn('diagnostics', saved.read_text())
            self.assertEqual(saved.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
