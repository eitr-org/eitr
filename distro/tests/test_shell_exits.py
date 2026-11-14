"""An unexpected end of the bar leaves a record; restarts and logouts do not."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distro/lib'))
import eitr_shell_exits as exits

INSTANCE = {'id': 'abc123', 'pid': 4242, 'launch_time': '2026-11-14T00:50:55', 'config_path': '/x/shell.qml'}


class ShellExitTests(unittest.TestCase):
    def watch(self, after_exit, session=True):
        listings = iter([[INSTANCE], after_exit])
        with patch.object(exits, 'instances', side_effect=lambda path: next(listings)), \
                patch.object(exits, 'wait_for_exit') as wait, patch.object(exits.time, 'sleep'), \
                patch.object(exits, 'session_running', return_value=session), \
                patch.object(exits, 'record', return_value=Path('/saved')) as record:
            result = exits.watch('desktop-bar', Path('/x/shell.qml'))
        wait.assert_called_once_with(4242)
        return result, record

    def test_unexpected_end_is_recorded(self):
        result, record = self.watch([])
        self.assertEqual(result, Path('/saved'))
        record.assert_called_once_with('desktop-bar', INSTANCE)

    def test_restart_and_logout_are_not_recorded(self):
        for after_exit, session in (([dict(INSTANCE, pid=5000)], True), ([], False)):
            with self.subTest(session=session):
                result, record = self.watch(after_exit, session)
                self.assertIsNone(result)
                record.assert_not_called()

    def test_record_keeps_the_log_tail_and_the_newest_files(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime, folder = Path(directory) / 'run', Path(directory) / 'exits'
            log = runtime / 'quickshell/by-id/abc123/log.log'
            log.parent.mkdir(parents=True)
            log.write_text('\n'.join(f'line {number}' for number in range(500)))
            folder.mkdir()
            for number in range(12):
                (folder / f'desktop-bar-2026-01-01T00-00-{number:02}.log').write_text('old')
            outputs = {'coredumpctl': '', 'journalctl': 'Out of memory: Killed process 4242 (quickshell)\nother'}
            with patch.dict(exits.os.environ, {'XDG_RUNTIME_DIR': str(runtime)}), \
                    patch.object(exits, 'run', side_effect=lambda command, timeout=5: outputs[command[0]]):
                target = exits.record('desktop-bar', INSTANCE, folder)
            text = target.read_text()
            self.assertIn('pid 4242', text)
            self.assertIn('Killed process 4242', text)
            self.assertNotIn('\nother', text)
            self.assertIn('line 499', text)
            self.assertNotIn('line 299\n', text)
            self.assertEqual(len(list(folder.glob('desktop-bar-*.log'))), exits.KEEP)
            self.assertTrue(target.exists())


if __name__ == '__main__':
    unittest.main()
