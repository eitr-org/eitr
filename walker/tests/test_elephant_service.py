import configparser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ElephantServiceTests(unittest.TestCase):
    def test_restart_preserves_menu_children(self):
        unit = configparser.ConfigParser(interpolation=None)
        unit.read(ROOT / "systemd/user/elephant.service")
        self.assertEqual(unit["Service"]["KillMode"], "process")
        self.assertTrue(unit["Service"]["ExecStart"].endswith(" /usr/bin/elephant"))

    def test_startup_uses_single_service(self):
        config = (ROOT / "hypr/hyprland.lua").read_text()
        self.assertIn('hl.exec_cmd("systemctl --user start elephant.service")', config)
        self.assertNotIn('hl.exec_cmd("elephant")', config)


if __name__ == "__main__":
    unittest.main()
