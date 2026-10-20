#!/usr/bin/env python3
"""Reminders: a notification at a time you choose.

  reminders.py new [WHEN [TEXT...]]   ask with Walker for what is missing
  reminders.py list                   upcoming reminders
  reminders.py manage                 pick one in Walker to cancel it
  reminders.py cancel ID
  reminders.py restore                at login: reschedule, and show missed ones
  reminders.py fire ID                (the timer runs this)

WHEN is a delay (10m, 1h30m, 45s, or a number of minutes) or a time of day
(18:30, tomorrow when that has passed). Reminders are kept in
~/.local/state/eitr/reminders.json and timed by transient systemd user timers,
so one that came due while the computer was off is shown at the next login.
"""
import eitr_bootstrap
from eitr_i18n import tr
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

DELAY = re.compile(r"^(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+)\s*s)?$", re.I)
CLOCK = re.compile(r"^(\d{1,2}):(\d{2})$")


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
    return None


def label(due):
    moment = datetime.fromtimestamp(due)
    today = datetime.now().date()
    day = "today" if moment.date() == today else "tomorrow" if moment.date() == today + timedelta(days=1) \
        else moment.strftime("%a %d %b")
    return f"{moment:%H:%M} {day}"


def unit(identifier):
    return f"eitr-reminder-{identifier}"


def schedule(reminder):
    delay = max(1, reminder["due"] - int(time.time()))
    subprocess.run(["systemd-run", "--user", "--quiet", f"--unit={unit(reminder['id'])}", f"--on-active={delay}s",
                    "--timer-property=AccuracySec=1s", "python3", str(Path(__file__).resolve()), "fire",
                    reminder["id"]], check=True)


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
    reminder = {"id": str(time.time_ns()), "due": due, "text": text}
    schedule(reminder)
    save(load() + [reminder])
    notify(tr('Reminder set'), f"{label(due)}: {text}")
    print(tr('Reminder set for {label}: {text}', label=f'{label(due)}', text=f'{text}'))
    return 0


def fire(identifier, missed=False):
    reminders = load()
    reminder = next((item for item in reminders if item["id"] == identifier), None)
    if reminder is None:
        return 0
    save([item for item in reminders if item["id"] != identifier])
    title = "Reminder (while the computer was off)" if missed else "Reminder"
    notify(title, reminder["text"], urgency="critical")
    return 0


def cancel(identifier):
    reminders = load()
    if not any(item["id"] == identifier for item in reminders):
        print(tr('No such reminder.'), file=sys.stderr)
        return 1
    subprocess.run(["systemctl", "--user", "stop", f"{unit(identifier)}.timer"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    save([item for item in reminders if item["id"] != identifier])
    return 0


def restore():
    now = int(time.time())
    for reminder in load():
        if reminder["due"] <= now:
            fire(reminder["id"], missed=True)
        elif subprocess.run(["systemctl", "--user", "is-active", "--quiet", f"{unit(reminder['id'])}.timer"]).returncode:
            schedule(reminder)
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
        cancel(reminder["id"])
        notify(tr('Reminder cancelled'), reminder["text"])
    return 0


def main(argv):
    command, rest = (argv[0], argv[1:]) if argv else ("new", [])
    if command == "new":
        return new(rest)
    if command == "list":
        return listing()
    if command == "manage":
        return manage()
    if command == "restore":
        return restore()
    if command in ("fire", "cancel") and len(rest) == 1:
        return fire(rest[0]) if command == "fire" else cancel(rest[0])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
