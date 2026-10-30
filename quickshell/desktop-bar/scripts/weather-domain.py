"""Weather calculations and compatible disk cache shared by broker and CLI."""
import datetime
import hashlib
import email.utils
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

TTL = 900
CONDITIONS = {0: 'Clear', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
              45: 'Fog', 48: 'Fog', 51: 'Drizzle', 53: 'Drizzle', 55: 'Drizzle',
              56: 'Freezing drizzle', 57: 'Freezing drizzle', 61: 'Rain', 63: 'Rain', 65: 'Rain',
              66: 'Freezing rain', 67: 'Freezing rain', 71: 'Snow', 73: 'Snow', 75: 'Snow',
              77: 'Snow grains', 80: 'Rain showers', 81: 'Rain showers', 82: 'Rain showers',
              85: 'Snow showers', 86: 'Snow showers', 95: 'Thunderstorm',
              96: 'Thunderstorm with hail', 99: 'Thunderstorm with hail'}


def icon(code, daytime=1):
    if code == 0:
        return '\ue32b' if daytime == 0 else '\ue30d'
    if code in (1, 2):
        return '\ue32e' if daytime == 0 else '\ue302'
    if code in (45, 48):
        return '\ue346' if daytime == 0 else '\ue313'
    if code in (51, 53, 55, 56, 57, 61):
        return '\ue333' if daytime == 0 else '\ue308'
    if code in (63, 65, 66, 67, 80, 81, 82):
        return '\ue318'
    if code in (71, 73, 75, 77, 85, 86):
        return '\ue31a'
    return '\ue31d' if code in (95, 96, 99) else '\ue33d'


def number(value):
    return '--' if value is None else format(float(value), '.0f')


def forecast_number(value):
    return str(math.floor(value + .5) if value >= 0 else math.ceil(value - .5))


def calculate(raw, location, source):
    current, daily = raw['current'], raw.get('daily', {})
    fahrenheit = location.get('country_code') in ('US', 'LR', 'MM')
    unit, wind = ('°F', 'mph') if fahrenheit else ('°C', 'km/h')
    code = current.get('weather_code')
    temperature = number(current.get('temperature_2m')) + unit
    days = []
    for index, date in enumerate(daily.get('time', [])[:4]):
        if index == 0:
            continue
        days.append(dict(day=datetime.date.fromisoformat(date).strftime('%a').upper(),
                         icon=str(daily['weather_code'][index]),
                         high=forecast_number(daily['temperature_2m_max'][index]),
                         low=forecast_number(daily['temperature_2m_min'][index])))
    maximum = daily.get('temperature_2m_max', [])
    return dict(source=source, text=icon(code, current.get('is_day', 1)) + ' ' + temperature,
                location=location.get('name') or 'Weather', condition=CONDITIONS.get(code, 'Current conditions'),
                temp=temperature, feels=number(current.get('apparent_temperature')) + unit,
                wind=number(current.get('wind_speed_10m')) + ' ' + wind,
                humidity=number(current.get('relative_humidity_2m')) + '%',
                forecast=number(maximum[1] if len(maximum) > 1 else None) + '°', forecastDays=days)


def read_json(path):
    try:
        result = json.loads(path.read_text())
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError):
        return {}


class WeatherDomain:
    def __init__(self):
        self.lock = threading.Lock()
        self.cooldowns = {}
        self.cities = {}
        self.next_refresh = 0

    def http(self, base, params, deadline):
        cache = Path(os.environ.get('WEATHER_CACHE_FILE') or Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'desktop-bar-weather.json')
        cooldown_file = cache.with_name(cache.name + '.cooldowns')
        host = urllib.parse.urlsplit(base).netloc
        persisted = read_json(cooldown_file).get(host, 0)
        if isinstance(persisted, (int, float)) and persisted > time.time():
            self.cooldowns[host] = max(self.cooldowns.get(host, 0), time.monotonic() + persisted - time.time())
        if time.monotonic() < self.cooldowns.get(host, 0):
            raise OSError('cooldown')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        try:
            with urllib.request.urlopen(base + '?' + urllib.parse.urlencode(params), timeout=min(5, remaining)) as response:
                payload = response.read(1048577)
                if len(payload) > 1048576:
                    raise ValueError('oversize-response')
                return json.loads(payload)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                try:
                    delay = max(TTL, float(error.headers.get('Retry-After', TTL)))
                except (TypeError, ValueError):
                    try:
                        delay = max(TTL, email.utils.parsedate_to_datetime(error.headers['Retry-After']).timestamp() - time.time())
                    except (KeyError, TypeError, ValueError):
                        delay = TTL
                self.cooldowns[host] = time.monotonic() + delay
                saved = read_json(cooldown_file)
                saved[host] = time.time() + delay
                try:
                    cooldown_file.parent.mkdir(parents=True, exist_ok=True)
                    descriptor, temporary = tempfile.mkstemp(dir=cooldown_file.parent, prefix=cooldown_file.name)
                    try:
                        with os.fdopen(descriptor, 'w') as output:
                            json.dump(saved, output)
                        os.replace(temporary, cooldown_file)
                    finally:
                        Path(temporary).unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    def search(self, query, deadline=None):
        with self.lock:
            try:
                payload = self.http('https://geocoding-api.open-meteo.com/v1/search',
                                    dict(name=query, count=5, language='en', format='json'), deadline or time.monotonic() + 5)
                cities = [city for city in payload.get('results', []) if all(key in city for key in ('name', 'latitude', 'longitude'))]
                return dict(cities=cities, error='' if cities else 'No cities found')
            except (OSError, ValueError):
                return dict(cities=[], error='City search unavailable')

    def read(self, topic):
        self.next_refresh = time.monotonic() + TTL
        return self.weather()

    def weather(self, city=None, force=False, deadline=None):
        with self.lock:
            deadline = deadline or time.monotonic() + 16
            state = Path(os.environ.get('WEATHER_STATE_FILE') or Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-bar/weather.json')
            cache = Path(os.environ.get('WEATHER_CACHE_FILE') or Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'desktop-bar-weather.json')
            location = dict(city) if city else read_json(state)
            if city:
                location['name'] = ', '.join(filter(None, [city['name'], city.get('country')]))
                key = json.dumps(city, sort_keys=True)
                cached, updated = self.cities.get(key, ({}, 0))
                legacy_state = dict(latitude=city['latitude'], longitude=city['longitude'],
                                    country_code=city.get('country_code'), name=location['name'])
                source = 'open-meteo-v4-' + hashlib.sha256(json.dumps(legacy_state).encode()).hexdigest()
            else:
                source = 'open-meteo-v4-' + (hashlib.sha256(state.read_bytes()).hexdigest() if state.is_file() else 'auto')
                cached = read_json(cache)
                updated = cache.stat().st_mtime if cache.is_file() else 0
            if not force and cached.get('source') == source and time.time() - updated < TTL:
                if not city:
                    self.next_refresh = time.monotonic() + max(0, TTL - (time.time() - updated))
                return cached
            try:
                if location.get('latitude') is None or location.get('longitude') is None:
                    if location.get('name'):
                        try:
                            resolved = self.http('https://geocoding-api.open-meteo.com/v1/search',
                                                 dict(name=location['name'], count=1, language='en', format='json'), deadline)['results'][0]
                            location.update(latitude=resolved['latitude'], longitude=resolved['longitude'])
                            location['name'] = ', '.join(filter(None, [resolved['name'], resolved.get('country')]))
                        except (OSError, ValueError, KeyError, IndexError):
                            pass
                    if location.get('latitude') is None or location.get('longitude') is None:
                        area = self.http('https://wttr.in/', dict(format='j1'), deadline)['nearest_area'][0]
                        location.update(latitude=area['latitude'], longitude=area['longitude'],
                                        name=', '.join(filter(None, [area['areaName'][0]['value'], area['country'][0]['value']])))
                fahrenheit = location.get('country_code') in ('US', 'LR', 'MM')
                raw = self.http('https://api.open-meteo.com/v1/forecast', dict(
                    latitude=location['latitude'], longitude=location['longitude'],
                    current='temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code,is_day',
                    daily='weather_code,temperature_2m_max,temperature_2m_min', forecast_days=4, timezone='auto',
                    temperature_unit='fahrenheit' if fahrenheit else 'celsius', wind_speed_unit='mph' if fahrenheit else 'kmh'), deadline)
                result = calculate(raw, location, source)
                if city:
                    if len(self.cities) >= 32:
                        self.cities.pop(next(iter(self.cities)))
                    self.cities[key] = (result, time.time())
                else:
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    descriptor, temporary = tempfile.mkstemp(dir=cache.parent, prefix=cache.name)
                    try:
                        with os.fdopen(descriptor, 'w') as output:
                            json.dump(result, output, separators=(',', ':'), ensure_ascii=False)
                            output.write('\n')
                        os.replace(temporary, cache)
                        self.next_refresh = time.monotonic() + TTL
                    finally:
                        Path(temporary).unlink(missing_ok=True)
                return result
            except (OSError, ValueError, KeyError, IndexError):
                return cached or dict(source=source, text='\ue33d --', location='Weather', condition='Unavailable',
                                      temp='--', feels='--', wind='--', humidity='--', forecast='--', forecastDays=[])
