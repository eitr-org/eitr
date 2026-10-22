import importlib.util
from pathlib import Path
import re
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("menu_action", ROOT / "quickshell/desktop-bar/scripts/menu-action.py")
action = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action)


class MenuActionTests(unittest.TestCase):
    def test_runs_the_rows_own_command_detached(self):
        with patch.object(action.subprocess, "Popen") as start:
            action.main(["toggle", "Screensaver"])
        command = start.call_args.args[0]
        self.assertEqual(command[:2], ["sh", "-c"])
        self.assertTrue(command[2].endswith("toggle/screensaver.sh"))
        self.assertTrue(start.call_args.kwargs["start_new_session"])

    def test_submenus_and_unknown_rows_are_refused(self):
        with self.assertRaisesRegex(ValueError, "submenu"):
            action.command("update", "Update Channel")
        with self.assertRaisesRegex(ValueError, "No row"):
            action.command("toggle", "Nothing")
        with self.assertRaisesRegex(ValueError, "Invalid menu"):
            action.command("../secrets", "x")

    def test_every_control_center_button_names_a_real_menu_row(self):
        # A renamed Walker row must not silently break a Control Center button.
        center = (ROOT / "quickshell/desktop-bar/ControlCenter.qml").read_text()
        calls = re.findall(r'menuAction\("([^"]+)", "([^"]+)"\)', center)
        calls += re.findall(r'"menu-action\.py", "([^"]+)", "([^"]+)"', center)
        self.assertGreater(len(calls), 20)
        for menu, row in calls:
            with self.subTest(menu=menu, row=row):
                self.assertTrue(action.command(menu, row))
        for menu in re.findall(r'walkerMenu\("([^"]+)"\)', center):
            with self.subTest(walker=menu):
                self.assertTrue(any((ROOT / "elephant/menus" / f"{menu}{suffix}").is_file() for suffix in (".lua", ".toml")))


if __name__ == "__main__":
    unittest.main()
