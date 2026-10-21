from menu_data import load as load_menu
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/actions/tools/reminders.py"
spec = importlib.util.spec_from_file_location("reminders", SCRIPT)
reminders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reminders)


class ReminderTimeTests(unittest.TestCase):
    now = datetime(2026, 10, 16, 14, 0, 0)

    def due(self, text):
        value = reminders.when(text, now=self.now)
        return None if value is None else datetime.fromtimestamp(value)

    def test_delays(self):
        self.assertEqual(self.due("10m"), datetime(2026, 10, 16, 14, 10))
        self.assertEqual(self.due("1h30m"), datetime(2026, 10, 16, 15, 30))
        self.assertEqual(self.due("45s"), datetime(2026, 10, 16, 14, 0, 45))
        self.assertEqual(self.due("25"), datetime(2026, 10, 16, 14, 25), "a bare number is minutes")
        self.assertEqual(self.due("2 H"), datetime(2026, 10, 16, 16, 0))

    def test_times_of_day_roll_over_to_tomorrow(self):
        self.assertEqual(self.due("18:30"), datetime(2026, 10, 16, 18, 30))
        self.assertEqual(self.due("9:05"), datetime(2026, 10, 17, 9, 5))

    def test_unreadable_times_are_refused(self):
        for text in ("soon", "25:00", "12:75", "0m", ""):
            self.assertIsNone(self.due(text), text)


class ReminderCommandTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.calls = self.folder / "calls"
        for name in ("systemd-run", "systemctl", "notify-send"):
            tool = self.folder / name
            tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{self.calls}"\nexit 1\n' if name == "systemctl" else
                            f'#!/bin/sh\necho "{name} $*" >> "{self.calls}"\n')
            tool.chmod(0o755)
        self.environment = {**os.environ, "PATH": f"{self.folder}:{os.environ['PATH']}",
                            "XDG_STATE_HOME": str(self.folder / "state"), "EITR_CODE_ROOT": str(ROOT)}
        self.state = self.folder / "state/eitr/reminders.json"

    def run_script(self, *args):
        return subprocess.run(["python3", str(SCRIPT), *args], env=self.environment, capture_output=True, text=True)

    def calls_made(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def test_a_new_reminder_is_saved_timed_and_confirmed(self):
        result = self.run_script("new", "10m", "Take", "the", "tea", "out")
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = json.loads(self.state.read_text())
        self.assertEqual(saved[0]["text"], "Take the tea out")
        self.assertAlmostEqual(saved[0]["due"], time.time() + 600, delta=5)
        calls = self.calls_made()
        self.assertIn(f"--unit=eitr-reminder-{saved[0]['id']}", calls)
        self.assertIn("--on-active=", calls)
        self.assertIn("Reminder set", calls)

    def test_a_bad_time_sets_nothing(self):
        self.assertEqual(self.run_script("new", "whenever", "x").returncode, 1)
        self.assertFalse(self.state.exists())
        self.assertIn("Reminder not set", self.calls_made())

    def test_firing_notifies_once_and_forgets_it(self):
        self.run_script("new", "5m", "Stretch")
        identifier = json.loads(self.state.read_text())[0]["id"]
        self.run_script("fire", identifier)
        self.run_script("fire", identifier)
        self.assertEqual(self.calls_made().count("--urgency=critical"), 1)
        self.assertEqual(json.loads(self.state.read_text()), [])

    def test_restore_shows_missed_reminders_and_reschedules_the_rest(self):
        self.state.parent.mkdir(parents=True)
        now = int(time.time())
        self.state.write_text(json.dumps([{"id": "1", "due": now - 60, "text": "Missed"},
                                          {"id": "2", "due": now + 3600, "text": "Later"}]))
        self.run_script("restore")
        calls = self.calls_made()
        self.assertIn("Reminder (while the computer was off) Missed", calls)
        self.assertIn("--unit=eitr-reminder-2", calls)
        self.assertEqual([item["text"] for item in json.loads(self.state.read_text())], ["Later"])

    def test_cancel_stops_the_timer_and_forgets_it(self):
        self.run_script("new", "1h", "Call")
        identifier = json.loads(self.state.read_text())[0]["id"]
        self.assertEqual(self.run_script("cancel", identifier).returncode, 0)
        self.assertIn(f"systemctl --user stop eitr-reminder-{identifier}.timer", self.calls_made())
        self.assertEqual(json.loads(self.state.read_text()), [])
        self.assertIn("No reminders.", self.run_script("list").stdout)

    def test_menus_and_command_offer_it(self):
        reminders = load_menu("reminders")
        self.assertEqual([entry["text"] for entry in reminders["entries"]], ["New Reminder", "Upcoming Reminders"])
        self.assertEqual(reminders["parent"], "tools")
        tools = json.loads((ROOT / "elephant/menu-rows/tools.json").read_text())
        self.assertEqual([row["text"] for row in tools], ["Capture", "Reminders", "Share", "Music Visualizer"])
        main = json.loads((ROOT / "elephant/menu-rows/main.json").read_text())
        tools_row = next(row for row in main if row["text"] == "Tools")
        self.assertEqual(tools_row["submenu"], "tools")
        self.assertIn('/walker/scripts/actions/tools/reminders.py", "restore"',
                      (ROOT / "quickshell/desktop-bar/shell.qml").read_text())
        self.assertIn('"tools/reminders.py"', (ROOT / "distro/bin/eitr").read_text())


if __name__ == "__main__":
    unittest.main()
