from pathlib import Path
import unittest


SHELL = (Path(__file__).resolve().parents[1] / "shell.qml").read_text()


class IdleLockBindingsTests(unittest.TestCase):
    def test_horizontal_and_vertical_icons_separate_mouse_buttons(self):
        for name in ("idleLockIcon", "verticalIdleLockIcon"):
            with self.subTest(icon=name):
                block = SHELL.split(f"id: {name}", 1)[1].split("onOpenChanged:", 1)[0]
                self.assertIn("rightClickable: true", block)
                self.assertIn("button === Qt.RightButton", block)
                self.assertIn("if (!toggleIdleLock.running) toggleIdleLock.running = true", block)
                self.assertIn("else bar.togglePanel(idleLockMenu)", block)

    def test_shared_status_icon_forwards_the_actual_button(self):
        component = SHELL.split("component StatusIcon: Item", 1)[1].split("component VerticalBarIcon", 1)[0]
        self.assertIn("signal clicked(int button)", component)
        self.assertIn("item.clicked(event.button)", component)
