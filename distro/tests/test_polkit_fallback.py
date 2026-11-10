"""The login fallback starts KDE's polkit agent only when the bar's agent is not registered."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'hypr/scripts/polkit-fallback.sh'
HYPRLAND = ROOT / 'hypr/hyprland.lua'
SESSION = ROOT / 'hypr/scripts/session-start.sh'


def fake_command(folder, name, body):
    path = folder / name
    path.write_text('#!/usr/bin/env bash\n' + body + '\n')
    path.chmod(0o755)


class PolkitFallbackTests(unittest.TestCase):
    def run_fallback(self, status_body):
        """Run the script with fake bar IPC, sleep and env; return (env calls, status queries)."""
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            log = folder / 'calls'
            fake_command(folder, 'eitr-shell', f'echo query >> "{log}"\n' + status_body)
            fake_command(folder, 'sleep', 'exit 0')
            fake_command(folder, 'env', f'echo "env $*" >> "{log}"')
            environment = dict(os.environ, PATH=f'{folder}:/usr/bin:/bin', QT_STYLE_OVERRIDE='kvantum')
            result = subprocess.run(['bash', str(SCRIPT)], env=environment, capture_output=True,
                                    text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = log.read_text().splitlines() if log.exists() else []
            return [call for call in calls if call.startswith('env ')], calls.count('query')

    def test_registered_bar_keeps_kde_agent_stopped(self):
        started, queries = self.run_fallback('[[ "$*" == "desktop-bar ipc call -- polkit status" ]] && echo registered')
        self.assertEqual(started, [])
        self.assertEqual(queries, 1)

    def test_unregistered_bar_starts_kde_agent_without_kvantum_style(self):
        started, queries = self.run_fallback('echo unregistered')
        self.assertEqual(started, ['env -u QT_STYLE_OVERRIDE /usr/lib/polkit-kde-authentication-agent-1'])
        self.assertEqual(queries, 30)

    def test_bar_without_ipc_answer_starts_kde_agent(self):
        started, _ = self.run_fallback('exit 1')
        self.assertEqual(started, ['env -u QT_STYLE_OVERRIDE /usr/lib/polkit-kde-authentication-agent-1'])

    def test_late_registration_within_the_wait_keeps_kde_agent_stopped(self):
        counter = '$(dirname "$0")/count'
        started, queries = self.run_fallback(
            f'count=$(( $(cat "{counter}" 2>/dev/null || echo 0) + 1 )); echo "$count" > "{counter}"\n'
            '(( count >= 5 )) && echo registered || echo unregistered')
        self.assertEqual(started, [])
        self.assertEqual(queries, 5)

    def test_session_starts_the_fallback_instead_of_the_kde_agent(self):
        startup = HYPRLAND.read_text().split('hl.on("hyprland.start", function()', 1)[1].split('end)', 1)[0]
        self.assertNotIn('polkit-kde-authentication-agent-1', startup)
        session = SESSION.read_text()
        ready = session.index('eitr-shell desktop-bar ipc call -- bar workspaces')
        self.assertLess(ready, session.index('polkit-fallback.sh" &'))


if __name__ == '__main__':
    unittest.main()
