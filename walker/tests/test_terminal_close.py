"""Dismiss terminals without a live terminal or desktop."""
import io
import unittest
from unittest.mock import Mock, patch

from home_isolation import setUpModule, tearDownModule
import eitr_terminal


class TerminalCloseTests(unittest.TestCase):
    def test_non_terminal_returns_without_reading(self):
        with patch.object(eitr_terminal.sys, 'stdin', io.StringIO()), \
                patch.object(eitr_terminal, 'print') as output, \
                patch.object(eitr_terminal.os, 'read') as read:
            eitr_terminal.wait_for_escape()
        read.assert_not_called()
        output.assert_called_once_with('Press Esc to close.', flush=True)

    def wait(self, keys):
        stream = Mock()
        stream.isatty.return_value = True
        stream.fileno.return_value = 7
        with patch.object(eitr_terminal.sys, 'stdin', stream), \
                patch.object(eitr_terminal, 'print'), \
                patch.object(eitr_terminal.termios, 'tcgetattr', return_value=['saved']), \
                patch.object(eitr_terminal.termios, 'tcsetattr') as restore, \
                patch.object(eitr_terminal.tty, 'setraw') as raw, \
                patch.object(eitr_terminal.os, 'read', side_effect=keys) as read:
            try:
                eitr_terminal.wait_for_escape()
            finally:
                raw.assert_called_once_with(7)
                restore.assert_called_once_with(7, eitr_terminal.termios.TCSADRAIN, ['saved'])
        return read.call_count

    def test_enter_and_other_keys_do_not_close(self):
        self.assertEqual(self.wait([b'\r', b'\n', b'x', b'\x1b']), 4)

    def test_eof_returns(self):
        self.assertEqual(self.wait([b'']), 1)

    def test_read_failure_restores_terminal(self):
        with self.assertRaises(OSError):
            self.wait(OSError('read failed'))
