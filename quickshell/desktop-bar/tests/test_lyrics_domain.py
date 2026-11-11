import importlib.util
import io
import json
from pathlib import Path
import unittest
import urllib.error
import urllib.parse

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'lyrics-domain.py'


def load():
    specification = importlib.util.spec_from_file_location('lyrics_domain', SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *details):
        return False


class LyricsDomainTests(unittest.TestCase):
    def setUp(self):
        self.module = load()
        self.calls = []

    def domain(self, answers):
        def opener(request, timeout):
            url = urllib.parse.urlparse(request.full_url)
            self.calls.append((url.path.rsplit('/', 1)[-1], dict(urllib.parse.parse_qsl(url.query)), request.get_header('User-agent')))
            answer = answers[url.path.rsplit('/', 1)[-1]]
            if isinstance(answer, int):
                raise urllib.error.HTTPError(request.full_url, answer, 'error', {}, None)
            return Response(json.dumps(answer).encode())
        return self.module.LyricsDomain(opener)

    def test_exact_match_sends_only_the_song_and_is_remembered(self):
        domain = self.domain(dict(get=dict(syncedLyrics='[00:01.00] Hello', plainLyrics='Hello')))
        first = domain.track('Song', 'Artist', 'Album', 200.4)
        second = domain.track('song', 'artist', 'Album', 200)
        self.assertEqual(first, dict(synced='[00:01.00] Hello', plain='Hello'))
        self.assertEqual(second, first)
        self.assertEqual(len(self.calls), 1, 'the second ask is answered from memory')
        endpoint, params, agent = self.calls[0]
        self.assertEqual(endpoint, 'get')
        self.assertEqual(params, dict(track_name='Song', artist_name='Artist', album_name='Album', duration='200'))
        self.assertIn('Eitr', agent)

    def test_search_fallback_prefers_synced_lyrics_of_the_closest_length(self):
        domain = self.domain(dict(get=404, search=[
            dict(duration=320, syncedLyrics='[00:01.00] far'),
            dict(duration=201, plainLyrics='close plain'),
            dict(duration=199, syncedLyrics='[00:01.00] close synced'),
        ]))
        self.assertEqual(domain.track('Song', 'Artist', duration=200)['synced'], '[00:01.00] close synced')

    def test_nothing_close_enough_is_no_lyrics(self):
        domain = self.domain(dict(get=404, search=[dict(duration=400, syncedLyrics='[00:01.00] other')]))
        self.assertEqual(domain.track('Song', 'Artist', duration=200), dict(synced='', plain=''))

    def test_rate_limit_is_unavailable_and_pauses_further_asks(self):
        domain = self.domain(dict(get=429))
        self.assertEqual(domain.track('Song', 'Artist', duration=200)['error'], 'unavailable')
        self.assertEqual(domain.track('Other', 'Artist', duration=180)['error'], 'unavailable')
        self.assertEqual(len(self.calls), 1, 'no request during the cooldown')


if __name__ == '__main__':
    unittest.main()
