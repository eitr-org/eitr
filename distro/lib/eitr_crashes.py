"""Shared crash-notification preference, including the former welcome choice."""
import json
from eitr_paths import config, state, read_settings, write_settings


def settings():
    try:
        path = config('eitr/crash-help.json')
        if path.exists():
            result = read_settings(path, {'enabled': True, 'ignored': []})
        else:
            try:
                previous = json.loads(state('eitr/problem-reports.json').read_text())
            except (OSError, ValueError):
                previous = {}
            if not isinstance(previous, dict):
                previous = {}
            result = {'enabled': previous.get('offer', True), 'ignored': []}
        if type(result['enabled']) is not bool or not isinstance(result['ignored'], list) or not all(isinstance(program, str) for program in result['ignored']):
            raise ValueError('Invalid crash notification settings')
        return result
    except (OSError, ValueError, TypeError):
        return {'enabled': False, 'ignored': []}


def set_enabled(enabled):
    previous = settings()
    write_settings(config('eitr/crash-help.json'), {**previous, 'enabled': enabled})
