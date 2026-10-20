#!/usr/bin/env python3
"""List Arch Linux news posted since this system's last full upgrade.

Arch announces upgrades that need a manual step on its news feed. Exit codes:
0 when there is nothing to show (or the feed cannot be reached: an update
should never wait on it), 10 when news was printed and the caller should ask.
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
UPGRADE = re.compile(r"^\[([^\]]+)\] \[PACMAN\] starting full system upgrade")
LIMIT = 5


def last_upgrade(log=PACMAN_LOG):
    """When the last full upgrade started, from pacman's log; None if never."""
    try:
        lines = log.read_text(errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        match = UPGRADE.match(line)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                return None
    return None


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
    since = last_upgrade()
    if since is None:
        return 0
    try:
        news = news_since(fetch(), since)
    except (OSError, ElementTree.ParseError, ValueError):
        return 0
    if not news:
        return 0
    print(tr('Arch posted news since your last update:'))
    for published, title, link in news[:LIMIT]:
        print(f"  • {title} ({link})")
    return 10


if __name__ == "__main__":
    sys.exit(main())
