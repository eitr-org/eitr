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
        shell = (ROOT / "BarHorizontalStatus.qml").read_text() + (ROOT / "BarWindow.qml").read_text() + (ROOT / "BarVerticalStatus.qml").read_text()
        self.assertLess(shell.index("id: obsIcon"), shell.index("id: updatesIcon"))
        self.assertLess(shell.index("id: updatesIcon"), shell.index("id: notificationIcon"))
        self.assertLess(shell.index("id: verticalObsIcon"), shell.index("id: verticalUpdatesIcon"))
        self.assertLess(shell.index("id: verticalUpdatesIcon"), shell.index("id: verticalNotificationIcon"))
        update = (ROOT.parents[1] / "walker/scripts/actions/system/update.sh").read_text()
        self.assertIn("ipc call -- updates refresh", update)


if __name__ == "__main__":
    unittest.main()


class BrokerUpdateResultsTests(unittest.TestCase):
    def test_offline_and_unknown_failure_are_not_successful_zero(self):
        offline = Completed(1)
        offline.stderr = 'Could not resolve host: mirror.example'
        for result, expected in ((Completed(2), 'ready'), (offline, 'offline'), (None, 'unavailable')):
            with self.subTest(expected=expected), patch.object(updates, 'run', return_value=result), \
                    patch.object(updates.shutil, 'which', return_value=None):
                data = updates.UpdatesDomain().read('updates.status')
                self.assertEqual(data['state'], expected)
                if expected == 'ready':
                    self.assertEqual(data['count'], 0)
                else:
                    self.assertNotIn('count', data)

    def test_command_timeout_retains_deadline_and_cli_fallback(self):
        with patch.object(updates.subprocess, 'run', side_effect=updates.subprocess.TimeoutExpired('checkupdates', 120)) as execute:
            self.assertIsNone(updates.run(['checkupdates']))
            self.assertEqual(execute.call_args.kwargs['timeout'], 120)
        with patch.object(updates, 'run', return_value=None):
            self.assertEqual(updates.repository_updates(Path('/run/private-db')), ([], 0))
            with self.assertRaises(RuntimeError):
                updates.repository_updates(Path('/run/private-db'), strict=True)

    def test_failed_size_or_aur_read_is_unavailable(self):
        with patch.object(updates, 'run', side_effect=[Completed(0, 'linux 1 -> 2'), None]):
            self.assertEqual(updates.UpdatesDomain().read('updates.status'), {'state': 'unavailable'})
        with patch.object(updates, 'run', side_effect=[Completed(2), None]), \
                patch.object(updates.shutil, 'which', return_value='/usr/bin/yay'):
            self.assertEqual(updates.UpdatesDomain().read('updates.status'), {'state': 'unavailable'})

    def test_unreadable_success_is_not_zero(self):
        with patch.object(updates, 'run', return_value=Completed(0, 'unreadable output')):
            self.assertEqual(updates.UpdatesDomain().read('updates.status'), {'state': 'unavailable'})

    def test_no_aur_upgrades_preserves_repository_updates(self):
        commands = [Completed(0, 'eitr-desktop 1 -> 2\nlinux 1 -> 2\nmesa 1 -> 2\n'),
                    Completed(0, 'Download Size : 8527667 B\n'), Completed(1)]
        with patch.object(updates, 'run', side_effect=commands), \
                patch.object(updates.shutil, 'which', return_value='/usr/bin/yay'):
            self.assertEqual(updates.UpdatesDomain().read('updates.status'),
                             {'state': 'ready', 'count': 3, 'repository': 3, 'aur': 0,
                              'downloadBytes': 8527667})

    def test_aur_exit_one_with_diagnostic_remains_failure(self):
        for diagnostic in ('Could not resolve host: aur.archlinux.org', 'invalid configuration'):
            result = Completed(1)
            result.stderr = diagnostic
            with self.subTest(diagnostic=diagnostic), patch.object(updates, 'run', return_value=result), \
                    patch.object(updates.shutil, 'which', return_value='/usr/bin/yay'):
                with self.assertRaises(RuntimeError):
                    updates.aur_updates(strict=True)
