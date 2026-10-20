import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
SCRIPT = HERE / "cooler-display.py"


def load():
    spec = importlib.util.spec_from_file_location("cooler_display", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoolerDisplayTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.cooler = load()

    def sensor(self, hwmon, index, label, millidegrees):
        folder = self.root / "hwmon" / hwmon
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"temp{index}_label").write_text(label + "\n")
        (folder / f"temp{index}_input").write_text(f"{millidegrees}\n")

    def test_report_puts_the_rounded_clamped_temperature_in_the_first_byte(self):
        self.assertEqual(self.cooler.report(41.6), bytes([0, 42] + [0] * 9))
        self.assertEqual(self.cooler.report(-3), bytes([0, 0] + [0] * 9))
        self.assertEqual(self.cooler.report(130), bytes([0, 99] + [0] * 9))

    def test_display_is_found_by_its_usb_id(self):
        for name, identifier in (("hidraw0", "0003:00000C45:00005004"), ("hidraw7", "0003:0000AA88:00008666")):
            device = self.root / "hidraw" / name / "device"
            device.mkdir(parents=True)
            (device / "uevent").write_text(f"DRIVER=hid-generic\nHID_ID={identifier}\n")
        self.assertEqual(self.cooler.find_display(self.root / "hidraw"), Path("/dev/hidraw7"))
        self.assertIsNone(self.cooler.find_display(self.root / "missing"))

    def test_cpu_package_sensor_is_preferred_over_cores_and_other_devices(self):
        self.sensor("hwmon1", 1, "Composite", 61000)
        self.sensor("hwmon5", 2, "Core 0", 70000)
        self.sensor("hwmon5", 1, "Package id 0", 48500)
        self.assertEqual(self.cooler.cpu_temperature(self.root / "hwmon"), 48.5)

    def test_amd_tctl_is_used_and_unknown_sensors_report_nothing(self):
        self.sensor("hwmon2", 1, "Tctl", 55250)
        self.assertEqual(self.cooler.cpu_temperature(self.root / "hwmon"), 55.25)
        empty = self.root / "empty"
        empty.mkdir()
        self.assertIsNone(self.cooler.cpu_temperature(empty))

    def test_owner_only_files_are_never_packaged(self):
        import sys
        sys.path.insert(0, str(ROOT / "distro/lib"))
        from layout import Layout
        for name in ("cooler-display.py", "cooler-display.service", "70-cooler-display.rules"):
            with self.subTest(file=name):
                self.assertFalse(Layout(ROOT).classify(f"owner/cooler-display/{name}")["runtime"])
        service = (HERE / "cooler-display.service").read_text()
        self.assertIn("ExecStart=%h/.local/bin/cooler-display run", service)
        rule = (HERE / "70-cooler-display.rules").read_text()
        self.assertIn('ATTRS{idVendor}=="aa88", ATTRS{idProduct}=="8666", TAG+="uaccess"', rule)


if __name__ == "__main__":
    unittest.main()
