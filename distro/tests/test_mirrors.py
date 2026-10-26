import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("eitr_system_mirrors", ROOT / "distro/system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)


class MirrorsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.mirrorlist = self.root / "pacman.d/mirrorlist"
        self.mirrorlist.parent.mkdir()
        self.original = "".join(f"Server = {server}\n" for server in system.WORLD_MIRRORS)
        self.mirrorlist.write_text(self.original)
        self.state = self.root / "state"
        self.state.mkdir()
        for name, value in (("STATE", self.state), ("MIRRORLIST", self.mirrorlist)):
            patcher = patch.object(system, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def ranked(self, count=4):
        return "".join(f"Server = https://mirror{number}.example/$repo/os/$arch\n" for number in range(count))

    def test_arguments_are_bounded_recent_https_and_country_specific(self):
        arguments = system.reflector_arguments("BR")
        for option, value in (("--protocol", "https"), ("--age", "12"), ("--sort", "rate"),
                              ("--number", "10"), ("--country", "BR")):
            self.assertEqual(arguments[arguments.index(option) + 1], value)
        self.assertNotIn("--country", system.reflector_arguments())

    def test_timezone_country_uses_zone_table(self):
        table = self.root / "zone.tab"
        table.write_text("# comment\nBR +0 America/Test\n")
        localtime = self.root / "localtime"
        localtime.symlink_to(self.root / "zoneinfo/America/Test")
        with patch.object(system, "ZONE_TABLE", table), patch.object(system, "LOCALTIME", localtime):
            self.assertEqual(system.mirror_country(), "BR")
            table.write_text("BR,AR +0 America/Test\n")
            self.assertIsNone(system.mirror_country())

    def test_rank_backup_status_and_restore(self):
        with patch.object(system, "mirror_country", return_value="BR"), \
                patch.object(system, "run", return_value=Mock(stdout=self.ranked())) as run:
            self.assertTrue(system.mirrors_rank())
        self.assertEqual(run.call_args.kwargs["timeout"], 120)
        self.assertEqual(system.mirror_servers(self.mirrorlist.read_text())[-3:], list(system.WORLD_MIRRORS))
        status = system.mirrors_status()
        self.assertEqual(status["mirror_count"], 7)
        self.assertTrue(status["backup_available"])
        self.assertIsNotNone(status["last_ranking_time"])
        system.mirrors_restore()
        self.assertEqual(self.mirrorlist.read_text(), self.original)
        self.assertTrue(system.mirrors_status()["shipped_fallback"])
        self.assertEqual(len(list(self.mirrorlist.parent.glob("*.bak"))), 2)

    def test_country_shortage_retries_worldwide(self):
        with patch.object(system, "mirror_country", return_value="BR"), patch.object(system, "run", side_effect=[
                Mock(stdout=self.ranked(1)), Mock(stdout=self.ranked())]) as run:
            self.assertTrue(system.mirrors_rank())
        self.assertIn("--country", run.call_args_list[0].args[0])
        self.assertNotIn("--country", run.call_args_list[1].args[0])

    def test_failed_timed_out_or_empty_reflector_changes_nothing(self):
        custom = "Server = https://custom.example/$repo/os/$arch\n"
        self.mirrorlist.write_text(custom)
        for response in (Mock(stdout=""), Mock(stdout="Server = http://unsafe/$repo/os/$arch\n"),
                         subprocess.TimeoutExpired("reflector", 120), OSError("offline")):
            with self.subTest(response=response), patch.object(system, "mirror_country", return_value=None), \
                    patch.object(system, "run", side_effect=response if isinstance(response, Exception) else None,
                                 return_value=response):
                with self.assertRaises(ValueError):
                    system.mirrors_rank()
                self.assertEqual(self.mirrorlist.read_text(), custom)
                self.assertEqual(list(self.mirrorlist.parent.glob("*.bak")), [])

    def test_only_the_latest_three_backups_are_kept(self):
        with patch.object(system, "mirror_country", return_value=None), \
                patch.object(system, "run", return_value=Mock(stdout=self.ranked())):
            for _ in range(5):
                system.mirrors_rank()
        self.assertEqual(len(list(self.mirrorlist.parent.glob("mirrorlist.eitr-*.bak"))), 3)

    def test_refuses_empty_write_and_restore(self):
        with self.assertRaises(ValueError):
            system.mirrors_write("# no servers\n")
        backup = self.mirrorlist.with_name("mirrorlist.eitr-0.bak")
        backup.write_text("")
        with self.assertRaises(ValueError):
            system.mirrors_restore()
        self.assertEqual(self.mirrorlist.read_text(), self.original)

    def test_first_boot_counts_only_online_attempts(self):
        marker = self.state / "mirrors-pending"
        marker.write_text("0\n")
        with patch("urllib.request.urlopen", side_effect=OSError("offline")) as probe, \
                patch.object(system, "mirrors_rank") as rank:
            for attempt in range(5):
                system.mirrors_first_boot()
            self.assertEqual(probe.call_count, 5)
            rank.assert_not_called()
            self.assertEqual(marker.read_text(), "0\n")
        with patch("urllib.request.urlopen"), patch.object(system, "mirrors_rank", side_effect=ValueError("none")):
            for attempt in range(4):
                system.mirrors_first_boot()
            self.assertEqual(marker.read_text(), "3\n")
        marker.write_text("0\n")
        with patch("urllib.request.urlopen"), patch.object(system, "mirrors_rank", side_effect=[ValueError("none"), True]):
            system.mirrors_first_boot()
            self.assertTrue(marker.exists())
            system.mirrors_first_boot()
            self.assertFalse(marker.exists())

    def test_install_and_menu_wiring(self):
        rows = json.loads((ROOT / "elephant/menu-rows/system-maintenance.json").read_text())
        row = next(row for row in rows if row["text"] == "Choose fastest mirrors")
        self.assertIn("task-terminal.py python3", row["actions"]["open"])
        self.assertIn("system/mirrors.py", row["actions"]["open"])
        installer = (ROOT / "distro/archinstall/eitr-guided-install").read_text()
        self.assertIn('("Scheduling mirror ranking", schedule_mirror_ranking)', installer)
        self.assertIn('chroot(["systemctl", "enable", "eitr-mirrors.timer"], log)', installer)
        timer = (ROOT / "distro/system/eitr-mirrors.timer").read_text()
        self.assertIn("OnBootSec=2min", timer)
        self.assertNotIn("OnUnitActiveSec", timer)
        unit = (ROOT / "distro/system/eitr-mirrors.service").read_text()
        self.assertIn("ExecStart=/usr/lib/eitr/eitr-system mirrors-first-boot", unit)
        self.assertNotIn("Before=", unit)
        package = (ROOT / "distro/pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn("distro/system/eitr-mirrors.timer", package)
        self.assertIn("reflector", (ROOT / "distro/packages.txt").read_text().splitlines())


class MirrorTerminalTests(unittest.TestCase):
    def setUp(self):
        specification = importlib.util.spec_from_file_location(
            "mirror_terminal", ROOT / "walker/scripts/actions/system/mirrors.py")
        self.terminal = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.terminal)

    def invoke(self, answer, backup=True, arguments=None):
        with patch.object(self.terminal.subprocess, "check_output", return_value=json.dumps({"backup_available": backup})), \
                patch.object(self.terminal.subprocess, "run") as run, \
                patch.object(self.terminal, "read_line_or_escape", return_value=answer), \
                patch.object(self.terminal, "wait_for_escape"), \
                patch.object(self.terminal.sys, "argv", arguments or ["mirrors.py"]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.terminal.main()
        return run

    def test_enter_confirms_and_escape_cancels(self):
        self.invoke("").assert_called_once_with(
            ["sudo", "/usr/lib/eitr/eitr-system", "mirrors-rank"], check=True)
        self.invoke(None).assert_not_called()
        self.invoke("unexpected").assert_not_called()

    def test_restore_is_only_available_with_backup(self):
        self.invoke("restore").assert_called_once_with(
            ["sudo", "/usr/lib/eitr/eitr-system", "mirrors-restore"], check=True)
        self.invoke("restore", backup=False).assert_not_called()
        self.invoke("", backup=False, arguments=["mirrors.py", "restore"]).assert_not_called()
