from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("arch_news", ROOT / "walker/scripts/actions/system/arch-news.py")
news = importlib.util.module_from_spec(spec)
spec.loader.exec_module(news)

FEED = b"""<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel>
<item><title>Newest: manual intervention</title><link>https://archlinux.org/news/newest/</link>
<pubDate>Fri, 16 Oct 2026 10:00:00 +0000</pubDate></item>
<item><title>Older news</title><link>https://archlinux.org/news/older/</link>
<pubDate>Mon, 21 Sep 2026 09:00:00 +0000</pubDate></item>
<item><title>Undated</title><link>x</link></item>
</channel></rss>"""


class ArchNewsTests(unittest.TestCase):
    def log(self, text):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "pacman.log"
        path.write_text(text)
        return path

    def test_the_last_full_upgrade_comes_from_pacmans_log(self):
        log = self.log("[2026-09-01T10:00:00-0300] [PACMAN] starting full system upgrade\n"
                       "[2026-10-01T08:30:00-0300] [PACMAN] starting full system upgrade\n"
                       "[2026-10-02T09:00:00-0300] [ALPM] installed foo (1-1)\n")
        self.assertEqual(news.last_upgrade(log), datetime(2026, 10, 1, 11, 30, tzinfo=timezone.utc))
        self.assertIsNone(news.last_upgrade(self.log("nothing here\n")))
        self.assertIsNone(news.last_upgrade(Path("/nonexistent/pacman.log")))

    def test_only_news_after_the_last_upgrade_is_listed_newest_first(self):
        items = news.news_since(FEED, datetime(2026, 10, 1, tzinfo=timezone.utc))
        self.assertEqual([title for _, title, _ in items], ["Newest: manual intervention"])
        self.assertEqual(len(news.news_since(FEED, datetime(2026, 1, 1, tzinfo=timezone.utc))), 2)

    def test_unreachable_feed_or_no_history_never_holds_up_an_update(self):
        with patch.object(news, "last_upgrade", return_value=datetime(2026, 1, 1, tzinfo=timezone.utc)), \
                patch.object(news, "fetch", side_effect=OSError("offline")):
            self.assertEqual(news.main(), 0)
        with patch.object(news, "last_upgrade", return_value=None), patch.object(news, "fetch") as fetch:
            self.assertEqual(news.main(), 0)
            fetch.assert_not_called()

    def test_news_is_printed_and_reported_with_exit_ten(self):
        with patch.object(news, "last_upgrade", return_value=datetime(2026, 10, 1, tzinfo=timezone.utc)), \
                patch.object(news, "fetch", return_value=FEED), patch("builtins.print") as printed:
            self.assertEqual(news.main(), 10)
        output = "\n".join(call.args[0] for call in printed.call_args_list)
        self.assertIn("Arch posted news since your last update:", output)
        self.assertIn("Newest: manual intervention (https://archlinux.org/news/newest/)", output)
        self.assertNotIn("Older news", output)


if __name__ == "__main__":
    unittest.main()
