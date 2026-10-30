import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error

spec = importlib.util.spec_from_file_location(
    'weather_popup', Path(__file__).parents[1] / 'scripts/weather-popup.py')
weather_popup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weather_popup)
backend = weather_popup.backend

RAW = dict(current=dict(temperature_2m=17, apparent_temperature=16, relative_humidity_2m=60,
                        wind_speed_10m=5, weather_code=0, is_day=1),
           daily=dict(time=['2026-10-30', '2026-10-31'], weather_code=[0, 63],
                      temperature_2m_max=[20, 21], temperature_2m_min=[10, 11]))


class WeatherPopupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name) / 'state.json'
        self.cache = Path(self.directory.name) / 'cache.json'
        self.state.write_text(json.dumps(dict(latitude=34, longitude=-118, name='Home')))
        self.environment = patch.dict(os.environ, dict(WEATHER_STATE_FILE=str(self.state), WEATHER_CACHE_FILE=str(self.cache)))
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.domain = backend.WeatherDomain()

    def test_default_cache_ttl_and_cli_share_calculations(self):
        with patch.object(self.domain, 'http', return_value=RAW) as query:
            result = self.domain.weather()
            self.assertEqual(result['temp'], '17°C')
            self.assertEqual(result['forecastDays'], [dict(day='SAT', icon='63', high='21', low='11')])
            os.utime(self.cache, (time.time() - 800,) * 2)
            self.assertEqual(self.domain.read('weather.default'), result)
            self.assertLess(self.domain.next_refresh - time.monotonic(), 101, 'opening a cached forecast must preserve its expiry')
            query.assert_called_once()
            os.utime(self.cache, (time.time() - 901,) * 2)
            self.domain.weather()
            self.assertEqual(query.call_count, 2)
        with patch.object(weather_popup, 'collector', self.domain), patch.object(self.domain, 'http', return_value=RAW):
            self.assertEqual(weather_popup.weather(None), result)

    def test_city_override_is_isolated_and_units_match(self):
        city = dict(latitude=34, longitude=-118, country_code='US', name='Malibu')
        with patch.object(self.domain, 'http', return_value=RAW):
            self.domain.weather()
            original = self.cache.read_bytes()
            self.assertEqual(self.domain.weather(city)['temp'], '17°F')
            self.assertEqual(self.cache.read_bytes(), original)
            self.assertEqual(json.loads(self.state.read_text())['name'], 'Home')

    def test_offline_retains_last_good(self):
        with patch.object(self.domain, 'http', return_value=RAW):
            result = self.domain.weather()
        with patch.object(self.domain, 'http', side_effect=OSError()):
            self.assertEqual(self.domain.weather(force=True), result)
        self.cache.unlink()
        with patch.object(self.domain, 'http', side_effect=OSError()):
            self.assertEqual(self.domain.weather()['temp'], '--')

    def test_rate_limit_blocks_repeated_http_until_cooldown(self):
        error = urllib.error.HTTPError('https://api.open-meteo.com', 429, '', {'Retry-After': '1800'}, None)
        with patch.object(backend.urllib.request, 'urlopen', side_effect=error) as query:
            self.domain.weather(force=True)
            self.domain.weather(force=True)
            backend.WeatherDomain().weather(force=True)
            query.assert_called_once()
        self.assertGreater(self.domain.cooldowns['api.open-meteo.com'], time.monotonic() + 1700)

    def test_search_offline_and_no_results(self):
        with patch.object(self.domain, 'http', side_effect=OSError()):
            self.assertEqual(self.domain.search('city')['error'], 'City search unavailable')
        with patch.object(self.domain, 'http', return_value={}):
            self.assertEqual(self.domain.search('city')['error'], 'No cities found')

    def test_cli_rounding_preserves_awk_current_and_jq_forecast_values(self):
        self.assertEqual(backend.number(2.5), '2')
        self.assertEqual(backend.number(-2.5), '-2')
        self.assertEqual(backend.forecast_number(2.5), '3')
        self.assertEqual(backend.forecast_number(-2.5), '-3')
