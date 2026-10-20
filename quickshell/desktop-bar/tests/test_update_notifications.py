from pathlib import Path
import os
import subprocess
import tempfile
import unittest


BAR = Path(__file__).resolve().parents[1]


class UpdateNotificationTests(unittest.TestCase):
    def notify(self, count, size, choice):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name, body in (("notify-send", f'echo "$@" > "{folder}/notified"\necho {choice}'),
                               ("kitty", f'echo "$@" > "{folder}/updated"')):
                tool = folder / name
                tool.write_text("#!/bin/sh\n" + body + "\n")
                tool.chmod(0o755)
            subprocess.run(["bash", str(BAR / "scripts/updates-notify.sh"), count, size], check=True,
                           env={**os.environ, "PATH": f"{folder}:{os.environ['PATH']}"})
            read = lambda name: (folder / name).read_text() if (folder / name).exists() else None
            return read("notified"), read("updated")

    def test_update_button_runs_system_update(self):
        notified, updated = self.notify("3", "120 MB", "update")
        self.assertIn("3 updates available", notified)
        self.assertIn("120 MB to download.", notified)
        self.assertIn("update.sh system", updated)

    def test_notification_shows_the_eitr_logo(self):
        notified, _ = self.notify("2", "10 MB", "later")
        icon = next(argument.split("=", 1)[1] for argument in notified.split() if argument.startswith("--icon="))
        self.assertTrue(icon.endswith("/fastfetch/assets/eitr-logo.png"), icon)
        self.assertTrue((BAR.parents[1] / "fastfetch/assets/eitr-logo.png").is_file())

    def test_later_does_nothing_and_one_update_is_singular(self):
        notified, updated = self.notify("1", "", "later")
        self.assertIn("1 update available", notified)
        self.assertIsNone(updated)

    def test_bar_announces_only_new_updates(self):
        source = (BAR / "shell.qml").read_text()
        self.assertIn("if (updates.count <= announcedUpdates)", source)
        self.assertIn("shell.announceUpdates();", source)
        self.assertIn("interval: 6 * 60 * 60 * 1000; repeat: true", source)


if __name__ == "__main__":
    unittest.main()
