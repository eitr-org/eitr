from home_isolation import setUpModule, tearDownModule
from menu_data import load as load_menu
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'walker/scripts/actions/tools'
sys.path.insert(0, str(TOOLS))
import calendars

SECRET = 'https://calendar.example.com/calendar/ical/private-0123456789abcdef/basic.ics'
NOW = datetime(2026, 10, 22, 12, tzinfo=timezone.utc).timestamp()


def ics(*events, name='Work', extra=''):
    body = ''.join('BEGIN:VEVENT\r\n' + event.strip().replace('\n', '\r\n') + '\r\nEND:VEVENT\r\n' for event in events)
    return f'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nX-WR-CALNAME:{name}\r\n{extra}{body}END:VCALENDAR\r\n'


def utc(row):
    return datetime.fromtimestamp(row['start'], timezone.utc).strftime('%Y-%m-%d %H:%M')


class ParserTests(unittest.TestCase):
    def parse(self, text):
        return calendars.parse_events(text, 'cal', 'Work', now=NOW)[1]

    def test_timezones_utc_windows_names_and_vtimezone_offsets(self):
        rows = self.parse(ics('UID:1\nDTSTART;TZID=Europe/Berlin:20261026T090000\nSUMMARY:Berlin',
                              'UID:2\nDTSTART:20261026T090000Z\nSUMMARY:UTC',
                              'UID:3\nDTSTART;TZID=Pacific Standard Time:20261023T080000\nSUMMARY:Outlook',
                              'UID:4\nDTSTART;TZID=/mozilla.org/20050126_1/America/New_York:20261023T080000\nSUMMARY:Prefixed',
                              'UID:5\nDTSTART;TZID=Odd Zone:20261024T080000\nSUMMARY:Custom',
                              extra='BEGIN:VTIMEZONE\r\nTZID:Odd Zone\r\nBEGIN:STANDARD\r\nTZOFFSETTO:+0530\r\nEND:STANDARD\r\nEND:VTIMEZONE\r\n'))
        found = {row['title']: utc(row) for row in rows}
        self.assertEqual(found, {'Berlin': '2026-10-26 08:00', 'UTC': '2026-10-26 09:00', 'Outlook': '2026-10-23 15:00',
                                 'Prefixed': '2026-10-23 12:00', 'Custom': '2026-10-24 02:30'})

    def test_floating_times_use_local_time(self):
        row = self.parse(ics('UID:1\nDTSTART:20261026T090000\nSUMMARY:Local'))[0]
        self.assertEqual(datetime.fromtimestamp(row['start']), datetime(2026, 10, 26, 9))

    def test_all_day_events_and_folded_escaped_lines(self):
        rows = self.parse(ics('UID:1\nDTSTART;VALUE=DATE:20261030\nDTEND;VALUE=DATE:20261101\nSUMMARY:Long\n  weekend\\, away\\; really',
                              'UID:2\nDTSTART;VALUE=DATE:20261025\nSUMMARY:One day'))
        self.assertEqual([(row['title'], row['date'], row['endDate'], row['allDay']) for row in rows],
                         [('One day', '2026-10-25', '2026-10-26', True), ('Long weekend, away; really', '2026-10-30', '2026-11-01', True)])

    def test_end_and_duration(self):
        rows = self.parse(ics('UID:1\nDTSTART:20261026T090000Z\nDTEND:20261026T103000Z\nSUMMARY:End',
                              'UID:2\nDTSTART:20261027T090000Z\nDURATION:PT45M\nSUMMARY:Duration'))
        self.assertEqual([row['end'] - row['start'] for row in rows], [5400, 2700])

    def test_weekly_recurrence_with_exceptions_overrides_and_count(self):
        rows = self.parse(ics('UID:a\nDTSTART;TZID=Europe/Berlin:20261019T090000\nDTEND;TZID=Europe/Berlin:20261019T093000\n'
                              'RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6\nEXDATE;TZID=Europe/Berlin:20261028T090000\nSUMMARY:Stand-up',
                              'UID:a\nRECURRENCE-ID;TZID=Europe/Berlin:20261102T090000\nDTSTART;TZID=Europe/Berlin:20261102T110000\nSUMMARY:Moved',
                              'UID:z\nDTSTART:20261029T090000Z\nSTATUS:CANCELLED\nSUMMARY:Gone'))
        # The wall clock stays 09:00 in Berlin across the end of summer time on 25 October.
        self.assertEqual([(row['title'], utc(row)) for row in rows],
                         [('Stand-up', '2026-10-19 07:00'), ('Stand-up', '2026-10-21 07:00'), ('Stand-up', '2026-10-26 08:00'),
                          ('Moved', '2026-11-02 10:00'), ('Stand-up', '2026-11-04 08:00')])
        self.assertEqual(len({row['key'] for row in rows}), len(rows))

    def test_monthly_yearly_until_and_interval(self):
        rows = self.parse(ics('UID:1\nDTSTART:20261030T150000Z\nRRULE:FREQ=MONTHLY;BYDAY=-1FR;UNTIL=20261231T000000Z\nSUMMARY:Last Friday',
                              'UID:2\nDTSTART:20260831T080000Z\nRRULE:FREQ=MONTHLY;BYMONTHDAY=31\nSUMMARY:Thirty-first',
                              'UID:3\nDTSTART;VALUE=DATE:20201103\nRRULE:FREQ=YEARLY\nSUMMARY:Birthday',
                              'UID:4\nDTSTART:20261020T070000Z\nRRULE:FREQ=DAILY;INTERVAL=10;UNTIL=20261115\nSUMMARY:Every ten days'))
        found = {}
        for row in rows:
            found.setdefault(row['title'], []).append(row.get('date') or utc(row))
        self.assertEqual(found['Last Friday'], ['2026-10-30 15:00', '2026-11-27 15:00'])
        # iCal skips months without a 31st instead of moving to the last day.
        self.assertEqual(found['Thirty-first'], ['2026-10-31 08:00'])
        self.assertEqual(found['Birthday'], ['2026-11-03'])
        self.assertEqual(found['Every ten days'], ['2026-10-20 07:00', '2026-10-30 07:00', '2026-11-09 07:00'])

    def test_unsupported_rules_show_only_the_first_event(self):
        rows = self.parse(ics('UID:1\nDTSTART:20261026T090000Z\nRRULE:FREQ=MONTHLY;BYDAY=MO,TU;BYSETPOS=-1\nSUMMARY:Odd'))
        self.assertEqual([utc(row) for row in rows], ['2026-10-26 09:00'])

    def test_events_outside_the_window_are_left_out(self):
        rows = self.parse(ics('UID:1\nDTSTART:20250101T090000Z\nSUMMARY:Old', 'UID:2\nDTSTART:20270601T090000Z\nSUMMARY:Far'))
        self.assertEqual(rows, [])

    def test_not_a_calendar(self):
        with self.assertRaises(calendars.CalendarError):
            self.parse('<html>Sign in</html>')


class AddressTests(unittest.TestCase):
    def test_only_https_and_webcal(self):
        self.assertEqual(calendars.normalize(' webcal://example.com/a.ics '), 'https://example.com/a.ics')
        self.assertEqual(calendars.normalize(SECRET), SECRET)
        for address in ('http://example.com/a.ics', 'file:///etc/passwd', 'https://', 'https://exa mple.com', '', None):
            self.assertIsNone(calendars.normalize(address), address)

    def test_fetch_errors_name_the_host_not_the_address(self):
        refused = urllib.error.HTTPError(SECRET, 404, 'Not Found', {}, io.BytesIO())
        self.addCleanup(refused.close)
        for error in (refused, urllib.error.URLError(SECRET), OSError(SECRET)):
            with self.subTest(error=type(error).__name__), patch.object(calendars.urllib.request.OpenerDirector, 'open', side_effect=error):
                with self.assertRaises(calendars.CalendarError) as raised:
                    calendars.fetch(SECRET, 'Work')
                self.assertNotIn('private', str(raised.exception))
                self.assertIn('calendar.example.com', str(raised.exception))

    def test_insecure_redirects_are_refused(self):
        handler = calendars.HttpsOnlyRedirects()
        with self.assertRaises(calendars.CalendarError):
            handler.redirect_request(None, None, 302, 'Found', {}, 'http://example.com/a.ics')

    def test_large_calendars_are_refused(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'x' * (calendars.MAX_BYTES + 1)
        with patch.object(calendars.urllib.request.OpenerDirector, 'open', return_value=response):
            with self.assertRaises(calendars.CalendarError):
                calendars.fetch(SECRET, 'Work')


class FlowTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        environment = patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.folder / 'config'),
                                              'XDG_CACHE_HOME': str(self.folder / 'cache'),
                                              'XDG_STATE_HOME': str(self.folder / 'state')})
        environment.start()
        self.addCleanup(environment.stop)
        self.calls = []
        for target, name in ((calendars.subprocess, 'run'), (calendars.subprocess, 'Popen'),
                             (calendars.reminders.subprocess, 'run'), (calendars.reminders.subprocess, 'Popen')):
            stub = patch.object(target, name, side_effect=lambda *arguments, **options: self.calls.append((arguments, options)))
            stub.start()
            self.addCleanup(stub.stop)
        for name in ('notify', 'chime'):
            stub = patch.object(calendars.reminders, name)
            setattr(self, name, stub.start())
            self.addCleanup(stub.stop)
        soon = datetime.fromtimestamp(NOW + 600, timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.text = ics(f'UID:1\nDTSTART:{soon}\nSUMMARY:Planning', 'UID:2\nDTSTART;VALUE=DATE:20261023\nSUMMARY:Holiday',
                        name='Team')

    def add(self, answers):
        provider = {'Google Calendar': 'google', 'Outlook': 'outlook', 'Other (any iCal address)': 'other'}[answers[0]]

        def wizard(title, steps):
            if steps[0].key == 'provider':
                return {'provider': provider}
            self.assertTrue(steps[0].secret)
            steps[0].validator(answers[1])
            values = {'address': answers[1]}
            values['name'] = (answers[2] if len(answers) > 2 else '') or steps[1].default(values)
            return values

        with patch.object(calendars, 'collect', side_effect=wizard), \
                patch.object(calendars, 'fetch', return_value=self.text), patch.object(calendars.time, 'time', return_value=NOW), \
                patch('sys.stdout', new_callable=io.StringIO) as output:
            result = calendars.add()
        self.assertNotIn(SECRET, output.getvalue())
        self.assertNotIn('private', output.getvalue())
        return result

    def assert_secret_kept(self):
        for arguments, options in self.calls:
            self.assertNotIn('private', json.dumps(arguments, default=str) + json.dumps(options, default=str))
        for call in self.notify.call_args_list:
            self.assertNotIn('private', json.dumps(call.args))

    def test_add_stores_privately_and_never_shows_the_address(self):
        self.assertEqual(self.add(['Google Calendar', SECRET.replace('https://', 'webcal://'), '']), 0)
        store = calendars.subscriptions_file()
        self.assertEqual(stat.S_IMODE(store.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(store.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(calendars.events_file().stat().st_mode), 0o600)
        saved = json.loads(store.read_text())
        self.assertEqual([(item['name'], item['url'], item['provider']) for item in saved], [('Team', SECRET, 'google')])
        self.assertNotIn('private', calendars.events_file().read_text())
        opened = [arguments[0] for arguments, _ in self.calls if arguments[0][:2] == [str(calendars.app_command([])[0]), 'xdg-open']]
        self.assertEqual(opened, [[str(ROOT / 'walker/bin/app-launch'), 'xdg-open', calendars.PROVIDERS['google']]])
        self.assertIn((['systemctl', '--user', 'enable', '--now', 'eitr-calendars.timer'],),
                      [arguments for arguments, _ in self.calls])
        self.assertEqual(self.notify.call_args.args[0], 'Calendar added')
        self.assert_secret_kept()
        rows = calendars.rows()
        self.assertEqual(rows, [{'id': saved[0]['id'], 'name': 'Team', 'host': 'calendar.example.com'}])

    def test_wizard_cancel_keeps_storage_untouched(self):
        for stage in (0, 1):
            calls = [{'provider': 'google'}, KeyboardInterrupt()] if stage else [KeyboardInterrupt()]
            with patch.object(calendars, 'collect', side_effect=calls), \
                    patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(calendars.add(), 0)
            self.assertIn('Nothing was added.', output.getvalue())
            self.assertFalse(calendars.subscriptions_file().exists())

    def test_add_refuses_insecure_or_repeated_addresses(self):
        self.assertEqual(self.add(['Other (any iCal address)', 'http://example.com/a.ics']), 1)
        self.assertFalse(calendars.subscriptions_file().exists())
        self.assertEqual(self.add(['Other (any iCal address)', SECRET, 'Mine']), 0)
        self.assertEqual(self.add(['Outlook', SECRET]), 1)
        self.assertEqual(len(calendars.load_calendars()), 1)
        self.assertEqual(calendars.load_calendars()[0]['name'], 'Mine')
        self.assert_secret_kept()

    def test_refresh_failure_keeps_events_and_hides_the_address(self):
        self.add(['Other (any iCal address)', SECRET, 'Mine'])
        before = json.loads(calendars.events_file().read_text())['events']
        stderr = io.StringIO()
        with patch.object(calendars.urllib.request.OpenerDirector, 'open', side_effect=OSError(SECRET)), \
                patch.object(sys, 'stderr', stderr):
            self.assertEqual(calendars.refresh(now=NOW), 1)
        self.assertEqual(json.loads(calendars.events_file().read_text())['events'], before)
        self.assertIn('Mine (calendar.example.com)', stderr.getvalue())
        self.assertNotIn('private', stderr.getvalue())

    def test_alerts_fire_once_and_skip_moved_events(self):
        self.add(['Other (any iCal address)', SECRET, 'Mine'])
        timers = [arguments[0] for arguments, _ in self.calls if arguments[0][0] == 'systemd-run']
        self.assertEqual(len(timers), 1, 'only the timed event in the next refresh window gets a timer')
        self.assertIn('--on-active=600s', timers[0])
        key = timers[0][-1]
        self.assertEqual(timers[0][-2:], ['fire', key])
        self.assertEqual(calendars.fire(key, now=NOW + 600), 0)
        self.assertEqual(calendars.fire(key, now=NOW + 601), 0)
        self.assertEqual([call.args[0] for call in self.notify.call_args_list].count('Planning'), 1)
        self.assertEqual(self.chime.call_count, 1)
        self.calls.clear()
        calendars.refresh({calendars.load_calendars()[0]['id']: self.text}, now=NOW + 60)
        self.assertFalse([arguments for arguments, _ in self.calls if arguments[0][0] == 'systemd-run'],
                         'an event that already alerted gets no new timer')
        calendars.fire('no-such-event', now=NOW)
        self.assertEqual(self.chime.call_count, 1)

    def test_remove_asks_and_esc_keeps_the_calendar(self):
        self.add(['Other (any iCal address)', SECRET, 'Mine'])
        identifier = calendars.load_calendars()[0]['id']
        with patch.object(calendars.reminders, 'ask', return_value=None):
            calendars.remove(identifier)
        self.assertEqual(len(calendars.load_calendars()), 1)
        with patch.object(calendars.reminders, 'ask', side_effect=lambda placeholder, choices: choices[0]) as ask:
            calendars.remove(identifier)
        self.assertEqual(ask.call_args.args[1], ["Remove 'Mine'"])
        self.assertEqual(calendars.load_calendars(), [])
        self.assertEqual(json.loads(calendars.events_file().read_text())['events'], [])
        self.assertIn((['systemctl', '--user', 'disable', '--now', 'eitr-calendars.timer'],),
                      [arguments for arguments, _ in self.calls])


    def test_opening_the_panel_refreshes_only_when_a_minute_has_passed(self):
        self.assertEqual(calendars.main(['refresh', '--if-older', '60']), 0, 'no calendars: nothing to do')
        self.add(['Other (any iCal address)', SECRET, 'Mine'])
        calendars.write_private(calendars.events_file(), {'updated': int(time.time()), 'events': []})
        with patch.object(calendars, 'refresh', return_value=0) as refresh:
            calendars.main(['refresh', '--if-older', '60'])
            refresh.assert_not_called()
            with patch.object(calendars.time, 'time', return_value=time.time() + 61):
                calendars.main(['refresh', '--if-older', '60'])
            refresh.assert_called_once_with()
        self.assertEqual(calendars.main(['refresh', '--if-older', 'soon']), 2)
        panel = (ROOT / 'quickshell/desktop-bar/CalendarMenu.qml').read_text()
        self.assertIn('calendars.py"), "refresh", "--if-older", "60"]', panel)

    def test_enter_refreshes_and_reports_without_the_address(self):
        self.add(['Other (any iCal address)', SECRET, 'Mine'])
        self.notify.reset_mock()
        with patch.object(calendars, 'refresh', return_value=0):
            self.assertEqual(calendars.main(['sync']), 0)
        title, body = self.notify.call_args.args
        self.assertEqual(title, 'Calendars refreshed')
        self.assertNotIn(SECRET, body)


class MenuTests(unittest.TestCase):
    def test_calendars_menu_lives_under_tools(self):
        menu = load_menu('calendars')
        self.assertEqual(menu['parent'], 'tools')
        self.assertEqual([entry['text'] for entry in menu['entries']], ['Add Calendar…'])
        self.assertTrue(menu['entries'][0]['actions']['open'].endswith('tools/calendars.py add'))
        row = next(entry for entry in load_menu('tools')['entries'] if entry['text'] == 'Calendars')
        self.assertEqual((row['subtext'], row['submenu']), ('>', 'calendars'))
        lua = (ROOT / 'elephant/menus/calendars.lua').read_text()
        self.assertIn('" rows")', lua)
        self.assertIn('calendar_delete = "python3 " .. quote(helper) .. " remove " .. quote(calendar.id)', lua)
        self.assertIn('open = "python3 " .. quote(helper) .. " sync"', lua)
        config = (ROOT / 'walker/config.toml').read_text()
        self.assertIn('{ action = "calendar_delete", label = "Delete", bind = "Delete", after = "Close" }', config)
        self.assertNotIn('url', lua)

    def test_units_ship_with_the_package(self):
        service = (ROOT / 'systemd/user/eitr-calendars.service').read_text()
        self.assertIn('tools/calendars.py refresh', service)
        timer = (ROOT / 'systemd/user/eitr-calendars.timer').read_text()
        self.assertIn('OnUnitActiveSec=15min', timer)
        self.assertIn('OnStartupSec=', timer)


if __name__ == '__main__':
    unittest.main()
