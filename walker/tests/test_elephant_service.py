import configparser
import os
import subprocess
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ElephantServiceTests(unittest.TestCase):
    def test_restart_preserves_menu_children(self):
        unit = configparser.ConfigParser(interpolation=None)
        unit.read(ROOT / "systemd/user/elephant.service")
        self.assertEqual(unit["Service"]["KillMode"], "process")
        self.assertTrue(unit["Service"]["ExecStart"].endswith(" /usr/bin/elephant"))

    def test_the_search_index_is_ready_before_the_first_walker(self):
        unit = configparser.ConfigParser(interpolation=None)
        unit.read(ROOT / "systemd/user/elephant.service")
        # "-": a failed warm-up never fails the backend; Walker then prepares it itself.
        self.assertEqual(unit["Service"]["ExecStartPost"],
                         "-/usr/bin/python3 /usr/share/eitr/walker/scripts/menus/search-index.py warm")

    def test_startup_uses_single_service(self):
        config = (ROOT / "hypr/hyprland.lua").read_text()
        self.assertIn('hyprScriptsDir .. "/session-start.sh"', config)
        startup = (ROOT / 'hypr/scripts/session-start.sh').read_text()
        self.assertIn('systemctl --user start --no-block elephant.service', startup)
        self.assertNotIn('hl.exec_cmd("elephant")', config)

    def test_early_walker_waits_for_backend_and_propagates_start_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            systemctl = root / 'systemctl'
            systemctl.write_text('#!/bin/sh\n[ "$*" = "--user start elephant.service" ] || exit 9\n'
                                  '[ "${FAIL_BACKEND:-}" != yes ] || exit 7\n'
                                  'sleep 0.05\nprintf ready > "$HOME/ready"\n')
            systemctl.chmod(0o755)
            walker = root / 'real-walker'
            walker.write_text('#!/bin/sh\n[ -f "$HOME/ready" ] || exit 8\nprintf "%s\\n" "$*"\n')
            walker.chmod(0o755)
            wrapper = root / 'walker-wrapper'
            wrapper.write_text((ROOT / 'walker/bin/walker').read_text().replace('/usr/bin/walker', str(walker)))
            environment = dict(os.environ, HOME=directory, EITR_CODE_ROOT=directory,
                               PATH=directory + os.pathsep + os.environ['PATH'],
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
            result = subprocess.run(['bash', str(wrapper), '--provider', 'menus:apps'],
                                    env=environment, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--provider menus:apps', result.stdout)
            (root / 'ready').unlink()
            result = subprocess.run(['bash', str(wrapper), '--provider', 'menus:apps'],
                                    env=dict(environment, FAIL_BACKEND='yes'), capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 7)
            self.assertFalse((root / 'ready').exists())


if __name__ == "__main__":
    unittest.main()
