"""Exercise the shell spinner without a live desktop or package operations."""
import os
from pathlib import Path
import pty
import select
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / 'distro/lib/spinner.sh'


class SpinnerTests(unittest.TestCase):
    def run_helper(self, command, terminal=False, input_text="", **environment):
        script = f'source "{HELPER}"; eitr_gettext() {{ printf "%s" "$1"; }}; {command}'
        env = {**os.environ, 'TERM': 'xterm-256color', 'COLORTERM': '', **environment}
        if 'NO_COLOR' not in environment:
            env.pop('NO_COLOR', None)
        if not terminal:
            return subprocess.run(['bash', '-c', script], capture_output=True, text=True, env=env, input=input_text)
        master, slave = pty.openpty()
        try:
            process = subprocess.Popen(['bash', '-c', script], stdout=slave, stderr=slave,
                                       stdin=subprocess.PIPE, env=env)
            process.stdin.write(input_text.encode())
            process.stdin.close()
            os.close(slave)
            slave = None
            output = bytearray()
            while True:
                if select.select([master], [], [], 5)[0]:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output.extend(chunk)
                else:
                    self.fail('spinner did not finish or left a process holding the terminal')
            return subprocess.CompletedProcess([], process.wait(timeout=3), output.decode(), '')
        finally:
            os.close(master)
            if slave is not None:
                os.close(slave)

    def test_plain_and_status(self):
        result = self.run_helper('run_with_spinner Waiting bash -c "exit 7"', EITR_NO_SPINNER='1')
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stderr, 'Waiting\n')

    def test_settled_and_reaped(self):
        result = self.run_helper('run_with_spinner Waiting sleep 0.3; test -z "$(jobs -pr)"', terminal=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('✓ Waiting', result.stdout)
        self.assertIn('\x1b[?25h', result.stdout)

    def test_tty_opt_out(self):
        result = self.run_helper('run_with_spinner Waiting true', terminal=True, EITR_NO_SPINNER='1')
        self.assertEqual(result.stdout.strip(), 'Waiting')

    def test_non_tty_fallback(self):
        result = self.run_helper('run_with_spinner Waiting true')
        self.assertEqual(result.stderr, 'Waiting\n')

    def test_terminal_fallbacks(self):
        for environment in ({'NO_COLOR': ''}, {'TERM': 'dumb'}):
            with self.subTest(environment=environment):
                result = self.run_helper('run_with_spinner Waiting true', terminal=True, **environment)
                self.assertEqual(result.stdout.strip(), 'Waiting')

    def test_animated_failure_status(self):
        result = self.run_helper('run_with_spinner Waiting bash -c "exit 7"', terminal=True)
        self.assertEqual(result.returncode, 7)
        self.assertNotIn('✓', result.stdout)
        self.assertIn('\x1b[?25h', result.stdout)

    def test_stdin_untouched(self):
        result = self.run_helper('run_with_spinner Waiting sleep 0.2; read -r answer; test "$answer" = yes',
                                 terminal=True, input_text='yes\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('✓ Waiting', result.stdout)

    def test_interrupt_cleans_up(self):
        result = self.run_helper(
            'run_with_spinner Waiting bash -c \'kill -INT "$PPID"\'; status=$?; '
            'test -z "$(jobs -pr)" || exit 99; exit "$status"', terminal=True)
        self.assertEqual(result.returncode, 130)
        self.assertIn('\x1b[?25h', result.stdout)

    def test_available_accent(self):
        result = self.run_helper('run_with_spinner Waiting sleep 0.2', terminal=True,
                                 EITR_TERMINAL_ACCENT='#123456')
        self.assertIn('\x1b[38;2;18;52;86m', result.stdout)

    def test_rainbow_unicode_and_normal_settlement(self):
        import re
        result = self.run_helper('run_with_spinner "Atualização…" sleep 0.35', terminal=True,
                                 COLORTERM='truecolor', LC_ALL='C.UTF-8')
        self.assertEqual(result.returncode, 0)
        colors = re.findall(r'\x1b\[38;2;\d+;\d+;\d+m', result.stdout)
        self.assertGreater(len(set(colors)), 10)
        plain = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', result.stdout)
        self.assertIn('Atualização… · ', plain)
        self.assertIn('✓ Atualização…', plain)
        self.assertNotRegex(result.stdout, '[ᚠᚢᚦᚨᚱᚲᚷᚹ]')
        self.assertTrue(result.stdout.endswith('✓ Atualização…\r\n'))

    def test_color_capability(self):
        for mode in ('', '256color', '24bit'):
            with self.subTest(mode=mode):
                result = self.run_helper('run_with_spinner Waiting sleep 0.2', terminal=True,
                                         COLORTERM=mode)
                self.assertEqual('\x1b[38;2;' in result.stdout, mode == '24bit')
                self.assertNotRegex(result.stdout, '[ᚠᚢᚦᚨᚱᚲᚷᚹ]')
