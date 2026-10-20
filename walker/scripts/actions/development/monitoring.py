#!/usr/bin/env python3
"""Monitoring dashboards: saved addresses of Grafana, Datadog, Sentry, New Relic,
Prometheus or any other tool, opened in the browser from Development > Monitoring.

They live only on this machine (~/.config/eitr/monitoring.json). EITR ships no
dashboards, accounts or brand icons; addresses never hold credentials.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break
from eitr_paths import code, config as user_config  # noqa: E402
from eitr_wizard import Step, collect as collect_setup
from eitr_i18n import tr  # noqa: E402

STORE = user_config("eitr/monitoring.json")
# Neutral Material Design icons from the Nerd Font, not the services' logos.
SERVICES = {
    "grafana": {"label": "Grafana", "icon": "\U000F0127", "example": "your-stack.grafana.net"},
    "datadog": {"label": "Datadog", "icon": "\U000F012A", "example": "app.datadoghq.com or app.datadoghq.eu"},
    "sentry": {"label": "Sentry", "icon": "\U000F0028", "example": "your-org.sentry.io"},
    "newrelic": {"label": "New Relic", "icon": "\U000F0437", "example": "one.newrelic.com"},
    "prometheus": {"label": "Prometheus", "icon": "\uEB31", "example": "localhost:9090"},
    "other": {"label": "Other", "icon": "\U000F0339", "example": "status.example.com"},
}


def web_addresses():
    """The Web Apps helper owns name and address validation; reuse it."""
    spec = importlib.util.spec_from_file_location(
        "eitr_webapps", code("walker/scripts/actions/install/webapps.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load():
    try:
        rows = json.loads(STORE.read_text())
    except FileNotFoundError:
        return []
    except ValueError as error:
        raise ValueError(tr('{path} is not valid JSON; fix or remove it.', path=STORE)) from error
    return [row for row in rows if isinstance(row, dict) and row.get("service") in SERVICES
            and isinstance(row.get("name"), str) and isinstance(row.get("url"), str)]


def save(rows):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STORE.with_suffix(".tmp")
    temporary.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    os.replace(temporary, STORE)


def identifier(service, name):
    return service + "-" + (re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48] or "dashboard")


def dashboards():
    rows = []
    for row in load():
        service = SERVICES[row["service"]]
        rows.append({"id": identifier(row["service"], row["name"]), "service": row["service"],
                     "label": service["label"], "icon": service["icon"], "name": row["name"], "url": row["url"]})
    return sorted(rows, key=lambda row: (row["name"].casefold(), row["label"].casefold()))


def add(service, name, url):
    if service not in SERVICES:
        raise ValueError(tr('Unknown monitoring service'))
    web = web_addresses()
    name, url = web.clean_name(name), web.clean_url(url)
    rows = load()
    if any(identifier(row["service"], row["name"]) == identifier(service, name) for row in rows):
        raise ValueError(tr('A {service} dashboard named {name} already exists.', service=SERVICES[service]['label'], name=name))
    rows.append({"service": service, "name": name, "url": url})
    save(rows)
    return name, url


def find(dashboard_id):
    match = next((row for row in dashboards() if row["id"] == dashboard_id), None)
    if match is None:
        raise ValueError(tr('That dashboard is no longer saved.'))
    return match


def open_dashboard(dashboard_id):
    subprocess.Popen(["xdg-open", find(dashboard_id)["url"]], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def remove(dashboard_id):
    find(dashboard_id)
    save([row for row in load() if identifier(row["service"], row["name"]) != dashboard_id])


def interactive():
    web = web_addresses()
    answers = collect_setup(tr('Add a monitoring dashboard: a saved address opened from Development > Monitoring.'), [
        Step('service', tr('Service number (Enter to cancel): '), options=[
            (tr('Other') if key == 'other' else SERVICES[key]['label'], key) for key in SERVICES]),
        Step('name', tr('Name (for example Production): '), validator=web.clean_name),
        Step('url', tr('Address (for example {example}): ', example='https://example.com'), validator=web.clean_url),
    ])
    service, name, url = (answers[key] for key in ('service', 'name', 'url'))
    name, url = add(service, name, url)
    subprocess.run(["notify-send", tr('Dashboard saved'), tr('{name} is in Development > Monitoring.', name=name)], check=False)
    return 0


def main(arguments):
    command = arguments[0] if arguments else ""
    if command == "add" and len(arguments) == 1:
        return interactive()
    if command == "list" and len(arguments) == 1:
        print(json.dumps(dashboards(), ensure_ascii=False))
        return 0
    if command == "open" and len(arguments) == 2:
        open_dashboard(arguments[1])
        return 0
    if command == "remove" and len(arguments) == 2:
        remove(arguments[1])
        return 0
    print("Usage: monitoring.py add | list | open ID | remove ID", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
