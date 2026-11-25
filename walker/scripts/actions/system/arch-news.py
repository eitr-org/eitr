#!/usr/bin/env python3
"""List Arch Linux news posted since this system's last full upgrade.

Arch announces upgrades that need a manual step on its news feed. Exit codes:
0 for no news, 10 when news was printed and 11 when the feed is unavailable.
"""
import eitr_bootstrap
from eitr_i18n import tr
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import re
import sys
import urllib.request
import xml.etree.ElementTree as ElementTree

FEED = "https://archlinux.org/feeds/news/"
PACMAN_LOG = Path("/var/log/pacman.log")
LOG_ENTRY = re.compile(r"^\[([^\]]+)\] \[(PACMAN|ALPM)\] (.*)$")
LIMIT = 5


def last_upgrade(log=PACMAN_LOG):
    """Return the last completed full-upgrade transaction in pacman's log."""
    completed = None
    full_upgrade = False
    try:
        with log.open(errors="replace") as stream:
            for line in stream:
                match = LOG_ENTRY.match(line)
                if not match:
                    continue
                timestamp, component, message = match.groups()
                if component == "PACMAN":
                    if message.startswith("Running "):
                        full_upgrade = False
                    elif message == "starting full system upgrade":
                        full_upgrade = True
                elif full_upgrade and message == "transaction completed":
                    full_upgrade = False
                    try:
                        completed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        pass
    except OSError:
        pass
    return completed


def news_since(feed_xml, since):
    """(date, title, link) of feed items published after ``since``, newest first."""
    items = []
    for item in ElementTree.fromstring(feed_xml).iter("item"):
        try:
            published = parsedate_to_datetime(item.findtext("pubDate", ""))
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if published > since:
            items.append((published, item.findtext("title", "").strip(), item.findtext("link", "").strip()))
    return sorted(items, reverse=True)


def fetch(url=FEED, timeout=8):
    request = urllib.request.Request(url, headers={"User-Agent": "Eitr System Update"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def main():
    since = last_upgrade() or datetime.min.replace(tzinfo=timezone.utc)
    try:
        news = news_since(fetch(), since)
    except (OSError, ElementTree.ParseError, ValueError):
        print(tr("Could not check Arch Linux news."), file=sys.stderr)
        return 11
    if not news:
        return 0
    print(tr('Arch posted news since your last update:'))
    for published, title, link in news[:LIMIT]:
        print(f"  • {title} ({link})")
    return 10


if __name__ == "__main__":
    sys.exit(main())
