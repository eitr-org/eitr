"""The newest notification is reachable from the keyboard, repeats collapse into one
card, and saved screenshots and recordings offer the actions the Handbook describes."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


class NotificationActionTests(unittest.TestCase):
    def test_newest_notification_can_be_opened_or_dismissed_from_the_keyboard(self):
        service = (BAR / 'notifications/NotificationService.qml').read_text()
        self.assertIn('function act(): bool { return service.actOnNewest(); }', service)
        self.assertIn('function dismissNewest(): bool { return service.dismissNewest(); }', service)
        # Clicking a card runs its default action, so the shortcut prefers it too.
        self.assertIn('candidate.identifier === "default"', service)
        lua = (ROOT / 'hypr/hyprland.lua').read_text()
        self.assertIn('" + ALT + N", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- notifications act")', lua)
        self.assertIn('" + ALT + SHIFT + N", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- notifications dismissNewest")', lua)
        rows = {row['text']: row for row in json.loads((ROOT / 'elephant/menu-rows/shortcuts.json').read_text())}
        self.assertEqual(rows['Open Newest Notification']['subtext'], 'SUPER + Alt + N')
        self.assertEqual(rows['Dismiss Newest Notification']['subtext'], 'SUPER + Alt + Shift + N')

    def test_identical_notifications_collapse_into_one_counted_card(self):
        service = (BAR / 'notifications/NotificationService.qml').read_text()
        self.assertIn('other.appName === notification.appName', service)
        self.assertIn('other.summary === notification.summary && other.body === notification.body', service)
        self.assertIn('counts[notification.id] = twin ? (counts[twin.id] || 1) + 1 : 1;', service)
        card = (BAR / 'notifications/NotificationCard.qml').read_text()
        self.assertIn('(card.repeats > 1 ? "  ×" + card.repeats : "")', card)
        for name in ('NotificationPopups.qml', 'NotificationGroup.qml'):
            self.assertIn('repeats:', (BAR / 'notifications' / name).read_text())

    def test_saved_screenshots_and_recordings_offer_their_actions(self):
        source = (BAR / 'scripts/obs-control.py').read_text()
        self.assertIn('[("open", tr(\'Open image\')), ("edit", tr(\'Edit image\')), ("folder", tr(\'Open folder\'))]', source)
        self.assertIn('[("open", tr(\'Play recording\')), ("folder", tr(\'Open folder\')), ("copy", tr(\'Copy path\'))]', source)
        # Editing saves over the screenshot it opened.
        self.assertIn('["satty", "-f", str(path), "-o", str(path)', source)


if __name__ == '__main__':
    unittest.main()
