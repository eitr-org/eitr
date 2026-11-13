"""Pure time-phrase parsing and recurrence rules for reminders."""
import eitr_bootstrap
from eitr_i18n import tr
from datetime import datetime, timedelta
import calendar
import re

DELAY = re.compile(r"^(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+)\s*s)?$", re.I)
CLOCK = re.compile(r"^(\d{1,2}):(\d{2})$")
WEEKDAYS = [name.lower() for name in calendar.day_name]  # Monday first, like datetime.weekday()
NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "thirty": 30, "forty-five": 45}


def normalize(text):
    """Everyday English phrasing in the parser's own terms: "in 5 minutes" -> "5m",
    "9:30 pm" -> "21:30", "every 29th at 9am" -> "every month on the 29th 09:00"."""
    text = " ".join(text.strip().lower().rstrip(".!").split())
    text = re.sub(r"\bhalf an hour\b", "30m", text)
    text = re.sub(r"\b(" + "|".join(NUMBER_WORDS) + r")\b(?= (?:hours?|hrs?|minutes?|mins?|seconds?|secs?)\b)",
                  lambda match: str(NUMBER_WORDS[match.group(1)]), text)
    for pattern, unit in ((r"hours?|hrs?", "h"), (r"minutes?|mins?", "m"), (r"seconds?|secs?", "s")):
        text = re.sub(rf"\b(\d+) ?(?:{pattern})\b", rf"\1{unit}", text)
    text = re.sub(r"(\d[hms]) and (\d)", r"\1 \2", text)

    def clock(match):
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        if not 1 <= hour <= 12 or minute > 59:
            return match.group(0)
        return f"{hour % 12 + (12 if match.group(3).startswith('p') else 0):02d}:{minute:02d}"
    text = re.sub(r"(?<![\d:])(\d{1,2})(?::(\d{2}))? ?([ap])\.?m\b\.?", clock, text)
    text = re.sub(r"\bnoon\b", "12:00", re.sub(r"\bmidnight\b", "00:00", text))
    text = re.sub(r"^(?:in|at) ", "", text).replace(" at ", " ")
    text = re.sub(r"^every (\d{1,2}(?:st|nd|rd|th))(?= |$)", r"every month on the \1", text)
    return text


def when(text, now=None):
    """The due time (epoch seconds) for a delay or a time of day; None if unreadable."""
    now = now or datetime.now()
    text = normalize(text)
    if text.isdigit():
        return int((now + timedelta(minutes=int(text))).timestamp())
    clock = CLOCK.match(text)
    if clock:
        hour, minute = int(clock.group(1)), int(clock.group(2))
        if hour > 23 or minute > 59:
            return None
        due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due <= now:
            due += timedelta(days=1)
        return int(due.timestamp())
    delay = DELAY.match(text)
    if delay and any(delay.groups()):
        hours, minutes, seconds = (int(value or 0) for value in delay.groups())
        total = hours * 3600 + minutes * 60 + seconds
        return int(now.timestamp()) + total if total > 0 else None
    try:
        parts = text.rsplit(" ", 1)
        clock_text = parts[-1] if CLOCK.fullmatch(parts[-1]) else "09:00"
        day_text = parts[0] if clock_text == parts[-1] else text
        hour, minute = map(int, clock_text.split(":"))
        if day_text in ("today", "tomorrow"):
            day = now + timedelta(days=day_text == "tomorrow")
        elif day_text.startswith("next ") and day_text[5:] in WEEKDAYS:
            # "next friday" is that day of next week (Monday to Sunday after this one).
            next_monday = now + timedelta(days=7 - now.weekday())
            day = next_monday + timedelta(days=WEEKDAYS.index(day_text[5:]))
        elif day_text in WEEKDAYS or (day_text.startswith("this ") and day_text[5:] in WEEKDAYS):
            day_text = day_text.removeprefix("this ")
            weekday = WEEKDAYS.index(day_text)
            day = now + timedelta(days=(weekday - now.weekday()) % 7)
            if day.replace(hour=hour, minute=minute, second=0, microsecond=0) <= now:
                day += timedelta(days=7)
        else:
            day = None
            for pattern in ("%Y-%m-%d", "%b %d", "%B %d"):
                try:
                    day = datetime.strptime(day_text if "%Y" in pattern else f"{now.year} {day_text}",
                                            pattern if "%Y" in pattern else "%Y " + pattern)
                    if "%Y" not in pattern:
                        if day.replace(hour=hour, minute=minute) <= now:
                            day = day.replace(year=now.year + 1)
                    break
                except ValueError:
                    continue
            if day is None:
                return None
        due = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return int(due.timestamp()) if due > now else None
    except (ValueError, OverflowError):
        return None


def repeat_rule(rule):
    """Validate the shared, deliberately small recurrence grammar."""
    if not isinstance(rule, dict) or not {'frequency'} <= rule.keys() or not rule.keys() <= {'frequency', 'interval', 'weekdays', 'day_of_month', 'until', 'count'}:
        raise ValueError(tr('Invalid repeat rule.'))
    frequency = rule['frequency']
    if frequency not in ('daily', 'weekly', 'monthly', 'yearly'):
        raise ValueError(tr('Invalid repeat rule.'))
    for key, maximum in (('interval', 1000), ('count', 100000)):
        if key in rule and (type(rule[key]) is not int or not 1 <= rule[key] <= maximum):
            raise ValueError(tr('Invalid repeat rule.'))
    if 'weekdays' in rule:
        days = rule['weekdays']
        if frequency != 'weekly' or not isinstance(days, list) or not days or any(type(day) is not int or not 0 <= day <= 6 for day in days) or len(set(days)) != len(days):
            raise ValueError(tr('Invalid repeat rule.'))
    if 'day_of_month' in rule and (frequency != 'monthly' or type(rule['day_of_month']) is not int or not 1 <= rule['day_of_month'] <= 31):
        raise ValueError(tr('Invalid repeat rule.'))
    if 'until' in rule:
        if 'count' in rule or not isinstance(rule['until'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', rule['until']):
            raise ValueError(tr('Invalid repeat rule.'))
        datetime.strptime(rule['until'], '%Y-%m-%d')
    return dict(rule)


def occurrence(anchor, rule, index):
    """Local calendar arithmetic preserves the original clock across DST."""
    step = rule.get('interval', 1)
    frequency = rule['frequency']
    if frequency == 'daily':
        return anchor + timedelta(days=index * step)
    if frequency == 'weekly':
        days = sorted(rule.get('weekdays', [anchor.weekday()]))
        first = [day for day in days if day > anchor.weekday()]
        if index == 0:
            return anchor
        if index <= len(first):
            return anchor + timedelta(days=first[index - 1] - anchor.weekday())
        cycle, offset = divmod(index - len(first) - 1, len(days))
        return anchor + timedelta(days=(cycle + 1) * step * 7 + days[offset] - anchor.weekday())
    months = index * step * (12 if frequency == 'yearly' else 1)
    year, month = divmod(anchor.year * 12 + anchor.month - 1 + months, 12)
    day = rule.get('day_of_month', anchor.day)
    return anchor.replace(year=year, month=month + 1, day=min(day, calendar.monthrange(year, month + 1)[1]))


def advance(reminder, after):
    rule = reminder.get('repeat')
    if not rule:
        return False
    anchor = datetime.fromisoformat(reminder['repeat_anchor'])
    index = reminder.get('repeat_index', 0) + 1
    while 'count' not in rule or index < rule['count']:
        try:
            candidate = occurrence(anchor, rule, index)
        except (OverflowError, ValueError):
            return False
        if 'until' in rule and candidate.date().isoformat() > rule['until']:
            return False
        due = int(candidate.timestamp())
        if due > after:
            reminder.update(due=due, repeat_index=index,
                            alerts=[due - offset for offset in reminder['alert_offsets'] if due - offset > after])
            return True
        index += 1
    return False


def repeat_label(reminder):
    if not reminder.get('repeat'):
        return ''
    rule = reminder['repeat']
    names = {'daily': tr('Daily'), 'weekly': tr('Weekly'), 'monthly': tr('Monthly'), 'yearly': tr('Yearly')}
    interval = rule.get('interval', 1)
    detail = names[rule['frequency']] if interval == 1 else names[rule['frequency']] + ' × ' + str(interval)
    if 'weekdays' in rule:
        days = [tr('Monday'), tr('Tuesday'), tr('Wednesday'), tr('Thursday'), tr('Friday'), tr('Saturday'), tr('Sunday')]
        chosen = ', '.join(days[day] for day in sorted(rule['weekdays']))
        # The chosen days already say it repeats weekly.
        detail = chosen if interval == 1 else detail + ' · ' + chosen
    if 'day_of_month' in rule:
        detail += ' · ' + str(rule['day_of_month'])
    if 'until' in rule:
        detail += ' · ' + tr('Until {date}', date=rule['until'])
    if 'count' in rule:
        detail += ' · ' + tr('{count} occurrences', count=rule['count'])
    return ' ↻ ' + detail


def parse_when(text, now=None):
    now = now or datetime.now()
    text = normalize(text)
    match = re.fullmatch(r'(every day|weekdays|every week|every month on the (\d{1,2})(?:st|nd|rd|th)?|every year|every (.+?))(?: (\d{1,2}:\d{2}))?', text.strip().lower())
    if not match:
        return when(text, now), None
    phrase, month_day, names, clock = match.groups()
    rule = {'frequency': 'daily'}
    if phrase == 'weekdays':
        rule = {'frequency': 'weekly', 'weekdays': [0, 1, 2, 3, 4]}
    elif month_day:
        rule = {'frequency': 'monthly', 'day_of_month': int(month_day)}
    elif phrase == 'every week':
        rule = {'frequency': 'weekly'}
    elif phrase == 'every year':
        rule = {'frequency': 'yearly'}
    elif names:
        values = re.split(r'\s*(?:,| and )\s*', names)
        if any(value not in WEEKDAYS for value in values):
            return None, None
        rule = {'frequency': 'weekly', 'weekdays': [WEEKDAYS.index(value) for value in values]}
    repeat_rule(rule)
    hour, minute = map(int, (clock or '09:00').split(':'))
    try:
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError:
        return None, None
    for offset in range(367):
        day = candidate + timedelta(days=offset)
        if day <= now:
            continue
        if 'weekdays' in rule and day.weekday() not in rule['weekdays']:
            continue
        if month_day and day.day != min(int(month_day), calendar.monthrange(day.year, day.month)[1]):
            continue
        return int(day.timestamp()), rule
    return None, None


def label(due):
    moment = datetime.fromtimestamp(due)
    today = datetime.now().date()
    day = "today" if moment.date() == today else "tomorrow" if moment.date() == today + timedelta(days=1) \
        else moment.strftime("%a %d %b")
    return f"{moment:%H:%M} {day}"


def has_time(phrase):
    """True when the phrase says when in the day (18:30) or is relative (10m, 90);
    a date alone ("every month on the 29th", "friday") needs a time first."""
    text = normalize(phrase)
    return bool(CLOCK.search(text.split()[-1]) if text.split() else False) or text.isdigit() or bool(
        DELAY.match(text) and any(DELAY.match(text).groups()))
