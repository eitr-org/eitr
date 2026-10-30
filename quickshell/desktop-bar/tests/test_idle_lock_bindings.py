from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "shell.qml").read_text()


class IdleLockBindingsTests(unittest.TestCase):
    def test_left_group_icons_toggle_without_a_panel(self):
        horizontal = SHELL.split("id: idleLockIcon", 1)[1].split("}", 1)[0]
        vertical = SHELL.split("id: verticalIdleLockIcon", 1)[1].split("\n", 1)[0]
        for name, block in (("horizontal", horizontal), ("vertical", vertical)):
            with self.subTest(icon=name):
                self.assertIn("onClicked: shell.switchIdleLock()", block)
                self.assertIn("shell.idleLockTooltip", block)
        self.assertIn("function switchIdleLock() { if (!toggleIdleLock.running) toggleIdleLock.running = true; }", SHELL)
        self.assertNotIn("idleLockMenu", SHELL)
        self.assertFalse((ROOT / "IdleLockMenu.qml").exists())

    def test_icons_follow_ai_usage_on_the_left(self):
        left = SHELL.split("id: hardwareStatus", 1)[1].split("SystemMonitorMenu {", 1)[0]
        self.assertLess(left.index("id: aiIcon"), left.index("id: idleLockIcon"))
        vertical = SHELL.split("id: verticalHardware", 1)[1].split("Item {", 1)[0]
        self.assertLess(vertical.index("id: verticalAiIcon"), vertical.index("id: verticalIdleLockIcon"))

    def test_shared_status_icon_forwards_the_actual_button(self):
        component = (ROOT / "StatusIcon.qml").read_text()
        self.assertIn("signal clicked(int button)", component)
        self.assertIn("item.clicked(event.button)", component)


if __name__ == "__main__":
    unittest.main()
