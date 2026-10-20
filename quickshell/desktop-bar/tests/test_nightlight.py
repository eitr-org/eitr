import datetime as dt
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[3] / "walker/scripts/actions/toggle/nightlight.py"
spec = importlib.util.spec_from_file_location("nightlight", SCRIPT)
nightlight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nightlight)


class NightlightTests(unittest.TestCase):
    def test_schedule_boundaries_and_manual_modes(self):
        for hour, expected in ((8, True), (9, False), (17, False), (18, True)):
            with self.subTest(hour=hour):
                now = dt.datetime(2026, 10, 7, hour)
                self.assertEqual(nightlight.desired("auto", now), expected)
                self.assertTrue(nightlight.desired("on", now))
                self.assertFalse(nightlight.desired("off", now))

    def test_custom_schedule_handles_minutes_and_daytime(self):
        overnight = {"start": "18:30", "end": "09:15"}
        daytime = {"start": "08:30", "end": "17:15"}
        for hour, minute, expected in ((18, 29, False), (18, 30, True),
                                       (9, 14, True), (9, 15, False)):
            self.assertEqual(nightlight.scheduled(dt.datetime(2026, 10, 7, hour, minute), overnight), expected)
        for hour, minute, expected in ((8, 29, False), (8, 30, True),
                                       (17, 14, True), (17, 15, False)):
            self.assertEqual(nightlight.scheduled(dt.datetime(2026, 10, 7, hour, minute), daytime), expected)

    def test_save_schedule_updates_timer_and_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(nightlight, "SCHEDULE_FILE", root / "schedule.json"), \
                    patch.object(nightlight, "TIMER_OVERRIDE", root / "timer.d/schedule.conf"), \
                    patch.object(nightlight.subprocess, "run") as run:
                nightlight.save_schedule("19:45", "07:30")
                self.assertEqual(nightlight.schedule(), {"start": "19:45", "end": "07:30"})
                self.assertIn("OnCalendar=*-*-* 19:45:00", (root / "timer.d/schedule.conf").read_text())
                self.assertIn("OnCalendar=*-*-* 07:30:00", (root / "timer.d/schedule.conf").read_text())
                self.assertEqual(run.call_count, 2)
                run.assert_any_call(["systemctl", "--user", "daemon-reload"], check=True)
                run.assert_any_call(["systemctl", "--user", "restart", "nightlight-auto.timer"], check=True)
                nightlight.save_schedule("19:45", "07:30")
                self.assertEqual(run.call_count, 2)
                with self.assertRaises(ValueError):
                    nightlight.save_schedule("12:00", "12:00")
                with self.assertRaises(ValueError):
                    nightlight.save_schedule("25:00", "09:00")

    def test_configure_saves_schedule_and_mode_together(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(nightlight, "STATE_DIR", root), \
                    patch.object(nightlight, "MODE_FILE", root / "mode"), \
                    patch.object(nightlight, "save_schedule") as save_schedule, \
                    patch.object(nightlight, "apply", return_value={}), \
                    patch("sys.argv", ["nightlight.py", "configure", "19:00", "08:00", "auto"]), \
                    patch("builtins.print"):
                self.assertEqual(nightlight.main(), 0)
                save_schedule.assert_called_once_with("19:00", "08:00")
                self.assertEqual(nightlight.mode(), "auto")

    def test_mode_is_saved_outside_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(nightlight, "STATE_DIR", root), \
                    patch.object(nightlight, "MODE_FILE", root / "mode"):
                self.assertEqual(nightlight.mode(), "auto")
                nightlight.save_mode("off")
                self.assertEqual(nightlight.mode(), "off")
                self.assertEqual((root / "mode").read_text(), "off\n")

    def test_apply_retries_until_hyprsunset_is_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(nightlight, "STATE_DIR", root), \
                    patch.object(nightlight, "MODE_FILE", root / "mode"), \
                    patch.object(nightlight, "APPLIED_FILE", root / "enabled"), \
                    patch.object(nightlight.shutil, "which", return_value="/usr/bin/tool"), \
                    patch.object(nightlight, "running", return_value=True), \
                    patch.object(nightlight, "scheduled", return_value=True), \
                    patch.object(nightlight.time, "sleep") as sleep, \
                    patch.object(nightlight.subprocess, "run", side_effect=[
                        SimpleNamespace(returncode=1, stderr="not ready"),
                        SimpleNamespace(returncode=0, stderr=""),
                    ]) as run:
                result = nightlight.apply()
                self.assertTrue(result["enabled"])
                self.assertTrue((root / "enabled").exists())
                self.assertEqual(run.call_count, 2)
                run.assert_any_call(["hyprctl", "hyprsunset", "temperature", "4000"],
                                    capture_output=True, text=True, check=False)
                sleep.assert_called_once_with(0.25)

    def test_manual_off_overrides_night_schedule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(nightlight, "STATE_DIR", root), \
                    patch.object(nightlight, "MODE_FILE", root / "mode"), \
                    patch.object(nightlight, "APPLIED_FILE", root / "enabled"), \
                    patch.object(nightlight.shutil, "which", return_value="/usr/bin/tool"), \
                    patch.object(nightlight, "running", return_value=True), \
                    patch.object(nightlight, "scheduled", return_value=True), \
                    patch.object(nightlight.subprocess, "run", return_value=SimpleNamespace(returncode=0, stderr="")) as run:
                nightlight.save_mode("off")
                (root / "enabled").touch()
                result = nightlight.apply()
                self.assertFalse(result["enabled"])
                self.assertFalse((root / "enabled").exists())
                run.assert_called_once_with(["hyprctl", "hyprsunset", "identity"],
                                            capture_output=True, text=True, check=False)


if __name__ == "__main__":
    unittest.main()
