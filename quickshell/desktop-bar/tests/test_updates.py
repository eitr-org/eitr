import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bar_updates", ROOT / "scripts/updates.py")
updates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updates)


class Completed:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


class UpdatesTests(unittest.TestCase):
    def test_counts_repository_updates_and_their_download_size(self):
        def run(command, environment=None):
            if command == ["checkupdates"]:
                self.assertEqual(environment, {"CHECKUPDATES_DB": "/run/db"})
                return Completed(0, "eitr-desktop 1:0.3.0-1 -> 1:0.3.1-1\nlinux 7.2.9-1 -> 7.2.10-1\n")
            self.assertEqual(command, ["pacman", "--dbpath", "/run/db", "-Si", "eitr-desktop", "linux"])
            return Completed(0, "Name : eitr-desktop\nDownload Size   : 40.50 MiB\n"
                                "Name : linux\nDownload Size   : 512.00 KiB\n")

        with patch.object(updates, "run", side_effect=run):
            names, size = updates.repository_updates(Path("/run/db"))
        self.assertEqual(names, ["eitr-desktop", "linux"])
        self.assertEqual(size, round(40.5 * 1024 ** 2) + 512 * 1024)

    def test_no_updates_offline_or_missing_tools_report_nothing(self):
        for result in (Completed(2), Completed(1, "==> ERROR: Cannot fetch updates\n"), None):
            with self.subTest(result=result), patch.object(updates, "run", return_value=result):
                self.assertEqual(updates.repository_updates(Path("/run/db")), ([], 0))
        with patch.object(updates.shutil, "which", return_value=None):
            self.assertEqual(updates.aur_updates(), [])

    def test_aur_updates_come_from_yay(self):
        with patch.object(updates.shutil, "which", return_value="/usr/bin/yay"), \
                patch.object(updates, "run", return_value=Completed(0, "yay-bin 12.4-1 -> 12.5-1\n")):
            self.assertEqual(updates.aur_updates(), ["yay-bin"])

    def test_bar_icon_sits_between_obs_and_notifications_and_refreshes_after_updates(self):
        shell = (ROOT / "shell.qml").read_text()
        self.assertLess(shell.index("id: obsIcon"), shell.index("id: updatesIcon"))
        self.assertLess(shell.index("id: updatesIcon"), shell.index("id: notificationIcon"))
        self.assertLess(shell.index("id: verticalObsIcon"), shell.index("id: verticalUpdatesIcon"))
        self.assertLess(shell.index("id: verticalUpdatesIcon"), shell.index("id: verticalNotificationIcon"))
        update = (ROOT.parents[1] / "walker/scripts/actions/system/update.sh").read_text()
        self.assertIn("ipc call -- updates refresh", update)


if __name__ == "__main__":
    unittest.main()
