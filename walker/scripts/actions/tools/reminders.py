#!/usr/bin/env python3
"""Reminders: a notification at a time you choose.

  reminders.py new [WHEN [TEXT...]]   ask with Walker for what is missing
  reminders.py list                   upcoming reminders
  reminders.py manage                 pick one in Walker to cancel it
  reminders.py cancel ID [occurrence|series]
  reminders.py restore                at login: reschedule, and show missed ones
  reminders.py fire ID                (the timer runs this)

WHEN is a delay (10m, 1h30m, 45s, or a number of minutes), a time of day
(18:30, tomorrow when that has passed), or a date such as "tomorrow 15:00",
"Friday" (or "this friday"), "next friday" (next week), "2026-10-30 09:00" or "Oct 30 15:00"; a date without a clock asks for the time.
Repeats: "every day 08:00", "every Monday 09:30", "weekdays 07:00",
"every month on the 15th", "every week", "every year".
Machine commands: list --json; add-json reads {title,event,alerts,repeat?} from stdin.
Optional appointment:true defaults to event minus lead seconds (3600) and event. Reminders are kept in
~/.local/state/eitr/reminders.json and timed by transient systemd user timers,
so one that came due while the computer was off is shown at the next login.
"""
import eitr_bootstrap
from eitr_i18n import tr
from datetime import datetime, timedelta
import calendar
import json
import fcntl
from contextlib import contextmanager
import os
from pathlib import Path
import re
import subprocess
import sys
import time

DELAY = re.compile(r"^(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+)\s*s)?$", re.I)
CLOCK = re.compile(r"^(\d{1,2}):(\d{2})$")
WEEKDAYS = [name.lower() for name in calendar.day_name]  # Monday first, like datetime.weekday()


def state_file():
    base = os.environ.get("XDG_STATE_HOME", "")
    return (Path(base) if base.startswith("/") else Path.home() / ".local/state") / "eitr/reminders.json"


def load():
    try:
        data = json.loads(state_file().read_text())
        return [item for item in data if isinstance(item, dict) and {"id", "due", "text"} <= item.keys()]
    except (OSError, ValueError):
        return []


def save(reminders):
    path = state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(sorted(reminders, key=lambda item: item["due"]), indent=2) + "\n")
    temporary.replace(path)


def when(text, now=None):
    """The due time (epoch seconds) for a delay or a time of day; None if unreadable."""
    now = now or datetime.now()
    text = text.strip().lower()
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


@contextmanager
def locked():
    path = state_file().with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield


def alerts(reminder):
    return reminder.get("alerts", [reminder["due"]])


def create(title, event, alert_times=None, appointment=False, lead=3600, repeat=None):
    times = sorted(set(alert_times if alert_times is not None else
                       ([event - lead, event] if appointment else [event])))
    now = time.time()
    if not isinstance(title, str) or not title.strip() or len(title) > 240 or any(ord(character) < 32 for character in title) or event <= now:
        raise ValueError(tr('Invalid reminder.'))
    if not times or len(times) > 8 or any(moment <= now or moment > event for moment in times) or event not in times:
        raise ValueError(tr('Invalid reminder alerts.'))
    reminder = {"id": str(time.time_ns()), "due": event, "text": title, "alerts": times}
    if repeat is not None:
        rule = repeat_rule(repeat)
        anchor = datetime.fromtimestamp(event)
        if ('until' in rule and anchor.date().isoformat() > rule['until']) or ('weekdays' in rule and anchor.weekday() not in rule['weekdays']) or ('day_of_month' in rule and anchor.day != min(rule['day_of_month'], calendar.monthrange(anchor.year, anchor.month)[1])):
            raise ValueError(tr('Invalid repeat rule.'))
        reminder.update(repeat=rule, repeat_anchor=anchor.isoformat(), repeat_index=0,
                        alert_offsets=[event - moment for moment in times])
    try:
        schedule(reminder)
        save(load() + [reminder])
    except (OSError, subprocess.CalledProcessError):
        stop_timers(reminder)
        raise
    return reminder


def label(due):
    moment = datetime.fromtimestamp(due)
    today = datetime.now().date()
    day = "today" if moment.date() == today else "tomorrow" if moment.date() == today + timedelta(days=1) \
        else moment.strftime("%a %d %b")
    return f"{moment:%H:%M} {day}"


def unit(identifier):
    return f"eitr-reminder-{identifier}"


def alert_unit(reminder, moment):
    return unit(reminder["id"]) if "alerts" not in reminder else unit(reminder["id"]) + "-" + str(moment)


def schedule(reminder):
    for moment in alerts(reminder):
        schedule_alert(reminder, moment)


def schedule_alert(reminder, moment):
    delay = max(1, moment - int(time.time()))
    subprocess.run(["systemd-run", "--user", "--quiet", f"--unit={alert_unit(reminder, moment)}", f"--on-active={delay}s",
                    "--timer-property=AccuracySec=1s", "--timer-property=WakeSystem=false",
                    "python3", str(Path(__file__).resolve()), "fire", reminder["id"], str(moment)], check=True)


def stop_timers(reminder):
    names = [f"{alert_unit(reminder, moment)}.timer" for moment in alerts(reminder)]
    subprocess.run(["systemctl", "--user", "stop", *names], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


ALERT_SOUND = Path("/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga")


def chime():
    """Reminder alerts (only they) play a short sound, unless Do Not Disturb is on."""
    try:
        status = subprocess.run(["eitr-shell", "desktop-bar", "ipc", "call", "notifications", "status"],
                                capture_output=True, text=True, timeout=3).stdout
        if json.loads(status or "{}").get("doNotDisturb") or not ALERT_SOUND.is_file():
            return
        subprocess.Popen(["pw-play", "--volume=0.7", str(ALERT_SOUND)], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass


def notify(title, body, urgency="normal"):
    root = os.environ.get("EITR_CODE_ROOT", "/usr/share/eitr")
    subprocess.run(["notify-send", "--app-name=Reminders", f"--urgency={urgency}",
                    f"--icon={root}/fastfetch/assets/eitr-logo.png", title, body], check=False)


def has_time(phrase):
    """True when the phrase says when in the day (18:30) or is relative (10m, 90);
    a date alone ("every month on the 29th", "friday") needs a time first."""
    text = phrase.strip().lower()
    return bool(CLOCK.search(text.split()[-1]) if text.split() else False) or text.isdigit() or bool(
        DELAY.match(text) and any(DELAY.match(text).groups()))


def with_time(phrase):
    """The phrase, with a time asked for when it is a date without one; None when dismissed.
    Anything else is returned as it is, for the parser to accept or refuse."""
    try:
        needs_time = not has_time(phrase) and parse_when(f"{phrase} 09:00")[0] is not None
    except ValueError:
        needs_time = False
    if not needs_time:
        return phrase
    clock = ask(tr('At what time? (for example 09:00)'))
    return f"{phrase} {clock.strip()}" if clock and CLOCK.fullmatch(clock.strip()) else None


def ask(placeholder, choices=None):
    """One line from Walker; None when dismissed."""
    walker = Path(os.environ.get("EITR_CODE_ROOT", "/usr/share/eitr")) / "walker/bin/walker"
    command = [str(walker), "--dmenu", "--placeholder", placeholder] + ([] if choices else ["--inputonly"])
    result = subprocess.run(command, input="\n".join(choices or []), capture_output=True, text=True)
    answer = result.stdout.strip()
    return answer or None


def new(arguments):
    spoken = arguments[0] if arguments else ask(tr('When? (10m, 18:30, every day 08:00)'))
    if not spoken:
        return 1
    spoken = with_time(spoken)
    if not spoken:
        return 1
    try:
        due, rule = parse_when(spoken)
    except ValueError:
        due, rule = None, None
    if due is None:
        notify(tr('Reminder not set'), tr("'{spoken}' is not a time: try 10m, 1h30m or 18:30.", spoken=f'{spoken}'))
        return 1
    text = " ".join(arguments[1:]) or ask(tr('Remind me about…'))
    if not text:
        return 1
    with locked():
        reminder = create(text, due, repeat=rule)
    repeats = repeat_label(reminder)
    notify(tr('Reminder set'), f"{label(due)}{repeats}: {text}")
    print(tr('Reminder set for {label}: {text}', label=f'{label(due)}{repeats}', text=f'{text}'))
    return 0


def fire(identifier, missed=False, moment=None):
    reminders = load()
    reminder = next((item for item in reminders if item["id"] == identifier), None)
    if reminder is None:
        return 0
    pending = alerts(reminder)
    moment = pending[0] if moment is None else moment
    if moment not in pending:
        return 0
    remaining = [value for value in pending if value != moment
                 and not (missed and reminder.get('repeat') and value <= time.time())]
    if reminder.get('repeat') and (moment == reminder['due'] or missed and reminder['due'] <= time.time()):
        stop_timers(reminder)
        if advance(reminder, int(time.time())):
            save(reminders)
            schedule(reminder)
        else:
            reminders.remove(reminder)
        save(reminders)
        notify(tr('Reminder (while the computer was off)') if missed else tr('Reminder'), reminder['text'], urgency='critical')
        chime()
        return 0
    if remaining:
        reminder["alerts"] = remaining
    else:
        reminders.remove(reminder)
    save(reminders)
    title = tr('Reminder (while the computer was off)') if missed else tr('Reminder')
    notify(title, reminder["text"], urgency="critical")
    chime()
    return 0


def cancel(identifier, scope=None):
    reminders = load()
    reminder = next((item for item in reminders if item["id"] == identifier), None)
    if reminder is None:
        print(tr('No such reminder.'), file=sys.stderr)
        return 1
    if scope is None:
        if reminder.get('repeat'):
            print(tr('Choose occurrence or series.'), file=sys.stderr)
            return 1
        scope = 'series'
    if scope not in ('occurrence', 'series'):
        raise ValueError(tr('Invalid cancellation scope.'))
    stop_timers(reminder)
    if scope == 'occurrence' and advance(reminder, max(int(time.time()), reminder['due'])):
        save(reminders)
        schedule(reminder)
    else:
        save([item for item in reminders if item["id"] != identifier])
    return 0


def restore():
    now = int(time.time())
    for reminder in load():
        if reminder.get('repeat') and reminder['due'] <= now:
            fire(reminder['id'], missed=True, moment=alerts(reminder)[0])
            continue
        pending = alerts(reminder)
        if reminder.get('repeat') and any(moment <= now for moment in pending):
            fire(reminder['id'], missed=True, moment=next(moment for moment in pending if moment <= now))
            pending = [moment for moment in pending if moment > now]
        for moment in pending:
            if moment <= now:
                fire(reminder["id"], missed=True, moment=moment)
            elif subprocess.run(["systemctl", "--user", "is-active", "--quiet",
                                 f"{alert_unit(reminder, moment)}.timer"]).returncode:
                schedule_alert(reminder, moment)
    return 0


def listing():
    reminders = load()
    if not reminders:
        print(tr('No reminders.'))
    for reminder in reminders:
        print(tr('{label}  {text}  (id {id})', label=f"{label(reminder['due'])}", text=f"{reminder['text']}{repeat_label(reminder)}", id=f"{reminder['id']}"))
    return 0


def manage():
    reminders = load()
    if not reminders:
        notify(tr('Reminders'), tr('No reminders are waiting.'))
        return 0
    rows = [f"{label(item['due'])}  ·  {item['text']}{repeat_label(item)}" for item in reminders]
    picked = ask(tr('Pick a reminder to cancel'), rows)
    if picked not in rows:
        return 0
    reminder = reminders[rows.index(picked)]
    choices = [tr('Keep it'), tr('This occurrence'), tr('All future occurrences')] if reminder.get('repeat') else [tr('Keep it'), tr('Cancel the reminder')]
    choice = ask(tr("Cancel '{text}'?", text=reminder['text']), choices)
    if choice in choices[1:]:
        with locked():
            cancel(reminder['id'], 'occurrence' if choice == tr('This occurrence') else 'series')
        notify(tr('Reminder cancelled'), reminder['text'])
    return 0


def main(argv):
    command, rest = (argv[0], argv[1:]) if argv else ("new", [])
    if command == "new":
        return new(rest)
    if command == "list":
        if rest == ["--json"]:
            print(json.dumps(load()))
            return 0
        return listing()
    if command == "manage":
        return manage()
    if command == "restore":
        return restore()
    if command == "add-json" and not rest:
        try:
            payload = json.load(sys.stdin)
            if (not isinstance(payload, dict) or not {"title", "event"} <= payload.keys()
                    or not payload.keys() <= {"title", "event", "alerts", "appointment", "lead", "repeat"}
                    or type(payload.get("appointment", False)) is not bool
                    or type(payload.get("lead", 3600)) is not int or not 0 < payload.get("lead", 3600) <= 31536000):
                raise ValueError(tr('Invalid reminder.'))
            def absolute(value):
                if not isinstance(value, str):
                    raise ValueError(tr('Invalid reminder time.'))
                moment = datetime.fromisoformat(value)
                if moment.tzinfo is None:
                    raise ValueError(tr('Invalid reminder time.'))
                return int(moment.timestamp())
            event = absolute(payload["event"])
            values = payload.get("alerts")
            if "alerts" in payload and not isinstance(values, list):
                raise ValueError(tr('Invalid reminder alerts.'))
            times = [absolute(value) for value in values] if values is not None else None
            print(json.dumps(create(payload["title"], event, times, payload.get("appointment", False), payload.get("lead", 3600), payload.get("repeat"))))
            return 0
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            print(str(error), file=sys.stderr)
            return 1
    if command == 'cancel' and len(rest) == 2:
        try:
            return cancel(rest[0], rest[1])
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
    if command == "fire" and len(rest) == 2:
        return fire(rest[0], moment=int(rest[1]))
    if command in ("fire", "cancel") and len(rest) == 1:
        return fire(rest[0]) if command == "fire" else cancel(rest[0])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] in ("new", "manage"):
        sys.exit(main(sys.argv[1:]))
    with locked():
        sys.exit(main(sys.argv[1:]))
