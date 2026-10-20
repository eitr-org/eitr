import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]


def load():
    loader = importlib.machinery.SourceFileLoader("eitr_timezone", str(DISTRO / "system/eitr-timezone.py"))
    spec = importlib.util.spec_from_loader("eitr_timezone", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class TimezoneDetectionTests(unittest.TestCase):
    def setUp(self):
        self.timezone = load()

    def test_only_real_named_zones_are_accepted(self):
        self.assertEqual(self.timezone.detect(lambda url: "America/Sao_Paulo"), "America/Sao_Paulo")
        for answer in ("UTC", "Etc/UTC", "Not/AZone", "", "<html>"):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                self.timezone.detect(lambda url: answer)

    def test_a_blocked_service_falls_back_to_the_next(self):
        def fetch(url):
            if "ipinfo" in url:
                raise OSError("Could not resolve host")
            return "Asia/Tokyo"
        self.assertEqual(self.timezone.detect(fetch), "Asia/Tokyo")

    def test_detected_zone_is_applied_once_and_offline_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "timezone-automatic"
            marker.touch()
            with patch.object(self.timezone, "MARKER", marker), \
                    patch.object(self.timezone, "detect", side_effect=OSError("offline")), \
                    patch.object(self.timezone.subprocess, "run") as run:
                self.assertEqual(self.timezone.main(), 1)
                run.assert_not_called()
            self.assertTrue(marker.exists())
            with patch.object(self.timezone, "MARKER", marker), \
                    patch.object(self.timezone, "detect", return_value="Europe/Lisbon"), \
                    patch.object(self.timezone.subprocess, "run") as run:
                self.assertEqual(self.timezone.main(), 0)
            run.assert_called_once_with(["timedatectl", "set-timezone", "Europe/Lisbon"], check=True)
            self.assertFalse(marker.exists())

    def test_installer_schedules_detection_only_after_an_offline_fallback(self):
        installer = (DISTRO / "archinstall/eitr-guided-install").read_text()
        self.assertIn('[] if choices["timezone_detected"] else', installer)
        self.assertIn('chroot(["systemctl", "enable", "eitr-timezone.service"], log)', installer)
        self.assertLess(installer.index('("Scheduling timezone detection"'),
                        installer.index('("Saving the factory reset point"'))
        ui = (DISTRO / "archinstall/installer-ui.py").read_text()
        self.assertIn('"timezone_detected": timezone != "UTC"', ui)
        unit = (DISTRO / "system/eitr-timezone.service").read_text()
        self.assertIn("ConditionPathExists=/var/lib/eitr/timezone-automatic", unit)
        self.assertIn("Restart=on-failure", unit)
        package = (DISTRO / "pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn('distro/system/eitr-timezone.py "$pkgdir/usr/lib/eitr/eitr-timezone"', package)
        self.assertIn("distro/system/eitr-timezone.service", package)


if __name__ == "__main__":
    unittest.main()
