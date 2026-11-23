"""Persist alarm actions through the reminder store and its systemd timers."""
import json
import subprocess
import sys
import time

from eitr_i18n import tr
from alarm_rules import configure, dismiss, moments, transition
from reminder_rules import advance


def replace(items, previous, updated, consumed, schedule_alert, stop_timers, save):
    old = set(moments(previous)) if previous else set()
    new = set(moments(updated)) if updated else set()
    started = []
    try:
        for moment in sorted(new - (old - {consumed})):
            schedule_alert(updated, moment)
            started.append(moment)
        save([item for item in items if item is not previous] + ([updated] if updated else []))
    except (OSError, subprocess.SubprocessError):
        if started:
            stop_timers(updated, started)
        raise
    obsolete = old - new - {consumed}
    if obsolete:
        stop_timers(previous, sorted(obsolete))


def command(operation, arguments, items, replace_alarm):
    try:
        identifier = arguments[0] if arguments else str(time.time_ns())
        previous = next((item for item in items if item["id"] == identifier and "alarm" in item), None)
        if arguments and previous is None:
            return 0 if operation in ("alarm-stop", "alarm-snooze") else 1
        now = int(time.time())
        if operation == "alarm-save":
            payload = json.load(sys.stdin)
            if not isinstance(payload, dict):
                raise ValueError(tr("Invalid alarm."))
            updated = configure(payload, identifier, now, tr("Invalid alarm."))
        elif operation == "alarm-delete":
            updated = None
        else:
            updated = json.loads(json.dumps(previous))
            if not dismiss(updated, operation == "alarm-snooze", now):
                return 0
        replace_alarm(items, previous, updated)
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        return 1


def fire(items, previous, moment, missed, replace_alarm, notify):
    updated = json.loads(json.dumps(previous))
    outcome = transition(updated, moment, int(time.time()), advance, missed)
    replace_alarm(items, previous, updated, consumed=moment)
    if outcome == "missed":
        notify(tr("Missed alarm"), updated["text"], suppress_sound=True)
    elif outcome == "ring":
        notify(tr("Alarm"), updated["text"], suppress_sound=True)
    return 0
