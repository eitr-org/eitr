#!/usr/bin/python3 -I
"""Set the timezone once the network is up, after an offline installation.

The guided installer leaves MARKER when it could not detect the timezone and
fell back to UTC. This runs as root from eitr-timezone.service, applies the
detected zone, removes the marker and is not run again. Without a network it
fails so systemd retries later.
"""
import sys
from pathlib import Path
# Run as root with python3 -I, which leaves the script's own folder off sys.path;
# that root-owned folder holds the eitr_bootstrap link to Eitr's library.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eitr_bootstrap  # noqa: E402
from eitr_i18n import tr
from pathlib import Path
import subprocess
import sys
import urllib.request
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MARKER = Path("/var/lib/eitr/timezone-automatic")
# Plain-text geolocation answers; some networks block one of them.
SERVICES = ("https://ipinfo.io/timezone", "https://ipapi.co/timezone/")


def lookup(url):
    return urllib.request.urlopen(url, timeout=10).read(64).decode().strip()


def detect(fetch=lookup):
    errors = []
    for url in SERVICES:
        try:
            zone = fetch(url)
            ZoneInfo(zone)
            if zone in ("UTC", "Etc/UTC") or "/" not in zone:
                raise ValueError(tr('unusable answer {zone}', zone=f'{zone!r}'))
            return zone
        except (OSError, ValueError, ZoneInfoNotFoundError) as error:
            errors.append(f"{url}: {error}")
    raise ValueError("; ".join(errors))


def main():
    if not MARKER.exists():
        return 0
    try:
        zone = detect()
    except (OSError, ValueError, ZoneInfoNotFoundError) as error:
        print(tr('Timezone not detected yet: {error}', error=f'{error}'), file=sys.stderr)
        return 1
    subprocess.run(["timedatectl", "set-timezone", zone], check=True)
    MARKER.unlink(missing_ok=True)
    print(tr('Timezone set to {zone}', zone=f'{zone}'))
    return 0


if __name__ == "__main__":
    sys.exit(main())
