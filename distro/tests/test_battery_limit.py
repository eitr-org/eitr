import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("eitr_system", ROOT / "distro/system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)


class BatteryLimitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.supplies = root / "sys/class/power_supply"
        self.supplies.mkdir(parents=True)
        self.etc = root / "etc"
        for target, value in (("POWER_SUPPLY", self.supplies),
                              ("BATTERY_LIMIT_CONFIG", self.etc / "eitr/battery-limit"),
                              ("SYSTEMD_SYSTEM", self.etc / "systemd/system")):
            patcher = patch.object(system, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.calls = []
        patcher = patch.object(system, "run", side_effect=lambda args, **_: self.calls.append(args))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("builtins.print")
        patcher.start()
        self.addCleanup(patcher.stop)

    def battery(self, name="BAT0", kind="Battery", end="100", start=None):
        path = self.supplies / name
        path.mkdir()
        (path / "type").write_text(kind + "\n")
        if end is not None:
            (path / "charge_control_end_threshold").write_text(end + "\n")
        if start is not None:
            (path / "charge_control_start_threshold").write_text(start + "\n")
        return path

    def threshold(self, battery):
        return (battery / "charge_control_end_threshold").read_text().strip()

    def test_limit_writes_threshold_and_persists_with_a_unit(self):
        battery = self.battery()
        system.battery_limit("80")
        self.assertEqual(self.threshold(battery), "80")
        self.assertEqual(system.BATTERY_LIMIT_CONFIG.read_text(), "80\n")
        unit = (system.SYSTEMD_SYSTEM / system.BATTERY_UNIT).read_text()
        self.assertIn(f"ExecStart={system.INSTALLED_HELPER} battery-limit-apply", unit)
        self.assertIn("suspend.target", unit.split("WantedBy=")[1])
        self.assertEqual(self.calls, [["systemctl", "daemon-reload"], ["systemctl", "enable", system.BATTERY_UNIT]])

    def test_apply_restores_saved_limit_after_reset(self):
        battery = self.battery()
        system.battery_limit("70")
        (battery / "charge_control_end_threshold").write_text("100\n")
        system.battery_limit_apply()
        self.assertEqual(self.threshold(battery), "70")

    def test_off_charges_fully_and_removes_persistence(self):
        battery = self.battery()
        system.battery_limit("80")
        self.calls.clear()
        system.battery_limit("off")
        self.assertEqual(self.threshold(battery), "100")
        self.assertFalse(system.BATTERY_LIMIT_CONFIG.exists())
        self.assertFalse((system.SYSTEMD_SYSTEM / system.BATTERY_UNIT).exists())
        self.assertIn(["systemctl", "disable", system.BATTERY_UNIT], self.calls)
        system.battery_limit_apply()  # Nothing saved: no error, no write.
        self.assertEqual(self.threshold(battery), "100")

    def test_desktops_and_unsupported_batteries_are_refused(self):
        self.battery("AC", kind="Mains")
        self.battery("hidpp_battery_0")
        self.battery("BAT1", end=None)
        with self.assertRaisesRegex(RuntimeError, "charge_control_end_threshold"):
            system.battery_limit("80")
        self.assertEqual(self.calls, [])
        self.assertFalse(system.BATTERY_LIMIT_CONFIG.exists())
        self.assertEqual(system.battery_limit_status(), 1)

    def test_invalid_values_are_rejected(self):
        self.battery()
        for value in ("59", "101", "", "80%", "-1", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                system.battery_limit(value)

    def test_start_threshold_conflict_changes_no_battery(self):
        first = self.battery("BAT0")
        self.battery("BAT1", start="75")
        with self.assertRaisesRegex(RuntimeError, "BAT1 starts charging at 75%"):
            system.battery_limit("70")
        self.assertEqual(self.threshold(first), "100")

    def test_every_supported_battery_is_limited(self):
        batteries = [self.battery("BAT0"), self.battery("BAT1", start="40")]
        system.battery_limit("85")
        self.assertEqual([self.threshold(battery) for battery in batteries], ["85", "85"])


if __name__ == "__main__":
    unittest.main()
