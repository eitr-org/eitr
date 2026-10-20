import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'weather_popup', Path(__file__).parents[1] / 'scripts/weather-popup.py')
weather_popup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weather_popup)


class WeatherPopupTests(unittest.TestCase):
    def test_default_refresh_keeps_shared_cache(self):
        with patch.dict(weather_popup.os.environ, {'WEATHER_CACHE_FILE': '/tmp/shared-weather.json'}), \
                patch.object(weather_popup.subprocess, 'check_output', return_value='{"temp":"17°C"}') as query:
            self.assertEqual(weather_popup.weather(None)['temp'], '17°C')
            environment = query.call_args.kwargs['env']
            self.assertEqual(environment['WEATHER_FORCE_REFRESH'], '1')
            self.assertEqual(environment['WEATHER_CACHE_FILE'], '/tmp/shared-weather.json')

    def test_city_override_is_isolated(self):
        city = {'latitude': 34, 'longitude': -118, 'country_code': 'US', 'name': 'Malibu'}

        def collect(*args, **kwargs):
            environment = kwargs['env']
            self.assertEqual(environment['WEATHER_FORCE_REFRESH'], '1')
            state = Path(environment['WEATHER_STATE_FILE'])
            self.assertEqual(json.loads(state.read_text())['name'], 'Malibu')
            self.assertEqual(Path(environment['WEATHER_CACHE_FILE']).parent, state.parent)
            return '{"temp":"67°F"}'

        with patch.object(weather_popup.subprocess, 'check_output', side_effect=collect):
            self.assertEqual(weather_popup.weather(city)['temp'], '67°F')
