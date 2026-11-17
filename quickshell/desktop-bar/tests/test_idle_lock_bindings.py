from bar_frame_source import frame_source
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "shell.qml").read_text() + frame_source(ROOT)


class IdleLockBindingsTests(unittest.TestCase):
    def test_left_group_icons_toggle_without_a_panel(self):
        zone_items = (ROOT / "bar/BarZoneItems.qml").read_text()
        self.assertIn('if (itemId === "idleLock")', zone_items)
        self.assertIn('zoneGrid.host.switchIdleLock()', zone_items)
        self.assertIn('zoneGrid.host.idleLockTooltip', zone_items)
        self.assertIn("function switchIdleLock() { if (!toggleIdleLock.running) toggleIdleLock.running = true; }", SHELL)
        self.assertNotIn("idleLockMenu", SHELL)
        self.assertFalse((ROOT / "IdleLockMenu.qml").exists())

    def test_icons_follow_ai_usage_on_the_left(self):
        order_source = (ROOT / "BarIconOrder.js").read_text()
        self.assertLess(order_source.index('"ai"'), order_source.index('"idleLock"'))
        self.assertIn('zone: "left"', (ROOT / "bar/BarLeftGroup.qml").read_text())
        self.assertIn('zone: "left"', (ROOT / "bar/BarVerticalPlacement.qml").read_text())

    def test_shared_status_icon_forwards_the_actual_button(self):
        component = (ROOT / "bar/StatusIcon.qml").read_text()
        self.assertIn("signal clicked(int button)", component)
        self.assertIn("item.clicked(event.button)", component)


if __name__ == "__main__":
    unittest.main()
