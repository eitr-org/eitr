"""Alarm state transitions for the shared reminder scheduler."""
from datetime import datetime, timedelta
import os
import re

from eitr_choice_lists import ALARM_SOUNDS, ids

RING_SECONDS = 600


def configure(payload, identifier, now, invalid):
    clock = payload.get("clock")
    days = payload.get("days")
    name = payload.get("name")
    sound = payload.get("sound")
    enabled = payload.get("enabled")
    if (not isinstance(clock, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", clock)
            or not isinstance(days, list) or any(type(day) is not int or not 0 <= day <= 6 for day in days)
            or not isinstance(name, str) or not name.strip() or len(name) > 240
            or any(ord(character) < 32 for character in name)
            or not isinstance(sound, str) or not sound or "\0" in sound
            or (sound not in ids(ALARM_SOUNDS)
                and not os.path.isabs(sound))
            or type(enabled) is not bool):
        raise ValueError(invalid)
    hour, minute = map(int, clock.split(":"))
    local = datetime.fromtimestamp(now)
    for offset in range(8):
        candidate = (local + timedelta(days=offset)).replace(hour=hour, minute=minute, second=0, microsecond=0, fold=0)
        due = int(candidate.timestamp())
        if due > now and (not days or candidate.weekday() in days):
            break
    alarm = {"clock": clock, "days": sorted(set(days)), "sound": sound, "enabled": enabled}
    item = {"id": identifier, "text": name.strip(), "due": due, "alarm": alarm,
            "alerts": [due] if enabled else []}
    if days:
        item.update(repeat={"frequency": "weekly", "weekdays": alarm["days"]},
                    repeat_anchor=candidate.isoformat(), repeat_index=0, alert_offsets=[0])
    return item


def moments(item):
    alarm = item["alarm"]
    return sorted(set(item["alerts"]) | {alarm[key] for key in ("snooze", "ringUntil") if key in alarm})


def transition(item, moment, now, advance, missed=False):
    alarm = item["alarm"]
    expired = alarm.get("ringUntil") == moment
    if expired:
        alarm.pop("ringUntil")
        alarm.pop("ringTime", None)
    due = moment in item["alerts"]
    snoozed = alarm.get("snooze") == moment
    if snoozed:
        alarm.pop("snooze")
        clock = alarm.pop("snoozeTime", alarm["clock"])
    else:
        clock = alarm["clock"]
    if due and not advance(item, now):
        item["alerts"] = []
        alarm["enabled"] = False
    if not (due or snoozed):
        return "missed" if expired else ""
    if missed or now >= moment + RING_SECONDS:
        return "missed"
    alarm.update(ringTime=clock, ringUntil=now + RING_SECONDS)
    return "ring"


def dismiss(item, snooze, now):
    alarm = item["alarm"]
    if "ringUntil" not in alarm or alarm["ringUntil"] <= now:
        return False
    if snooze:
        alarm.update(snooze=now + RING_SECONDS, snoozeTime=alarm["ringTime"])
    alarm.pop("ringUntil")
    alarm.pop("ringTime")
    return True
