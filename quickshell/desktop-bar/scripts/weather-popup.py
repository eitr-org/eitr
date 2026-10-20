#!/usr/bin/env python3
"""Session-only city overrides using the existing weather collector."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request


def weather(city):
    with tempfile.TemporaryDirectory(prefix='weather-popup-') as directory:
        environment = os.environ.copy()
        environment['WEATHER_FORCE_REFRESH'] = '1'
        if city:
            state = Path(directory) / 'location.json'
            state.write_text(json.dumps({
                'latitude': city['latitude'], 'longitude': city['longitude'],
                'country_code': city.get('country_code'),
                'name': ', '.join(filter(None, [city['name'], city.get('country')])),
            }))
            environment['WEATHER_STATE_FILE'] = str(state)
            environment['WEATHER_CACHE_FILE'] = str(Path(directory) / 'weather.json')
        raw = subprocess.check_output([str(Path(__file__).with_name('weather-status.sh'))],
                                      text=True, env=environment, timeout=20)
        return json.loads(raw.splitlines()[-1])


def search(query):
    params = urllib.parse.urlencode({'name': query, 'count': 5, 'language': 'en', 'format': 'json'})
    try:
        with urllib.request.urlopen('https://geocoding-api.open-meteo.com/v1/search?' + params, timeout=5) as response:
            cities = json.load(response).get('results', [])
        cities = [city for city in cities if all(key in city for key in ('name', 'latitude', 'longitude'))]
        return {'cities': cities, 'error': '' if cities else 'No cities found'}
    except (OSError, ValueError):
        return {'cities': [], 'error': 'City search unavailable'}


if __name__ == '__main__':
    if sys.argv[1] == 'search':
        print(json.dumps(search(sys.argv[2])))
    else:
        print(json.dumps(weather(json.loads(sys.argv[2]) if len(sys.argv) > 2 else None)))
