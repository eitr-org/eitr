#!/usr/bin/env python3
"""CLI entry points for the shared weather implementation."""
import importlib.util
import json
import os
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('weather_domain', Path(__file__).with_name('weather-domain.py'))
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)
collector = backend.WeatherDomain()


def weather(city):
    return collector.weather(city, force=True)


def search(query):
    return collector.search(query)


if __name__ == '__main__':
    if sys.argv[1] == 'search':
        result = search(sys.argv[2])
    elif sys.argv[1] == 'status':
        result = collector.weather(force=os.environ.get('WEATHER_FORCE_REFRESH') == '1')
    else:
        result = weather(json.loads(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
