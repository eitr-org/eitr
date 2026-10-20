import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "distro/lib/run-hook.sh"


class UserHookTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.hooks = self.home / "config/eitr/hooks"
        self.hooks.mkdir(parents=True)
        self.log = self.home / "state/eitr/hooks.log"
        self.environment = {**os.environ, "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / "config"),
                            "XDG_STATE_HOME": str(self.home / "state")}

    def hook(self, event, body, executable=True):
        path = self.hooks / event
        path.write_text("#!/bin/sh\n" + body + "\n")
        if executable:
            path.chmod(0o755)
        return path

    def run_hook(self, *args):
        return subprocess.run(["bash", str(RUNNER), *args], env=self.environment, capture_output=True, text=True)

    def test_a_hook_gets_its_arguments_and_its_output_is_logged(self):
        self.hook("theme-set", f'echo "theme is $1" > "{self.home}/seen"; echo visible')
        self.assertEqual(self.run_hook("theme-set", "norse").returncode, 0)
        self.assertEqual((self.home / "seen").read_text(), "theme is norse\n")
        log = self.log.read_text()
        self.assertIn("theme-set: running with norse", log)
        self.assertIn("visible", log)

    def test_a_failing_hook_never_fails_the_caller(self):
        self.hook("post-update", "exit 3")
        self.assertEqual(self.run_hook("post-update", "system").returncode, 0)
        self.assertIn("post-update: exited with 3", self.log.read_text())

    def test_a_file_that_is_not_executable_is_skipped_with_a_hint(self):
        self.hook("battery-low", f'touch "{self.home}/ran"', executable=False)
        self.assertEqual(self.run_hook("battery-low", "15").returncode, 0)
        self.assertFalse((self.home / "ran").exists())
        self.assertIn("skipped, not executable (chmod +x", self.log.read_text())

    def test_no_hook_means_nothing_happens(self):
        self.assertEqual(self.run_hook("post-boot").returncode, 0)
        self.assertFalse(self.log.exists())

    def test_post_boot_runs_once_per_boot(self):
        self.hook("post-boot", f'echo ran >> "{self.home}/count"')
        self.run_hook("post-boot")
        self.run_hook("post-boot")
        self.assertEqual((self.home / "count").read_text(), "ran\n")

    def test_unknown_events_are_refused(self):
        self.assertEqual(self.run_hook("pre-everything").returncode, 2)

    def test_every_event_is_wired_to_its_moment(self):
        update = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        self.assertIn('bash "$runner" post-update "$update_kind"', update)
        self.assertIn('theme-set "$THEME_NAME"', (ROOT / "walker/scripts/actions/style/apply.sh").read_text())
        shell = (ROOT / "quickshell/desktop-bar/shell.qml").read_text()
        self.assertIn('runHook(["battery-low", String(shell.battery.percent)])', shell)
        self.assertIn('shell.runHook(["post-boot"])', shell)
        command = (ROOT / "distro/bin/eitr").read_text()
        for event in ("post-update", "theme-set", "battery-low", "post-boot"):
            self.assertIn(f'"{event}"', command)
            self.assertIn(event, RUNNER.read_text())


if __name__ == "__main__":
    unittest.main()
