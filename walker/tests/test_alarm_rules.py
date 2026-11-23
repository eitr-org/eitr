"""Clock alarms use the existing reminder timer and persistence transaction."""
from datetime import datetime
from io import StringIO
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from test_reminders import reminders
from alarm_rules import configure, dismiss, moments, transition
from reminder_rules import advance


def stamp(day, hour=6, minute=0):
    return int(datetime(2026, 3, day, hour, minute, tzinfo=ZoneInfo("America/New_York")).timestamp())


class AlarmTests(unittest.TestCase):
    def setUp(self):
        zone = patch.dict("os.environ", {"TZ": "America/New_York"})
        zone.start()
        time.tzset()
        self.addCleanup(time.tzset)
        self.addCleanup(zone.stop)
        self.payload = {"clock": "07:30", "days": [], "name": "Walk",
                        "sound": "alarm-clock-elapsed", "enabled": True}

    def configure(self, now, **changes):
        return configure(dict(self.payload, **changes), "1", now, "Invalid alarm.")

    def test_once_snooze_and_missed(self):
        item = self.configure(stamp(7))
        due = stamp(7, 7, 30)
        self.assertEqual(moments(item), [due])
        self.assertEqual(transition(item, due, due, advance), "ring")
        self.assertFalse(item["alarm"]["enabled"])
        self.assertTrue(dismiss(item, True, due + 5))
        snoozed = due + 605
        self.assertEqual(moments(item), [snoozed])
        self.assertEqual(transition(item, snoozed, snoozed, advance), "ring")
        self.assertEqual(item["alarm"]["ringTime"], "07:30")
        self.assertEqual(transition(item, snoozed + 600, snoozed + 600, advance), "missed")
        self.assertEqual(moments(item), [])

    def test_weekly_days_and_dst_gap_keep_the_original_wall_time(self):
        item = self.configure(stamp(7), clock="02:30", days=[6])
        gap = stamp(8, 3, 30)
        self.assertEqual(item["due"], gap)
        self.assertEqual(transition(item, gap, gap, advance), "ring")
        self.assertTrue(item["alarm"]["enabled"])
        self.assertEqual(item["alerts"], [stamp(15, 2, 30)])

    def test_snooze_does_not_replace_the_next_repeat(self):
        item = self.configure(stamp(7), days=[5, 6])
        due = item["due"]
        transition(item, due, due, advance)
        dismiss(item, True, due + 10)
        self.assertEqual(moments(item), [due + 610, stamp(8, 7, 30)])

    def test_disabled_and_stale_fire(self):
        disabled = self.configure(stamp(7), enabled=False)
        self.assertEqual(moments(disabled), [])
        self.assertEqual(transition(disabled, disabled["due"], disabled["due"], advance), "")
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(reminders, "state_file", return_value=Path(directory) / "reminders.json"):
                reminders.save([disabled])
                self.assertEqual(reminders.fire(disabled["id"]), 0)
                self.assertEqual(reminders.load(), [disabled])

    def test_late_fire_is_missed_and_saved_with_no_sound(self):
        item = self.configure(stamp(7))
        due = item["due"]
        with tempfile.TemporaryDirectory() as directory:
            with (patch.object(reminders, "state_file", return_value=Path(directory) / "reminders.json"),
                  patch.object(reminders, "notify") as notify,
                  patch.object(reminders, "schedule_alert") as schedule,
                  patch("time.time", return_value=due + 600)):
                reminders.save([item])
                self.assertEqual(reminders.fire(item["id"], moment=due), 0)
                self.assertFalse(reminders.load()[0]["alarm"]["enabled"])
                schedule.assert_not_called()
                notify.assert_called_once_with("Missed alarm", "Walk", suppress_sound=True)

    def test_save_uses_existing_timer_and_writes_only_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            with (patch.object(reminders, "state_file", return_value=Path(directory) / "reminders.json"),
                  patch.object(reminders, "schedule_alert", side_effect=OSError("timer failed")),
                  patch("sys.stdin", StringIO(json.dumps(self.payload))),
                  patch("time.time", return_value=stamp(7))):
                self.assertEqual(reminders.main(["alarm-save"]), 1)
                self.assertEqual(reminders.load(), [])

    def test_calendar_timer_uses_absolute_time_without_waking_the_pc(self):
        item = self.configure(stamp(7))
        due = item["due"]
        with (patch.object(reminders.subprocess, "run") as run,
              patch("time.time", return_value=stamp(7))):
            reminders.schedule_alert(item, due)
        command = run.call_args.args[0]
        self.assertIn("--on-calendar=2026-03-07 12:30:00 UTC", command)
        self.assertIn("--timer-property=WakeSystem=false", command)
        self.assertEqual(command[-3:], ["fire", item["id"], str(due)])

    def test_fall_back_alarm_uses_first_occurrence(self):
        timezone = ZoneInfo("America/New_York")
        now = int(datetime(2026, 11, 1, 0, 0, tzinfo=timezone).timestamp())
        first = int(datetime(2026, 11, 1, 1, 30, tzinfo=timezone, fold=0).timestamp())
        item = self.configure(now, clock="01:30", days=[6])
        self.assertEqual(item["due"], first)
        self.assertEqual(transition(item, first, first, advance), "ring")
        next_week = int(datetime(2026, 11, 8, 1, 30, tzinfo=timezone).timestamp())
        self.assertEqual(item["alerts"], [next_week])
