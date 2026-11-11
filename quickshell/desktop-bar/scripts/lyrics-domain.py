"""Song lyrics from LRCLIB (lrclib.net), looked up only after the owner turns on online
lyrics in Drop's Media page. The title, artist, album and length of the playing song are
sent; nothing else. Answers are kept in memory for the session."""
from collections import OrderedDict
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

API = 'https://lrclib.net/api/'
AGENT = 'Eitr desktop (https://github.com/eitr-org/eitr)'
REMEMBERED = 200


class LyricsDomain:
    def __init__(self, opener=None):
        self.open = opener or urllib.request.urlopen
        self.lock = threading.Lock()
        self.remembered = OrderedDict()
        self.cooldown = 0

    def http(self, path, params, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or time.monotonic() < self.cooldown:
            raise TimeoutError('lyrics-unavailable')
        request = urllib.request.Request(API + path + '?' + urllib.parse.urlencode(params), headers={'User-Agent': AGENT})
        try:
            with self.open(request, timeout=min(8, remaining)) as response:
                payload = response.read(524289)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code == 429:
                self.cooldown = time.monotonic() + 60
            raise
        if len(payload) > 524288:
            raise ValueError('oversize-response')
        return json.loads(payload)

    def track(self, title, artist='', album='', duration=0, deadline=None):
        """{'synced': LRC text, 'plain': text} for the song, both empty when none is known,
        or {'error': ...} when LRCLIB could not be asked."""
        key = json.dumps([title.casefold(), artist.casefold(), round(duration)])
        with self.lock:
            if key in self.remembered:
                self.remembered.move_to_end(key)
                return self.remembered[key]
            deadline = deadline or time.monotonic() + 15
            try:
                found = None
                if artist and duration:
                    params = dict(track_name=title, artist_name=artist, duration=round(duration))
                    if album:
                        params['album_name'] = album
                    found = self.http('get', params, deadline)
                if not found:
                    results = self.http('search', dict(track_name=title, artist_name=artist) if artist else dict(q=title), deadline) or []
                    candidates = [entry for entry in results if isinstance(entry, dict) and (entry.get('syncedLyrics') or entry.get('plainLyrics'))]
                    if duration:
                        candidates.sort(key=lambda entry: (not entry.get('syncedLyrics'), abs(float(entry.get('duration') or 0) - duration)))
                    found = candidates[0] if candidates and (not duration or abs(float(candidates[0].get('duration') or 0) - duration) <= 5) else None
            except (OSError, ValueError, TimeoutError):
                return dict(synced='', plain='', error='unavailable')
            result = dict(synced=str((found or {}).get('syncedLyrics') or ''), plain=str((found or {}).get('plainLyrics') or ''))
            self.remembered[key] = result
            if len(self.remembered) > REMEMBERED:
                self.remembered.popitem(last=False)
            return result
