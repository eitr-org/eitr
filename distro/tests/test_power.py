"""Tests for battery warning level settings."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "distro/lib") not in sys.path:
    sys.path.insert(0, str(ROOT / "distro/lib"))
if str(ROOT / "walker/tests") not in sys.path:
    sys.path.insert(0, str(ROOT / "walker/tests"))

from home_isolation import setUpModule, tearDownModule
import eitr_power


class PowerSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.home = Path(self.temp_dir.name)
        patcher = patch.object(Path, "home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_defaults_when_missing(self):
        result = eitr_power.settings()
        self.assertEqual(result, {"low": 10, "critical": 5})

    def test_validate_levels(self):
        self.assertEqual(eitr_power.validate_levels(10, 5), (10, 5))
        self.assertEqual(eitr_power.validate_levels(50, 49), (50, 49))
        self.assertEqual(eitr_power.validate_levels(3, 2), (3, 2))

        # critical must be < low
        with self.assertRaises(ValueError):
            eitr_power.validate_levels(10, 10)
        with self.assertRaises(ValueError):
            eitr_power.validate_levels(10, 15)

        # Range 2-50
        with self.assertRaises(ValueError):
            eitr_power.validate_levels(10, 1)
        with self.assertRaises(ValueError):
            eitr_power.validate_levels(51, 10)

        # Non-integers
        with self.assertRaises(ValueError):
            eitr_power.validate_levels(10.5, 5)
        with self.assertRaises(ValueError):
            eitr_power.validate_levels("10", 5)

    def test_save_and_read_settings(self):
        saved = eitr_power.set_levels(15, 8)
        self.assertEqual(saved, {"low": 15, "critical": 8})
        self.assertEqual(eitr_power.settings(), {"low": 15, "critical": 8})

        power_file = self.home / ".config/eitr/power.json"
        self.assertTrue(power_file.is_file())
        data = json.loads(power_file.read_text())
        self.assertEqual(data.get("low"), 15)
        self.assertEqual(data.get("critical"), 8)

    def test_partial_updates(self):
        eitr_power.set_levels(20, 10)
        eitr_power.set_levels(low=25)
        self.assertEqual(eitr_power.settings(), {"low": 25, "critical": 10})
        eitr_power.set_levels(critical=7)
        self.assertEqual(eitr_power.settings(), {"low": 25, "critical": 7})

    def test_corrupt_file_falls_back_to_defaults(self):
        power_file = self.home / ".config/eitr/power.json"
        power_file.parent.mkdir(parents=True, exist_ok=True)
        power_file.write_text("{not json")
        self.assertEqual(eitr_power.settings(), {"low": 10, "critical": 5})

    def test_invalid_values_in_file_fall_back_to_defaults(self):
        power_file = self.home / ".config/eitr/power.json"
        power_file.parent.mkdir(parents=True, exist_ok=True)
        power_file.write_text(json.dumps({"low": 5, "critical": 10}))  # critical > low
        self.assertEqual(eitr_power.settings(), {"low": 10, "critical": 5})


if __name__ == "__main__":
    unittest.main()
