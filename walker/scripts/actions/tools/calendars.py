#!/usr/bin/env python3
"""Read-only calendar subscriptions through a calendar's secret iCal address.

  calendars.py add         ask for the provider, the address and a name
  calendars.py rows        JSON rows for the Walker menu (names and hosts only)
  calendars.py remove ID   ask, then forget that calendar
  calendars.py refresh     fetch every calendar, cache its events, time the alerts
  calendars.py refresh --if-older SECONDS   the same, unless a refresh is that recent
  calendars.py sync        refresh now and report the result in a notification
  calendars.py fire KEY    (a timer runs this) alert for one event

The addresses are secrets: they live only in $XDG_CONFIG_HOME/eitr/calendars/
subscriptions.json (folder 0700, file 0600) and never reach a command line, a log,
a notification or an error message, which name the calendar and its host instead.
Events from a week ago to 60 days ahead are cached in
$XDG_CACHE_HOME/eitr/calendar-events.json for the calendar panel. eitr-calendars.timer
refreshes them every 15 minutes and at login while at least one calendar exists;
opening the calendar panel also refreshes them when the last refresh is over a minute old.
"""
import eitr_bootstrap
from eitr_i18n import tr
from eitr_wizard import collect, Step
from eitr_paths import cache, config, state
from eitr_app import app_command
from contextlib import contextmanager
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from ical import CalendarError, parse_events
import reminders

TIMER = 'eitr-calendars.timer'
MAX_BYTES = 5 * 1024 * 1024
TIMEOUT = 20
# Refreshes run every 15 minutes; events starting before the next one get a timer now.
ALERT_HORIZON = 20 * 60
PROVIDERS = {
    'google': 'https://calendar.google.com/calendar/r/settings',
    'outlook': 'https://outlook.live.com/calendar/0/options/calendar/SharedCalendars',
}


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
            subprocess.Popen(app_command(['xdg-open', PROVIDERS[provider]]), stdout=subprocess.DEVNULL,
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
    if command == 'refresh' and len(rest) == 2 and rest[0] == '--if-older' and rest[1].isdigit():
        # The calendar panel asks on opening; a refresh within that many seconds is enough.
        if not load_calendars() or time.time() - load_cache().get('updated', 0) < int(rest[1]):
            return 0
        with locked():
            return refresh()
    if command == 'sync' and not rest:
        with locked():
            failed = refresh()
        count = len(load_cache()['events'])
        reminders.notify(tr('Calendars refreshed'), tr('{count} events from the last week to the next 60 days.', count=count)
                         if not failed else tr('Some calendars could not be reached; their previous events stay.'))
        return failed
    if command == 'fire' and len(rest) == 1:
        with locked():
            return fire(rest[0])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
