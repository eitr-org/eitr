#!/usr/bin/env python3
"""Reminders: a notification at a time you choose.

  reminders.py new [WHEN [TEXT...]]   ask with Walker for what is missing
  reminders.py list                   upcoming reminders
  reminders.py manage                 pick one in Walker to cancel it
  reminders.py cancel ID
  reminders.py restore                at login: reschedule, and show missed ones
  reminders.py fire ID                (the timer runs this)

WHEN is a delay (10m, 1h30m, 45s, or a number of minutes), a time of day
(18:30, tomorrow when that has passed), or a date such as "tomorrow 15:00",
"Friday", "2026-10-30 09:00" or "Oct 30 15:00" (09:00 without a clock).
Machine commands: list --json; add-json reads {title,event,alerts} from stdin.
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
        elif day_text in WEEKDAYS:
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


@contextmanager
def locked():
    path = state_file().with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield


def alerts(reminder):
    return reminder.get("alerts", [reminder["due"]])


def create(title, event, alert_times=None, appointment=False, lead=3600):
    times = sorted(set(alert_times if alert_times is not None else
                       ([event - lead, event] if appointment else [event])))
    now = time.time()
    if not isinstance(title, str) or not title.strip() or len(title) > 240 or any(ord(character) < 32 for character in title) or event <= now:
        raise ValueError(tr('Invalid reminder.'))
    if not times or len(times) > 8 or any(moment <= now or moment > event for moment in times) or event not in times:
        raise ValueError(tr('Invalid reminder alerts.'))
    reminder = {"id": str(time.time_ns()), "due": event, "text": title, "alerts": times}
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


def notify(title, body, urgency="normal"):
    root = os.environ.get("EITR_CODE_ROOT", "/usr/share/eitr")
    subprocess.run(["notify-send", "--app-name=Reminders", f"--urgency={urgency}",
                    f"--icon={root}/fastfetch/assets/eitr-logo.png", title, body], check=False)


def ask(placeholder, choices=None):
    """One line from Walker; None when dismissed."""
    walker = Path(os.environ.get("EITR_CODE_ROOT", "/usr/share/eitr")) / "walker/bin/walker"
    command = [str(walker), "--dmenu", "--placeholder", placeholder] + ([] if choices else ["--inputonly"])
    result = subprocess.run(command, input="\n".join(choices or []), capture_output=True, text=True)
    answer = result.stdout.strip()
    return answer or None


def new(arguments):
    spoken = arguments[0] if arguments else ask(tr('Remind me in or at… (10m, 1h30m, 18:30)'))
    if not spoken:
        return 1
    due = when(spoken)
    if due is None:
        notify(tr('Reminder not set'), tr("'{spoken}' is not a time: try 10m, 1h30m or 18:30.", spoken=f'{spoken}'))
        return 1
    text = " ".join(arguments[1:]) or ask(tr('Remind me about…'))
    if not text:
        return 1
    with locked():
        create(text, due)
    notify(tr('Reminder set'), f"{label(due)}: {text}")
    print(tr('Reminder set for {label}: {text}', label=f'{label(due)}', text=f'{text}'))
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
    remaining = [value for value in pending if value != moment]
    if remaining:
        reminder["alerts"] = remaining
    else:
        reminders.remove(reminder)
    save(reminders)
    title = tr('Reminder (while the computer was off)') if missed else tr('Reminder')
    notify(title, reminder["text"], urgency="critical")
    return 0


def cancel(identifier):
    reminders = load()
    reminder = next((item for item in reminders if item["id"] == identifier), None)
    if reminder is None:
        print(tr('No such reminder.'), file=sys.stderr)
        return 1
    stop_timers(reminder)
    save([item for item in reminders if item["id"] != identifier])
    return 0


def restore():
    now = int(time.time())
    for reminder in load():
        for moment in alerts(reminder):
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
        print(tr('{label}  {text}  (id {id})', label=f"{label(reminder['due'])}", text=f"{reminder['text']}", id=f"{reminder['id']}"))
    return 0


def manage():
    reminders = load()
    if not reminders:
        notify(tr('Reminders'), tr('No reminders are waiting.'))
        return 0
    rows = [f"{label(item['due'])}  ·  {item['text']}" for item in reminders]
    picked = ask(tr('Pick a reminder to cancel'), rows)
    if picked not in rows:
        return 0
    reminder = reminders[rows.index(picked)]
    if ask(tr("Cancel '{text}'?", text=f"{reminder['text']}"), ["Keep it", "Cancel the reminder"]) == "Cancel the reminder":
        with locked():
            cancel(reminder["id"])
        notify(tr('Reminder cancelled'), reminder["text"])
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
                    or not payload.keys() <= {"title", "event", "alerts", "appointment", "lead"}
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
            print(json.dumps(create(payload["title"], event, times, payload.get("appointment", False), payload.get("lead", 3600))))
            return 0
        except (ValueError, OSError, subprocess.SubprocessError) as error:
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
