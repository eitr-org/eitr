#!/usr/bin/env python3
"""Read-only calendar subscriptions through a calendar's secret iCal address.

  calendars.py add         ask for the provider, the address and a name
  calendars.py rows        JSON rows for the Walker menu (names and hosts only)
  calendars.py remove ID   ask, then forget that calendar
  calendars.py refresh     fetch every calendar, cache its events, time the alerts
  calendars.py fire KEY    (a timer runs this) alert for one event

The addresses are secrets: they live only in $XDG_CONFIG_HOME/eitr/calendars/
subscriptions.json (folder 0700, file 0600) and never reach a command line, a log,
a notification or an error message, which name the calendar and its host instead.
Events from a week ago to 60 days ahead are cached in
$XDG_CACHE_HOME/eitr/calendar-events.json for the calendar panel. eitr-calendars.timer
refreshes them every 15 minutes and at login while at least one calendar exists.

The iCal reader covers VEVENT start, end or duration, summary and UID; UTC, TZID
(IANA names, common Windows names, else the VTIMEZONE standard offset) and floating
times; all-day events; EXDATE; RECURRENCE-ID overrides; and RRULE with FREQ
DAILY, WEEKLY (BYDAY), MONTHLY (one BYMONTHDAY or one BYDAY such as 1MO or -1FR) or
YEARLY, plus INTERVAL, COUNT and UNTIL. Rules with other parts (BYSETPOS,
BYWEEKNO, BYYEARDAY, BYHOUR, several month days...) show only their first event.
"""
import eitr_bootstrap
from eitr_i18n import tr
from eitr_wizard import collect, Step
from eitr_paths import cache, config, state
from contextlib import contextmanager
from datetime import date, datetime, time as clock, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import reminders

TIMER = 'eitr-calendars.timer'
MAX_BYTES = 5 * 1024 * 1024
TIMEOUT = 20
PAST_DAYS = 7
FUTURE_DAYS = 60
# Refreshes run every 15 minutes; events starting before the next one get a timer now.
ALERT_HORIZON = 20 * 60
MAX_EVENTS = 2000
PROVIDERS = {
    'google': 'https://calendar.google.com/calendar/r/settings',
    'outlook': 'https://outlook.live.com/calendar/0/options/calendar/SharedCalendars',
}
DAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
WINDOWS_ZONES = {
    'AUS Eastern Standard Time': 'Australia/Sydney', 'Alaskan Standard Time': 'America/Anchorage',
    'Arabian Standard Time': 'Asia/Dubai', 'Argentina Standard Time': 'America/Argentina/Buenos_Aires',
    'Atlantic Standard Time': 'America/Halifax', 'Central Europe Standard Time': 'Europe/Budapest',
    'Central European Standard Time': 'Europe/Warsaw', 'Central Standard Time': 'America/Chicago',
    'Central Standard Time (Mexico)': 'America/Mexico_City', 'China Standard Time': 'Asia/Shanghai',
    'E. Australia Standard Time': 'Australia/Brisbane', 'E. Europe Standard Time': 'Europe/Chisinau',
    'E. South America Standard Time': 'America/Sao_Paulo', 'Eastern Standard Time': 'America/New_York',
    'Egypt Standard Time': 'Africa/Cairo', 'FLE Standard Time': 'Europe/Kiev', 'GMT Standard Time': 'Europe/London',
    'GTB Standard Time': 'Europe/Bucharest', 'Greenwich Standard Time': 'Atlantic/Reykjavik',
    'Hawaiian Standard Time': 'Pacific/Honolulu', 'India Standard Time': 'Asia/Kolkata',
    'Israel Standard Time': 'Asia/Jerusalem', 'Korea Standard Time': 'Asia/Seoul',
    'Morocco Standard Time': 'Africa/Casablanca', 'Mountain Standard Time': 'America/Denver',
    'New Zealand Standard Time': 'Pacific/Auckland', 'Newfoundland Standard Time': 'America/St_Johns',
    'Pacific SA Standard Time': 'America/Santiago', 'Pacific Standard Time': 'America/Los_Angeles',
    'Pakistan Standard Time': 'Asia/Karachi', 'Romance Standard Time': 'Europe/Paris',
    'Russian Standard Time': 'Europe/Moscow', 'SA Pacific Standard Time': 'America/Bogota',
    'SE Asia Standard Time': 'Asia/Bangkok', 'Singapore Standard Time': 'Asia/Singapore',
    'South Africa Standard Time': 'Africa/Johannesburg', 'Taipei Standard Time': 'Asia/Taipei',
    'Tokyo Standard Time': 'Asia/Tokyo', 'Turkey Standard Time': 'Europe/Istanbul',
    'US Mountain Standard Time': 'America/Phoenix', 'UTC': 'UTC',
    'W. Australia Standard Time': 'Australia/Perth', 'W. Central Africa Standard Time': 'Africa/Lagos',
    'W. Europe Standard Time': 'Europe/Berlin',
}


class CalendarError(Exception):
    """A message that is safe to show: it never contains the address."""


# Storage --------------------------------------------------------------------

def subscriptions_file():
    return config('eitr/calendars/subscriptions.json')


def events_file():
    return cache('eitr/calendar-events.json')


def alerts_file():
    return state('eitr/calendar-alerts.json')


def write_private(path, value):
    """Atomically write JSON readable only by this user."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
    try:
        with os.fdopen(descriptor, 'w') as output:
            json.dump(value, output, indent=2)
            output.write('\n')
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def load_calendars():
    data = read_json(subscriptions_file(), [])
    return [item for item in data if isinstance(item, dict) and isinstance(item.get('id'), str)
            and isinstance(item.get('name'), str) and isinstance(item.get('url'), str)] if isinstance(data, list) else []


def save_calendars(calendars):
    folder = subscriptions_file().parent
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(folder, 0o700)
    write_private(subscriptions_file(), calendars)


@contextmanager
def locked():
    path = state('eitr/calendars.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield


def normalize(address):
    """The https address for a pasted one, or None. webcal:// is iCal's name for https."""
    address = (address or '').strip()
    if address.lower().startswith('webcal://'):
        address = 'https://' + address[len('webcal://'):]
    if len(address) > 4096 or any(ord(character) <= 32 or ord(character) == 127 for character in address):
        return None
    try:
        parts = urllib.parse.urlsplit(address)
    except ValueError:
        return None
    return address if parts.scheme.lower() == 'https' and parts.hostname else None


def host(address):
    try:
        return urllib.parse.urlsplit(address).hostname or '?'
    except ValueError:
        return '?'


# Fetching -------------------------------------------------------------------

class HttpsOnlyRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_address):
        if urllib.parse.urlsplit(new_address).scheme.lower() != 'https':
            raise CalendarError(tr('The calendar server redirected to an insecure address.'))
        return super().redirect_request(request, fp, code, message, headers, new_address)


def fetch(address, name):
    """The calendar's text. Errors name the calendar and host, never the address."""
    where = f'{name} ({host(address)})'
    opener = urllib.request.build_opener(HttpsOnlyRedirects)
    request = urllib.request.Request(address, headers={'User-Agent': 'Eitr calendars', 'Accept': 'text/calendar'})
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            body = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise CalendarError(tr('{calendar}: the server answered HTTP {status}.', calendar=where, status=error.code)) from None
    except CalendarError:
        raise
    except (OSError, ValueError, urllib.error.URLError):
        raise CalendarError(tr('{calendar}: could not connect.', calendar=where)) from None
    if len(body) > MAX_BYTES:
        raise CalendarError(tr('{calendar}: the calendar is larger than 5 MB.', calendar=where))
    return body.decode('utf-8', errors='replace')


# iCal reading ---------------------------------------------------------------

def split_line(line):
    """NAME;PARAM=VALUE:VALUE into (NAME, {PARAM: VALUE}, VALUE); colons inside quotes are data."""
    quoted = False
    for index, character in enumerate(line):
        if character == '"':
            quoted = not quoted
        elif character == ':' and not quoted:
            head, value = line[:index], line[index + 1:]
            break
    else:
        return None
    fields = re.findall(r'(?:[^;"]|"[^"]*")+', head)
    if not fields:
        return None
    params = {}
    for field in fields[1:]:
        key, _, data = field.partition('=')
        params[key.strip().upper()] = data.strip().strip('"')
    return fields[0].strip().upper(), params, value


def content_lines(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n[ \t]', '', text)  # unfold continuation lines
    for line in text.split('\n'):
        parsed = split_line(line) if line.strip() else None
        if parsed:
            yield parsed


def read_components(text):
    """(calendar name, [VEVENT properties], {TZID: standard UTC offset in seconds})."""
    events, zones, name = [], {}, None
    stack = []
    for key, params, value in content_lines(text):
        if key == 'BEGIN':
            stack.append((value.strip().upper(), {}))
        elif key == 'END':
            kind = value.strip().upper()
            if not stack or stack[-1][0] != kind:
                continue
            _, properties = stack.pop()
            if kind == 'VEVENT':
                events.append(properties)
            elif kind == 'STANDARD' and stack and stack[-1][0] == 'VTIMEZONE' and 'TZOFFSETTO' in properties:
                stack[-1][1]['_standard'] = properties['TZOFFSETTO']
            elif kind == 'VTIMEZONE' and 'TZID' in properties and '_standard' in properties:
                offset = re.fullmatch(r'([+-])(\d{2})(\d{2})(\d{2})?', properties['_standard'][0][1].strip())
                if offset:
                    seconds = int(offset[2]) * 3600 + int(offset[3]) * 60 + int(offset[4] or 0)
                    zones[properties['TZID'][0][1].strip()] = -seconds if offset[1] == '-' else seconds
        elif stack:
            stack[-1][1].setdefault(key, []).append((params, value))
            if key == 'X-WR-CALNAME' and stack[-1][0] == 'VCALENDAR':
                name = unescape(value)
    return name, events, zones


def unescape(value):
    return re.sub(r'\\([nN,;\\])', lambda match: '\n' if match[1] in 'nN' else match[1], value).strip()


def zone_for(tzid, zones):
    name = tzid.strip().strip('"')
    parts = [part for part in name.split('/') if part]
    candidates = [name, WINDOWS_ZONES.get(name)] + ['/'.join(parts[index:]) for index in range(1, len(parts))]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ZoneInfo(candidate)
        except (ZoneInfoNotFoundError, ValueError, OSError):
            continue
    if name in zones:
        return timezone(timedelta(seconds=zones[name]))
    return None  # floating: this computer's local time


def parse_moment(params, value, zones):
    """A date (all-day), an aware datetime, or a naive datetime in local time."""
    value = value.strip()
    if params.get('VALUE', '').upper() == 'DATE' or re.fullmatch(r'\d{8}', value):
        return datetime.strptime(value[:8], '%Y%m%d').date()
    match = re.fullmatch(r'(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(Z?)', value)
    if not match:
        raise ValueError('bad date-time')
    numbers = [int(part) for part in match.groups()[:6]]
    moment = datetime(*numbers[:5], min(numbers[5], 59))
    if match[7]:
        return moment.replace(tzinfo=timezone.utc)
    if 'TZID' in params:
        zone = zone_for(params['TZID'], zones)
        return moment.replace(tzinfo=zone) if zone else moment
    return moment


def epoch(moment):
    if not isinstance(moment, datetime):
        moment = datetime.combine(moment, clock())
    return moment.timestamp()


DURATION = re.compile(r'([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?')


def parse_duration(value):
    match = DURATION.fullmatch(value.strip().upper())
    if not match or not any(match.groups()[1:]):
        raise ValueError('bad duration')
    weeks, days, hours, minutes, seconds = (int(part or 0) for part in match.groups()[1:])
    length = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return -length if match[1] == '-' else length


def parse_rule(text, start):
    """The reminders-style rule for an RRULE, or None when it uses unsupported parts."""
    parts = {}
    for item in text.upper().split(';'):
        key, _, value = item.partition('=')
        if key:
            parts[key.strip()] = value.strip()
    frequency = {'DAILY': 'daily', 'WEEKLY': 'weekly', 'MONTHLY': 'monthly', 'YEARLY': 'yearly'}.get(parts.pop('FREQ', ''))
    if not frequency:
        return None
    try:
        rule = {'frequency': frequency, 'interval': max(1, int(parts.pop('INTERVAL', '1')))}
        if 'COUNT' in parts:
            rule['count'] = max(1, int(parts.pop('COUNT')))
    except ValueError:
        return None
    rule['until'] = parts.pop('UNTIL', None)
    parts.pop('WKST', None)
    by_day, month_day, month = parts.pop('BYDAY', None), parts.pop('BYMONTHDAY', None), parts.pop('BYMONTH', None)
    if parts:
        return None
    if month and (frequency != 'yearly' or month != str(start.month)):
        return None
    if by_day:
        days = by_day.split(',')
        nth = re.fullmatch(r'([+-]?[1-5])(MO|TU|WE|TH|FR|SA|SU)', days[0])
        if frequency == 'weekly' and all(day in DAYS for day in days):
            rule['weekdays'] = sorted({DAYS.index(day) for day in days})
        elif frequency == 'monthly' and len(days) == 1 and nth:
            rule['nth'] = (int(nth[1]), DAYS.index(nth[2]))
        else:
            return None
    if month_day:
        if not re.fullmatch(r'\d{1,2}', month_day) or 'nth' in rule:
            return None
        if frequency == 'monthly':
            rule['day_of_month'] = int(month_day)
        elif frequency != 'yearly' or int(month_day) != start.day:
            return None
    return rule


def nth_weekday(year, month, nth, weekday):
    first = date(year, month, 1)
    days = (date(year + month // 12, month % 12 + 1, 1) - first).days
    matches = [day for day in range(1, days + 1) if date(year, month, day).weekday() == weekday]
    index = nth - 1 if nth > 0 else nth
    return matches[index] if -len(matches) <= index < len(matches) else None


def candidates(start, rule):
    """Every start the rule produces, in order, DTSTART first."""
    yield start
    if 'nth' in rule:
        nth, weekday = rule['nth']
        for index in range(1, 100000):
            year, month = divmod(start.year * 12 + start.month - 1 + index * rule['interval'], 12)
            day = nth_weekday(year, month + 1, nth, weekday)
            if day:
                yield start.replace(year=year, month=month + 1, day=day)
        return
    wanted = rule.get('day_of_month', start.day)
    for index in range(1, 100000):
        moment = reminders.occurrence(start, rule, index)
        # reminders move the 31st to a short month's last day; iCal skips that month.
        if rule['frequency'] in ('monthly', 'yearly') and moment.day != wanted:
            continue
        yield moment


def within(moment, until):
    if until is None:
        return True
    if not isinstance(until, datetime):
        return (moment.date() if isinstance(moment, datetime) else moment) <= until
    return epoch(moment) <= epoch(until)


def first(properties, key):
    values = properties.get(key)
    return values[0] if values else None


def instances(properties, zones, window_start, window_end, skipped=frozenset()):
    """(start, end) pairs of one VEVENT inside the window."""
    start_field = first(properties, 'DTSTART')
    if not start_field:
        return []
    start = parse_moment(*start_field, zones)
    all_day = not isinstance(start, datetime)
    end_field, duration = first(properties, 'DTEND'), first(properties, 'DURATION')
    length = None
    if end_field:
        end = parse_moment(*end_field, zones)
        try:
            length = end - start if isinstance(end, datetime) != all_day else None
        except TypeError:  # one side floating, the other in a zone
            length = None
    elif duration:
        length = parse_duration(duration[1])
    if length is None or length < timedelta():
        length = timedelta(days=1) if all_day else timedelta()
    if all_day and length < timedelta(days=1):
        length = timedelta(days=1)
    excluded = set(skipped)
    for params, value in properties.get('EXDATE', []):
        for item in value.split(','):
            try:
                excluded.add(epoch(parse_moment(params, item, zones)))
            except ValueError:
                continue
    rule_field = first(properties, 'RRULE')
    rule = parse_rule(rule_field[1], start) if rule_field else None
    until = None
    if rule and rule.get('until'):
        try:
            until = parse_moment({}, rule['until'], zones)
        except ValueError:
            rule = None
    found, produced = [], 0
    for moment in (candidates(start, rule) if rule else [start]):
        if not within(moment, until) or epoch(moment) >= window_end:
            break
        produced += 1
        if epoch(moment) not in excluded and epoch(moment + length) > window_start:
            found.append((moment, moment + length))
        if rule and 'count' in rule and produced >= rule['count']:
            break
    return found


def parse_events(text, calendar_id, calendar_name, now=None):
    """Cached event rows of a calendar between a week ago and 60 days ahead."""
    now = now if now is not None else time.time()
    today = datetime.fromtimestamp(now).date()
    window_start = epoch(today - timedelta(days=PAST_DAYS))
    window_end = epoch(today + timedelta(days=FUTURE_DAYS + 1))
    if not re.search(r'^\W*BEGIN:VCALENDAR\s*$', text, re.M | re.I):
        raise CalendarError(tr('This address did not return an iCal calendar.'))
    name, events, zones = read_components(text)
    overrides = {}
    for properties in events:
        uid, recurrence = first(properties, 'UID'), first(properties, 'RECURRENCE-ID')
        if uid and recurrence:
            try:
                overrides.setdefault(uid[1], set()).add(epoch(parse_moment(*recurrence, zones)))
            except ValueError:
                continue
    rows = []
    for properties in events:
        status = first(properties, 'STATUS')
        uid = (first(properties, 'UID') or ({}, ''))[1]
        is_override = bool(first(properties, 'RECURRENCE-ID'))
        if status and status[1].strip().upper() == 'CANCELLED':
            continue
        summary = unescape((first(properties, 'SUMMARY') or ({}, ''))[1])
        title = ''.join(character for character in summary.replace('\n', ' ') if ord(character) >= 32)[:200] or tr('Busy')
        try:
            pairs = instances(properties, zones, window_start, window_end,
                              frozenset() if is_override else overrides.get(uid, frozenset()))
        except (ValueError, OverflowError):
            continue
        for start, end in pairs:
            key = hashlib.sha256(f'{calendar_id}\0{uid}\0{start.isoformat()}'.encode()).hexdigest()[:24]
            row = {'key': key, 'calendarId': calendar_id, 'calendar': calendar_name, 'title': title}
            if isinstance(start, datetime):
                row.update(start=int(epoch(start)), end=int(epoch(end)))
            else:
                row.update(allDay=True, date=start.isoformat(), endDate=end.isoformat())
            rows.append(row)
    rows.sort(key=lambda row: (row.get('date') or '', row.get('start', 0)))
    return name, rows[:MAX_EVENTS]


# Refresh and alerts ---------------------------------------------------------

def load_cache():
    data = read_json(events_file(), {})
    return data if isinstance(data, dict) and isinstance(data.get('events'), list) else {'events': []}


def refresh(prefetched=None, now=None):
    """Fetch every calendar; a calendar that fails keeps its previous events."""
    now = now if now is not None else time.time()
    previous = load_cache()['events']
    events, failures = [], 0
    for calendar in load_calendars():
        try:
            text = (prefetched or {}).get(calendar['id']) or fetch(calendar['url'], calendar['name'])
            events += parse_events(text, calendar['id'], calendar['name'], now)[1]
        except CalendarError as error:
            failures += 1
            print(str(error), file=sys.stderr)
            events += [event for event in previous if event.get('calendarId') == calendar['id']]
    write_private(events_file(), {'updated': int(now), 'events': events})
    schedule_alerts(events, now)
    return 1 if failures else 0


def load_fired():
    data = read_json(alerts_file(), {})
    return data if isinstance(data, dict) else {}


def unit(key):
    return f'eitr-calendar-{key}'


def schedule_alerts(events, now):
    fired = load_fired()
    for event in events:
        if event.get('allDay') or event['key'] in fired:
            continue
        delay = int(event['start'] - now)
        if 0 < delay <= ALERT_HORIZON:
            # A timer that already exists for this event makes systemd-run fail: that is fine.
            subprocess.run(['systemd-run', '--user', '--quiet', f'--unit={unit(event["key"])}', f'--on-active={delay}s',
                            '--timer-property=AccuracySec=1s', '--timer-property=WakeSystem=false',
                            'python3', str(Path(__file__).resolve()), 'fire', event['key']],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def fire(key, now=None):
    """Alert once for an event still in the calendar; moved or deleted events stay quiet."""
    now = now if now is not None else time.time()
    event = next((item for item in load_cache()['events'] if item.get('key') == key and not item.get('allDay')), None)
    if event is None:
        return 0
    fired = load_fired()
    if key in fired:
        return 0
    fired = {name: start for name, start in fired.items() if isinstance(start, (int, float)) and start > now - 2 * 86400}
    fired[key] = event['start']
    write_private(alerts_file(), fired)
    reminders.notify(event['title'], f"{datetime.fromtimestamp(event['start']):%H:%M} · {event['calendar']}", urgency='critical')
    reminders.chime()
    return 0


def set_timer(enabled):
    subprocess.run(['systemctl', '--user', 'enable' if enabled else 'disable', '--now', TIMER],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Walker flows ---------------------------------------------------------------

def rows():
    calendars = sorted(load_calendars(), key=lambda item: item['name'].casefold())
    return [{'id': item['id'], 'name': item['name'], 'host': host(item['url'])} for item in calendars]


def add():
    try:
        provider = collect(tr('Add Calendar'), [
            Step('provider', tr('Which calendar?'), default='google', options=[
                (tr('Google Calendar'), 'google'), (tr('Outlook'), 'outlook'),
                (tr('Other (any iCal address)'), 'other')]),
        ])['provider']
        instructions = (tr('Google: Settings > your calendar > "Secret address in iCal format".')
                        if provider == 'google' else
                        tr('Outlook: Settings > Calendar > Shared calendars > Publish a calendar > copy the ICS link, not the HTML one.')
                        if provider == 'outlook' else tr('Paste an https:// or webcal:// iCal address.'))
        if provider in PROVIDERS:
            subprocess.Popen(['xdg-open', PROVIDERS[provider]], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        print(instructions, flush=True)
        identifier = str(time.time_ns())
        fetched = {}

        def validate_address(value):
            address = normalize(value)
            if not address:
                raise ValueError(tr('Paste an https:// or webcal:// iCal address.'))
            if any(item['url'] == address for item in load_calendars()):
                raise ValueError(tr('This calendar is already added.'))
            return True

        def suggested_name(values):
            address = normalize(values.get('address'))
            if not address:
                return ''
            if address not in fetched:
                text = fetch(address, tr('New calendar'))
                suggested, events = parse_events(text, identifier, '')
                fetched[address] = (text, suggested, events)
            return (fetched[address][1] or host(address))[:80]

        answers = collect(tr('Add Calendar'), [
            Step('address', tr('Paste the secret iCal address (https://…)'), secret=True,
                 validator=validate_address, description=instructions),
            Step('name', tr('Name'), default=suggested_name),
        ])
        validate_address(answers['address'])
        suggested = suggested_name(answers)
        address = normalize(answers['address'])
        text, _, events = fetched[address]
        name = ''.join(character for character in answers['name'].strip()[:80] if ord(character) >= 32) or suggested
    except (KeyboardInterrupt, EOFError):
        print(tr('Nothing was added.'))
        return 0
    except (CalendarError, ValueError) as error:
        print(f'{tr("Calendar not added")}: {error}', file=sys.stderr)
        reminders.notify(tr('Calendar not added'), str(error))
        return 1
    with locked():
        save_calendars(load_calendars() + [{'id': identifier, 'name': name, 'provider': provider, 'url': address}])
        refresh({identifier: text})
    set_timer(True)
    reminders.notify(tr('Calendar added'), tr('{name}: {count} events from the last week to the next 60 days.',
                                              name=name, count=len(events)))
    return 0


def remove(identifier):
    calendar = next((item for item in load_calendars() if item['id'] == identifier), None)
    if calendar is None:
        return 1
    confirm = tr("Remove '{name}'", name=calendar['name'])
    if reminders.ask(tr('Enter removes the calendar; Esc keeps it'), [confirm]) != confirm:
        return 0
    with locked():
        remaining = [item for item in load_calendars() if item['id'] != identifier]
        save_calendars(remaining)
        cached = load_cache()
        write_private(events_file(), dict(cached, events=[event for event in cached['events']
                                                          if event.get('calendarId') != identifier]))
    if not remaining:
        set_timer(False)
    reminders.notify(tr('Calendar removed'), calendar['name'])
    return 0


def main(argv):
    command, rest = (argv[0], argv[1:]) if argv else ('add', [])
    if command == 'rows' and not rest:
        print(json.dumps(rows()))
        return 0
    if command == 'add' and not rest:
        return add()
    if command == 'remove' and len(rest) == 1:
        return remove(rest[0])
    if command == 'refresh' and not rest:
        with locked():
            return refresh()
    if command == 'fire' and len(rest) == 1:
        with locked():
            return fire(rest[0])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
