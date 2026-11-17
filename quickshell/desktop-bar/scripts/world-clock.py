#!/usr/bin/env python3
"""Read-only resolver for cities saved by the official world-clock plugin."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def default_config_path() -> Path:
    configured = os.environ.get("XDG_CONFIG_HOME", "")
    root = Path(configured) if configured.startswith("/") else Path.home() / ".config"
    return root / "eitr/plugins/world-clock.json"


def country_flag(code: str) -> str:
    cleaned = str(code or "").strip().upper()
    if len(cleaned) == 2 and cleaned.isascii() and cleaned.isalpha():
        return chr(0x1F1E6 + ord(cleaned[0]) - 0x41) + chr(0x1F1E6 + ord(cleaned[1]) - 0x41)
    return ""


def parse_now(raw_now: str | None, local_zone: str | None) -> datetime:
    tz = ZoneInfo(local_zone) if local_zone else None
    if raw_now:
        try:
            dt = datetime.fromtimestamp(float(raw_now), tz=tz)
        except ValueError:
            parsed = datetime.fromisoformat(raw_now)
            dt = parsed if parsed.tzinfo else parsed.replace(tzinfo=tz)
            if tz:
                dt = dt.astimezone(tz)
        return dt if tz or dt.tzinfo else dt.astimezone()
    return datetime.now(tz) if tz else datetime.now().astimezone()


def format_time_12(dt: datetime) -> str:
    hour = dt.hour % 12 or 12
    meridiem = "AM" if dt.hour < 12 else "PM"
    return f"{hour}:{dt.minute:02d} {meridiem}"


# How far ahead to look for a daylight-saving change; the page asks again by then anyway.
LOOKAHEAD = timedelta(days=8)


def offsets(moment: datetime, zone: ZoneInfo) -> tuple:
    """The city's and the local UTC offsets at one moment."""
    return (moment.astimezone(zone).utcoffset(), moment.astimezone().utcoffset())


def next_change(now_dt: datetime, zone: ZoneInfo) -> datetime:
    """When the city's or the local UTC offset next changes, to the minute, within LOOKAHEAD;
    the page computes times from the offsets until then and only asks again afterwards."""
    start = offsets(now_dt, zone)
    step = timedelta(hours=1)
    previous = now_dt
    moment = now_dt + step
    while moment - now_dt <= LOOKAHEAD:
        if offsets(moment, zone) != start:
            low, high = previous, moment
            while high - low > timedelta(minutes=1):
                middle = low + (high - low) / 2
                if offsets(middle, zone) == start:
                    low = middle
                else:
                    high = middle
            return high
        previous, moment = moment, moment + step
    return now_dt + LOOKAHEAD


def resolve_cities(config_path: Path, now_dt: datetime) -> dict:
    if not config_path.is_file():
        return {"cities": [], "error": ""}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"cities": [], "error": str(error)}

    raw_cities = payload.get("cities") if isinstance(payload, dict) else []
    if not isinstance(raw_cities, list):
        return {"cities": [], "error": ""}

    local_offset = now_dt.utcoffset()
    cities = []
    for entry in raw_cities:
        if not isinstance(entry, dict):
            continue
        zone_name = str(entry.get("zone") or "").strip()
        if not zone_name:
            continue
        try:
            zone = ZoneInfo(zone_name)
        except ZoneInfoNotFoundError:
            continue
        city_dt = now_dt.astimezone(zone)
        city_offset = city_dt.utcoffset()
        diff_minutes = 0
        if city_offset is not None and local_offset is not None:
            diff_minutes = round((city_offset - local_offset).total_seconds() / 60)
        name = str(entry.get("name") or "").strip() or zone_name.split("/")[-1].replace("_", " ")
        label = str(entry.get("label") or "").strip()
        country = str(entry.get("country") or "").strip().upper()
        cities.append({
            "zone": zone_name,
            "label": label,
            "name": name,
            "country": country,
            "flag": country_flag(country),
            "time24": city_dt.strftime("%H:%M"),
            "time12": format_time_12(city_dt),
            "dayDelta": (city_dt.date() - now_dt.date()).days,
            "offsetMinutes": diff_minutes,
            "utcOffsetMinutes": round(city_offset.total_seconds() / 60) if city_offset is not None else 0,
            "validUntil": int(next_change(now_dt, zone).timestamp()),
            "abbreviation": city_dt.tzname() or "",
        })
    return {"cities": cities, "error": ""}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve saved world-clock cities read-only.")
    parser.add_argument("--config", type=Path, default=None, help="Path to world-clock.json.")
    parser.add_argument("--now", default=None, help="Optional reference epoch seconds or ISO timestamp.")
    parser.add_argument("--local-zone", default=None, help="Optional IANA zone override for local time.")
    args = parser.parse_args(argv)
    config_path = args.config if args.config is not None else default_config_path()
    try:
        now_dt = parse_now(args.now, args.local_zone)
    except (ValueError, ZoneInfoNotFoundError) as error:
        print(json.dumps({"cities": [], "error": str(error)}))
        return 1
    print(json.dumps(resolve_cities(config_path, now_dt), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
