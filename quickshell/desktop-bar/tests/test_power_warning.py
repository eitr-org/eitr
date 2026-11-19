"""Tests for power-settings.py CLI helper."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "distro/lib") not in sys.path:
    sys.path.insert(0, str(ROOT / "distro/lib"))
if str(ROOT / "walker/tests") not in sys.path:
    sys.path.insert(0, str(ROOT / "walker/tests"))

from home_isolation import setUpModule, tearDownModule

SCRIPT = ROOT / "quickshell/desktop-bar/scripts/power-settings.py"
spec = importlib.util.spec_from_file_location("power_settings", SCRIPT)
power_settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power_settings)


class PowerSettingsCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.home = Path(self.temp_dir.name)
        patcher = patch.object(Path, "home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_summary_default(self):
        with patch("sys.stdout.write") as mock_write:
            output = []
            mock_write.side_effect = output.append
            code = power_settings.main(["summary"])
            self.assertEqual(code, 0)
            data = json.loads("".join(output))
            self.assertEqual(data, {"low": 10, "critical": 5})

    def test_set_levels(self):
        with patch("sys.stdout.write") as mock_write:
            output = []
            mock_write.side_effect = output.append
            code = power_settings.main(["set", "20", "10"])
            self.assertEqual(code, 0)
            data = json.loads("".join(output))
            self.assertEqual(data, {"low": 20, "critical": 10})

    def test_set_low_and_critical(self):
        power_settings.main(["set-low", "25"])
        with patch("sys.stdout.write") as mock_write:
            output = []
            mock_write.side_effect = output.append
            power_settings.main(["summary"])
            data = json.loads("".join(output))
            self.assertEqual(data, {"low": 25, "critical": 5})

        power_settings.main(["set-critical", "8"])
        with patch("sys.stdout.write") as mock_write:
            output = []
            mock_write.side_effect = output.append
            power_settings.main(["summary"])
            data = json.loads("".join(output))
            self.assertEqual(data, {"low": 25, "critical": 8})

    def test_set_invalid_levels(self):
        # critical >= low
        code = power_settings.main(["set", "10", "15"])
        self.assertEqual(code, 1)

        # out of range
        code = power_settings.main(["set", "60", "10"])
        self.assertEqual(code, 1)

    def test_reset(self):
        power_settings.main(["set", "30", "15"])
        with patch("sys.stdout.write") as mock_write:
            output = []
            mock_write.side_effect = output.append
            code = power_settings.main(["reset"])
            self.assertEqual(code, 0)
            data = json.loads("".join(output))
            self.assertEqual(data, {"low": 10, "critical": 5})


if __name__ == "__main__":
    unittest.main()
