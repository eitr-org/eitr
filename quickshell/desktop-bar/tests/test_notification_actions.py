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
        self.assertIn('[("open", tr(\'Open image\')), ("edit", tr(\'Edit image\')), ("beautify", tr(\'Beautify\')), ("pin", tr(\'Pin on screen\')),', source)
        self.assertIn('call = ["beautify", "open"] if chosen == "beautify" else ["pins", "add"]', source)
        bar_dir = (BAR / 'qmldir').read_text()
        self.assertIn('ScreenshotPins capture/ScreenshotPins.qml', bar_dir)
        self.assertIn('BeautifyWindow capture/BeautifyWindow.qml', bar_dir)
        self.assertIn('[("open", tr(\'Play recording\')), ("folder", tr(\'Open folder\')), ("copy", tr(\'Copy path\'))]', source)
        # Editing saves over the screenshot it opened.
        self.assertIn('["satty", "-f", str(path), "-o", str(path)', source)


    def test_popups_show_on_every_display_unless_kept_on_the_main_one(self):
        service = (BAR / 'notifications/NotificationService.qml').read_text()
        self.assertIn('property bool popupsOnAllDisplays: true', service)
        self.assertIn('service.popupsOnAllDisplays = service.preferenceData.popupDisplays !== "main";', service)
        self.assertIn('popupDisplays: enabled ? "all" : "main"', service)
        panels = (BAR / 'bar/BarPanels.qml').read_text()
        self.assertIn('shown: barHost.isMainBar || barHost.notificationsRef.popupsOnAllDisplays', panels)
        shell = (BAR / 'shell.qml').read_text()
        # Displays without a bar get their own popup window, beside no bar.
        self.assertIn('screen => screen && shell.targetScreens().indexOf(screen) === -1', shell)
        self.assertIn('besideBar: false', shell)
        page = (BAR / 'settings/SettingsNotificationsPage.qml').read_text()
        self.assertIn('view.notifications.setPopupsOnAllDisplays(checked)', page)

    def test_event_sounds_are_optional_quiet_in_do_not_disturb_and_skip_low_priority(self):
        sounds = (BAR / 'services/EventSounds.qml').read_text()
        self.assertIn('property bool notifications: false', sounds)
        self.assertIn('property bool charger: false', sounds)
        self.assertIn('if (doNotDisturb) return;', sounds)
        self.assertIn('if (urgency === 0) return;', sounds)
        self.assertIn('notification.hints["suppress-sound"]', sounds)
        self.assertIn('play(urgency === 2 ? "dialog-warning" : "message-new-instant")', sounds)
        self.assertIn('play(pluggedIn ? "power-plug" : "power-unplug")', sounds)
        self.assertIn('singleton EventSounds 1.0 services/EventSounds.qml', (BAR / 'qmldir').read_text())
        service = (BAR / 'notifications/NotificationService.qml').read_text()
        self.assertIn('Binding { target: EventSounds; property: "doNotDisturb"; value: service.doNotDisturb }', service)
        self.assertIn('if (!notification.lastGeneration) EventSounds.notificationArrived(notification);', service)
        hooks = (BAR / 'services/SessionHooks.qml').read_text()
        self.assertIn('EventSounds.chargerPlugged(connected)', hooks)
        self.assertIn('sound-theme-freedesktop', (ROOT / 'distro/packages.txt').read_text().split())


if __name__ == '__main__':
    unittest.main()
