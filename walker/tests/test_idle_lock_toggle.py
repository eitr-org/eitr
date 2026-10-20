from pathlib import Path
import unittest


class IdleLockToggleTests(unittest.TestCase):
    def test_toggle_changes_service_without_notifications(self):
        root = Path(__file__).resolve().parents[2]
        script = (root / "walker/scripts/actions/toggle/idle-lock.sh").read_text()
        self.assertNotIn("notify-send", script)
        self.assertIn("pkill -x hypridle", script)
        self.assertIn("uwsm app -- eitr-hypridle", script)
        self.assertIn("setsid eitr-hypridle", script)
