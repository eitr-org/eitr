#!/usr/bin/env python3
"""System batteries only; peripherals must not turn a desktop into a laptop."""
import eitr_bootstrap
from eitr_battery import system_batteries
import json
from pathlib import Path

def number(path, name):
    try:
        return float((path / name).read_text().strip())
    except (OSError, ValueError):
        return 0

def status(root=Path('/sys/class/power_supply'), batteries=None):
    paths = system_batteries(root) if batteries is None else batteries
    batteries = []
    for path in paths:
        try:
            full = number(path, 'energy_full') or number(path, 'charge_full')
            now = number(path, 'energy_now') or number(path, 'charge_now')
            design = number(path, 'energy_full_design') or number(path, 'charge_full_design')
            rate = number(path, 'power_now') if number(path, 'energy_full') else number(path, 'current_now')
            state = (path / 'status').read_text().strip()
            batteries.append({'percent': number(path, 'capacity'), 'status': state,
                              'health': 100 * full / design if design else 0,
                              'hours': (full - now if state == 'Charging' else now) / rate if rate else 0})
        except OSError:
            continue
    if not batteries:
        return {'available': False, 'percent': 0, 'status': '', 'health': 0, 'hours': 0}
    state = next((b['status'] for b in batteries if b['status'] == 'Discharging'), batteries[0]['status'])
    result = {'available': True, 'status': state}
    for key in ('percent', 'health', 'hours'):
        result[key] = sum(b[key] for b in batteries) / len(batteries)
    return result

if __name__ == '__main__':
    print(json.dumps(status()))
