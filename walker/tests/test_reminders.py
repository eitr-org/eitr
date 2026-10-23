from home_isolation import setUpModule, tearDownModule
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
import unittest.mock

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

    def test_this_and_next_weekday(self):
        now = datetime(2026, 10, 22, 11, 0)  # a Thursday
        stamp = lambda phrase: datetime.fromtimestamp(reminders.when(phrase, now)).strftime('%a %d %H:%M')
        self.assertEqual(stamp('friday 10:30'), 'Fri 23 10:30')
        self.assertEqual(stamp('this friday 10:30'), 'Fri 23 10:30')
        self.assertEqual(stamp('next friday 10:30'), 'Fri 30 10:30')
        self.assertEqual(stamp('next monday 09:00'), 'Mon 26 09:00')

    def test_a_date_without_a_time_asks_for_one(self):
        for phrase in ("every month on the 29th", "friday", "tomorrow", "weekdays"):
            self.assertFalse(reminders.has_time(phrase), phrase)
        for phrase in ("today 13:00", "every monday 09:00", "20m", "90", "2026-10-30 09:00"):
            self.assertTrue(reminders.has_time(phrase), phrase)
        with unittest.mock.patch.object(reminders, "ask_time", return_value="10:00") as ask:
            self.assertEqual(reminders.with_time("every month on the 29th"), "every month on the 29th 10:00")
            self.assertEqual(reminders.with_time("18:30"), "18:30")
            self.assertEqual(reminders.with_time("whenever"), "whenever", "not a date: the parser refuses it")
            self.assertEqual(ask.call_count, 1)
        for answer in (None, "soon"):
            with unittest.mock.patch.object(reminders, "ask_time", return_value=answer):
                self.assertIsNone(reminders.with_time("friday"))

    def test_everyday_phrasing(self):
        now = datetime(2026, 10, 22, 17, 14)
        stamp = lambda phrase: datetime.fromtimestamp(reminders.parse_when(phrase, now)[0]).strftime('%d %H:%M')
        for phrase, expected in [('in one minute', '22 17:15'), ('in 1 minute', '22 17:15'), ('in half an hour', '22 17:44'),
                                 ('1 hour and 30 minutes', '22 18:44'), ('9am', '23 09:00'), ('9:30 PM', '22 21:30'),
                                 ('12am', '23 00:00'), ('tomorrow at 3pm', '23 15:00'), ('friday at noon', '23 12:00'),
                                 ('Oct 30 3pm', '30 15:00'), ('every 29th at 09:00 am', '29 09:00')]:
            self.assertEqual(stamp(phrase), expected, phrase)
        self.assertEqual(reminders.parse_when('every 29th', now)[1], {'frequency': 'monthly', 'day_of_month': 29})
        self.assertFalse(reminders.has_time('every 29th'))
        self.assertIsNone(reminders.parse_when('13pm', now)[0])
        with unittest.mock.patch.object(reminders, "ask_time", return_value="9 am"):
            self.assertEqual(reminders.with_time("every 29th"), "every 29th 09:00")

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
        for name in ("systemd-run", "systemctl", "notify-send", "eitr-shell", "pw-play"):
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

    def test_a_repeat_is_named_in_the_confirmation(self):
        result = self.run_script("new", "every day 08:00", "Stretch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("↻ Daily", result.stdout)

    def test_alerts_chime_unless_do_not_disturb(self):
        sound = self.folder / "alarm.oga"
        sound.write_bytes(b"")
        for status, plays in (('{"doNotDisturb":false}', True), ('{"doNotDisturb":true}', False), ("", True)):
            with self.subTest(status=status), unittest.mock.patch.object(reminders, "ALERT_SOUND", sound), \
                    unittest.mock.patch.object(reminders.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, status)), \
                    unittest.mock.patch.object(reminders.subprocess, "Popen") as play:
                reminders.chime()
            self.assertEqual(play.called, plays)
            if plays:
                self.assertEqual(play.call_args.args[0], ["pw-play", "--volume=0.7", str(sound)])

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
        self.assertIn(f"systemctl --user stop eitr-reminder-{identifier}-", self.calls_made())
        self.assertEqual(json.loads(self.state.read_text()), [])
        self.assertIn("No reminders.", self.run_script("list").stdout)

    def test_menus_and_command_offer_it(self):
        reminders = load_menu("reminders")
        self.assertEqual([entry["text"] for entry in reminders["entries"]], ["New Reminder", "Tell the assistant…", "Upcoming Reminders"])
        self.assertEqual(reminders["parent"], "tools")
        tools = json.loads((ROOT / "elephant/menu-rows/tools.json").read_text())
        self.assertEqual([row["text"] for row in tools], ["Calendars", "Capture", "Plugins", "Reminders", "Share", "Music Visualizer"])
        main = json.loads((ROOT / "elephant/menu-rows/main.json").read_text())
        tools_row = next(row for row in main if row["text"] == "Tools")
        self.assertEqual(tools_row["submenu"], "tools")
        self.assertIn('/walker/scripts/actions/tools/reminders.py", "restore"',
                      (ROOT / "quickshell/desktop-bar/shell.qml").read_text())
        self.assertIn('"tools/reminders.py"', (ROOT / "distro/bin/eitr").read_text())


if __name__ == "__main__":
    unittest.main()


class RepeatTests(unittest.TestCase):
    def setUp(self):
        quiet = unittest.mock.patch.object(reminders, "chime")
        quiet.start()
        self.addCleanup(quiet.stop)

    def test_common_phrases(self):
        now = datetime(2026, 10, 16, 14)
        for phrase, expected, frequency in [
            ('every day 08:00', datetime(2026, 10, 17, 8), 'daily'),
            ('every Monday 09:30', datetime(2026, 10, 19, 9, 30), 'weekly'),
            ('weekdays 07:00', datetime(2026, 10, 19, 7), 'weekly'),
            ('every Monday and Thursday 09:30', datetime(2026, 10, 19, 9, 30), 'weekly'),
            ('every month on the 31st', datetime(2026, 10, 31, 9), 'monthly')]:
            due, rule = reminders.parse_when(phrase, now)
            self.assertEqual(datetime.fromtimestamp(due), expected)
            self.assertEqual(rule['frequency'], frequency)
        self.assertEqual(reminders.parse_when('every someday', now), (None, None))

    def test_month_and_leap_year_clamping_retains_anchor(self):
        anchor = datetime(2028, 1, 31, 8)
        self.assertEqual(reminders.occurrence(anchor, {'frequency':'monthly'}, 1), datetime(2028, 2, 29, 8))
        self.assertEqual(reminders.occurrence(anchor, {'frequency':'monthly'}, 2), datetime(2028, 3, 31, 8))
        self.assertEqual(reminders.occurrence(datetime(2028, 2, 29, 8), {'frequency':'yearly'}, 4), datetime(2032, 2, 29, 8))

    def test_strict_rules(self):
        for rule in [{}, {'frequency':'hourly'}, {'frequency':'daily','interval':True},
                     {'frequency':'weekly','weekdays':[0,0]}, {'frequency':'monthly','day_of_month':32},
                     {'frequency':'daily','weekdays':[0]}, {'frequency':'daily','count':0},
                     {'frequency':'daily','until':'2026-02-30'}, {'frequency':'daily','until':'2026-10-30','count':2},
                     {'frequency':'daily','command':'x'}]:
            with self.assertRaises(ValueError, msg=str(rule)):
                reminders.repeat_rule(rule)

    def test_missed_series_once_offsets_count_and_cancel(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_STATE_HOME':directory}), patch.object(reminders, 'schedule') as schedule, patch.object(reminders, 'stop_timers'), patch.object(reminders, 'notify') as notify:
            anchor = datetime(2026, 10, 1, 9)
            due = int(anchor.timestamp())
            item = {'id':'series','text':'Stretch','due':due,'alerts':[due-3600,due],
                    'repeat':{'frequency':'daily','count':12},'repeat_anchor':anchor.isoformat(),
                    'repeat_index':0,'alert_offsets':[3600,0]}
            reminders.save([item])
            now = int(datetime(2026, 10, 8, 12).timestamp())
            with patch.object(reminders.time, 'time', return_value=now):
                reminders.restore()
                notify.assert_called_once()
                saved = reminders.load()[0]
                self.assertEqual(saved['repeat_index'], 8)
                self.assertEqual(datetime.fromtimestamp(saved['due']), datetime(2026, 10, 9, 9))
                self.assertEqual(saved['alerts'], [saved['due']-3600, saved['due']])
                reminders.cancel('series', 'occurrence')
                self.assertEqual(reminders.load()[0]['repeat_index'], 9)
                reminders.cancel('series', 'series')
                self.assertEqual(reminders.load(), [])
            self.assertEqual(schedule.call_count, 2)

    def test_dst_wall_clock_and_until(self):
        from unittest.mock import patch
        if not hasattr(time, 'tzset'):
            self.skipTest('tzset required')
        original = os.environ.get('TZ')
        try:
            os.environ['TZ'] = 'America/New_York'
            time.tzset()
            anchor = datetime(2026, 3, 7, 8)
            tomorrow = reminders.occurrence(anchor, {'frequency':'daily'}, 1)
            self.assertEqual(tomorrow.hour, 8)
            self.assertEqual(tomorrow.timestamp()-anchor.timestamp(), 23*3600)
            item = {'repeat':{'frequency':'daily','until':'2026-03-08'},'repeat_anchor':anchor.isoformat(), 'alert_offsets':[0]}
            self.assertTrue(reminders.advance(item, int(anchor.timestamp())))
            self.assertFalse(reminders.advance(item, item['due']))
        finally:
            if original is None:
                os.environ.pop('TZ', None)
            else:
                os.environ['TZ'] = original
            time.tzset()

    def test_firing_advances_only_at_event_and_rejects_stale_timer(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_STATE_HOME':directory}), patch.object(reminders, 'schedule') as schedule, patch.object(reminders, 'stop_timers'), patch.object(reminders, 'notify') as notify:
            now = int(datetime(2026, 10, 1, 8).timestamp())
            with patch.object(reminders.time, 'time', return_value=now):
                item = reminders.create('Appointment', now+7200, appointment=True, repeat={'frequency':'daily','count':2})
                reminders.fire(item['id'], moment=now+3600)
                self.assertEqual(reminders.load()[0]['due'], now+7200)
                reminders.fire(item['id'], moment=now+7200)
                next_item = reminders.load()[0]
                self.assertEqual(next_item['repeat_index'], 1)
                self.assertEqual(next_item['alerts'], [next_item['due']-3600, next_item['due']])
                reminders.fire(item['id'], moment=now+7200)
                self.assertEqual(notify.call_count, 2)
                reminders.fire(item['id'], moment=next_item['due']-3600)
                reminders.fire(item['id'], moment=next_item['due'])
                self.assertEqual(reminders.load(), [])
                self.assertEqual(schedule.call_count, 2)


class NativeTimePickerTests(unittest.TestCase):
    def test_set_and_cancel_use_private_runtime_and_remove_answer(self):
        for value in ('09:30\n', ''):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                def ipc(command, **options):
                    self.assertEqual(command[:7], ['eitr-shell', 'desktop-bar', 'ipc', 'call', 'timepicker', 'open', 'request_1'])
                    (Path(directory) / 'eitr-time-picker/request_1').write_text(value)
                    return subprocess.CompletedProcess(command, 0)
                with unittest.mock.patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                     unittest.mock.patch.object(reminders.secrets, 'token_hex', return_value='request_1'), \
                     unittest.mock.patch.object(reminders.subprocess, 'run', side_effect=ipc):
                    self.assertEqual(reminders.ask_time('Question', 'Dentist'), value.strip() or None)
                folder = Path(directory) / 'eitr-time-picker'
                self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
                self.assertEqual(list(folder.iterdir()), [])

    def test_ipc_failure_falls_back_to_walker(self):
        with tempfile.TemporaryDirectory() as directory, \
             unittest.mock.patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
             unittest.mock.patch.object(reminders.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), \
             unittest.mock.patch.object(reminders, 'ask', return_value='9:30') as ask:
            self.assertEqual(reminders.ask_time('Question'), '9:30')
            ask.assert_called_once_with('Question')

    def test_invalid_request_ids_never_reach_paths_or_ipc(self):
        for request in ('../escape', '', 'a' * 65, 'a/b', 'request\n'):
            with self.subTest(request=request), tempfile.TemporaryDirectory() as directory, \
                 unittest.mock.patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                 unittest.mock.patch.object(reminders.secrets, 'token_hex', return_value=request), \
                 unittest.mock.patch.object(reminders.subprocess, 'run') as ipc, \
                 unittest.mock.patch.object(reminders, 'ask', return_value=None):
                self.assertIsNone(reminders.ask_time('Question'))
                ipc.assert_not_called()
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_with_time_passes_subtitle(self):
        with unittest.mock.patch.object(reminders, 'ask_time', return_value='09:30') as ask:
            self.assertEqual(reminders.with_time('tomorrow', 'Dentist'), 'tomorrow 09:30')
            ask.assert_called_once_with('At what time?', 'Dentist')
