"""iCalendar parser for subscribed calendar feeds.

The reader covers VEVENT start, end or duration, summary and UID; UTC, TZID
(IANA names, common Windows names, else the VTIMEZONE standard offset) and floating
times; all-day events; EXDATE; RECURRENCE-ID overrides; and RRULE with FREQ
DAILY, WEEKLY (BYDAY), MONTHLY (one BYMONTHDAY or one BYDAY such as 1MO or -1FR) or
YEARLY, plus INTERVAL, COUNT and UNTIL. Rules with other parts (BYSETPOS,
BYWEEKNO, BYYEARDAY, BYHOUR, several month days...) show only their first event.
"""
import eitr_bootstrap
from eitr_i18n import tr
from datetime import date, datetime, time as clock, timedelta, timezone
import hashlib
import re
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import reminder_rules

PAST_DAYS = 7
FUTURE_DAYS = 60
MAX_EVENTS = 2000
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
DURATION = re.compile(r'([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?')


class CalendarError(Exception):
    """A message that is safe to show: it never contains the address."""


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
        moment = reminder_rules.occurrence(start, rule, index)
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
