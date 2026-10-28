"""Exercise the root preview wrapper using fake Plymouth, mount and namespace commands."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'tools/plymouth-preview.sh'

FAKE = r'''#!/usr/bin/python3
import json, os, signal, sys, time
from pathlib import Path
name = Path(sys.argv[0]).name
arguments = sys.argv[1:]
with open(os.environ['PREVIEW_LOG'], 'a') as output:
    output.write(json.dumps([name, arguments]) + '\n')
if name == 'python3': sys.exit(1 if os.environ.get('FAIL_X11') else 0)
elif name == 'id': print('0')
elif name == 'readlink':
    if arguments[0].startswith('/proc/'):
        print('host' if '/1/' in arguments[0] or os.environ.get('SAME_NAMESPACE') else 'preview')
    else: os.execv('/usr/bin/readlink', ['/usr/bin/readlink', *arguments])
elif name == 'unshare':
    theme = Path(os.environ['PREVIEW_THEME'])
    metadata = (theme / 'eitr-preview.plymouth').read_text()
    assert 'Name=Eitr preview' in metadata
    assert 'ImageDir=/usr/share/plymouth/themes/eitr-preview' in metadata
    assert 'ScriptFile=/usr/share/plymouth/themes/eitr-preview/eitr-preview.script' in metadata
    assert not (theme / 'eitr.plymouth').exists()
    assert arguments[:3] == ['--mount', '--net', '--fork']
    os.execvp(arguments[3], arguments[3:])
elif name == 'mount':
    if '--bind' in arguments and arguments[-1].endswith('renderers'):
        assert [path.name for path in Path(arguments[-2]).iterdir()] == ['x11.so']
elif name == 'plymouthd':
    assert os.environ['GDK_BACKEND'] == 'x11'
    assert os.environ['PLY_CREATE_FAKE_MULTI_HEAD_SETUP'] == '1'
    assert 'WAYLAND_DISPLAY' not in os.environ and 'NOTIFY_SOCKET' not in os.environ
    if os.environ.get('FAIL_DAEMON'): sys.exit(1)
    Path(os.environ['PREVIEW_DAEMON']).write_text(str(os.getpid()))
    while True: time.sleep(1)
elif name == 'plymouth':
    if arguments[0] == '--ping':
        daemon = Path(os.environ['PREVIEW_DAEMON'])
        if not daemon.exists(): sys.exit(1)
        try: os.kill(int(daemon.read_text()), 0)
        except ProcessLookupError: sys.exit(1)
    if arguments[0] == 'show-splash' and os.environ.get('FAIL_SHOW'): sys.exit(7)
    if arguments[0] == 'ask-for-password':
        Path(os.environ['PREVIEW_READY']).touch()
        if os.environ.get('WAIT_PASSWORD'): time.sleep(30)
        print('DO_NOT_LEAK_DEMO_ANSWER')
elif name == 'sleep': pass
'''


class PlymouthPreviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='eitr-preview-test-')
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)
        tools = self.folder / 'tools'
        tools.mkdir()
        source = self.folder / 'distro/plymouth/eitr'
        source.mkdir(parents=True)
        (source / 'eitr.plymouth').write_text((ROOT / 'distro/plymouth/eitr/eitr.plymouth').read_text())
        (source / 'eitr.script').write_text('# fixture')
        (source / 'wordmark.png').write_bytes(b'fixture')
        self.theme = self.folder / 'themes/eitr-preview'
        self.theme.parent.mkdir()
        installed = self.theme.parent / 'eitr'
        installed.mkdir()
        (installed / 'untouched').write_text('installed theme')
        self.renderers = self.folder / 'renderers'
        self.renderers.mkdir()
        (self.renderers / 'x11.so').write_text('x11 fixture')
        (self.renderers / 'drm.so').write_text('never exposed')
        self.runtime = self.folder / 'runtime'
        self.runtime.mkdir()
        (self.runtime / 'untouched').write_text('host state')
        sockets = self.folder / 'sockets'
        sockets.mkdir()
        connection = socket.socket(socket.AF_UNIX)
        self.addCleanup(connection.close)
        connection.bind(str(sockets / 'X987'))
        self.script = tools / 'plymouth-preview.sh'
        text = SCRIPT.read_text().replace('/usr/share/plymouth/themes/eitr-preview', str(self.theme))
        text = text.replace('/usr/lib/plymouth/renderers', str(self.renderers)).replace('/run/plymouth', str(self.runtime))
        text = text.replace('/tmp/.X11-unix', str(sockets)).replace('/tmp/eitr-plymouth-preview.XXXXXX', str(self.folder / 'work.XXXXXX'))
        self.script.write_text(text)
        binaries = self.folder / 'bin'
        binaries.mkdir()
        for name in ('id', 'readlink', 'unshare', 'mount', 'plymouth', 'plymouthd', 'sleep', 'python3'):
            path = binaries / name
            path.write_text(FAKE)
            path.chmod(0o755)
        self.log = self.folder / 'commands.jsonl'
        self.environment = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH'],
                                DISPLAY=':987', XAUTHORITY='', SUDO_USER='',
                                PREVIEW_THEME=str(self.theme), PREVIEW_LOG=str(self.log), PREVIEW_READY=str(self.folder / 'ready'),
                                PREVIEW_DAEMON=str(self.folder / 'daemon.pid'))

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def assert_clean(self):
        self.assertFalse(self.theme.exists())
        self.assertEqual(list(self.folder.glob('work.*')), [])
        self.assertEqual((self.runtime / 'untouched').read_text(), 'host state')
        self.assertEqual((self.theme.parent / 'eitr/untouched').read_text(), 'installed theme')
        daemon = self.folder / 'daemon.pid'
        if daemon.exists():
            with self.assertRaises(ProcessLookupError): os.kill(int(daemon.read_text()), 0)

    def test_sequence_discards_password_and_cleans_up(self):
        result = subprocess.run(['bash', str(self.script)], env=self.environment, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('DO_NOT_LEAK_DEMO_ANSWER', result.stdout + result.stderr)
        commands = self.commands()
        clients = [arguments for name, arguments in commands if name == 'plymouth']
        self.assertIn(['show-splash'], clients)
        self.assertIn(['change-mode', '--shutdown'], clients)
        self.assertTrue(any(arguments[0] == 'ask-for-password' and '--command=/usr/bin/cat' in arguments for arguments in clients))
        self.assertEqual([arguments for name, arguments in commands if name == 'sleep' and arguments != ['0.1']], [['6'], ['6'], ['5']])
        daemon = next(arguments for name, arguments in commands if name == 'plymouthd')
        self.assertIn('--no-boot-log', daemon)
        self.assertIn('--tty=/dev/null', daemon)
        self.assertTrue(any('plymouth.splash=eitr-preview' in argument for argument in daemon))
        self.assert_clean()

    def test_failed_splash_cleans_up_and_preserves_installed_theme(self):
        result = subprocess.run(['bash', str(self.script)], env=dict(self.environment, FAIL_SHOW='1'), capture_output=True, text=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        self.assert_clean()

    def test_daemon_startup_failure_removes_the_preview(self):
        result = subprocess.run(['bash', str(self.script)], env=dict(self.environment, FAIL_DAEMON='1'), capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assert_clean()

    def test_missing_host_runtime_directory_is_removed_after_preview(self):
        (self.runtime / 'untouched').unlink()
        self.runtime.rmdir()
        result = subprocess.run(['bash', str(self.script)], env=self.environment, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.runtime.exists())
        self.assertFalse(self.theme.exists())
        self.assertEqual(list(self.folder.glob('work.*')), [])

    def test_x11_authentication_failure_does_not_install_a_preview(self):
        result = subprocess.run(['bash', str(self.script)], env=dict(self.environment, FAIL_X11='1'), capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assert_clean()
        self.assertFalse(any(name in ('plymouth', 'plymouthd', 'mount') for name, arguments in self.commands()))

    def test_preexisting_preview_is_never_overwritten(self):
        self.theme.mkdir()
        (self.theme / 'owner').write_text('keep')
        result = subprocess.run(['bash', str(self.script)], env=self.environment, capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.theme / 'owner').read_text(), 'keep')
        self.assertFalse(any(name == 'plymouth' for name, arguments in self.commands()))

    def test_player_refuses_host_namespaces_before_any_plymouth_command(self):
        result = subprocess.run(['bash', str(self.script), '--player', str(self.folder)],
                                env=dict(self.environment, SAME_NAMESPACE='1'), capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(name in ('plymouth', 'plymouthd', 'mount') for name, arguments in self.commands()))

    def test_ctrl_c_cleans_up_while_waiting_for_password(self):
        process = subprocess.Popen(['bash', str(self.script)], env=dict(self.environment, WAIT_PASSWORD='1'),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            deadline = time.monotonic() + 8
            while not (self.folder / 'ready').exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue((self.folder / 'ready').exists())
            os.killpg(process.pid, signal.SIGINT)
            stdout, stderr = process.communicate(timeout=10)
            self.assertNotIn('DO_NOT_LEAK_DEMO_ANSWER', stdout + stderr)
            self.assertEqual(process.returncode, 130, stdout + stderr)
            self.assert_clean()
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            process.communicate(timeout=10)


if __name__ == '__main__':
    unittest.main()
