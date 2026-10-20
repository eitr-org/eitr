import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
ROOT = DISTRO.parent


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


home_snapshots = load("home_snapshots", DISTRO / "system/home-snapshots.py")
REAL_RUN = subprocess.run
factory_reset = load("factory_reset_carry", DISTRO / "system/factory-reset.py")
restore_file = load("restore_file", ROOT / "walker/scripts/actions/system/restore-file.py")


class ExclusionTests(unittest.TestCase):
    """Folders become nested subvolumes; a directory named in `subvolumes` stands in for one."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name) / "alex"
        (self.home / "Downloads").mkdir(parents=True)
        (self.home / "Downloads/video.mkv").write_text("big file")
        (self.home / ".local/share/Steam").mkdir(parents=True)
        (self.home / ".local/share/Steam/game").write_text("game")
        self.subvolumes = set()
        self.pending = Path(directory.name) / "pending"
        self.pending.touch()

        def run(args, **kwargs):
            if args[:3] == ["btrfs", "subvolume", "create"]:
                Path(args[3]).mkdir()
                self.subvolumes.add(Path(args[3]))
            elif args[:3] == ["btrfs", "subvolume", "delete"]:
                shutil.rmtree(args[3])
            elif args[0] == "cp":
                REAL_RUN(["cp", "-a", args[3], args[4]], check=True)
            return subprocess.CompletedProcess(args, 0)
        for name, value in (("run", run), ("PENDING", self.pending)):
            patcher = patch.object(home_snapshots, name, value) if name == "PENDING" else \
                patch.object(home_snapshots, name, side_effect=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # A converted folder keeps its path: the staging subvolume is renamed onto it.
        patcher = patch.object(home_snapshots, "is_subvolume",
                               side_effect=lambda path: path.with_name(path.name + ".eitr-subvolume") in self.subvolumes
                               or path in self.subvolumes)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(home_snapshots.subprocess, "run", return_value=subprocess.CompletedProcess([], 0))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_existing_folders_keep_their_files_and_become_subvolumes(self):
        home_snapshots.exclude([self.home])
        self.assertEqual((self.home / "Downloads/video.mkv").read_text(), "big file")
        self.assertEqual((self.home / ".local/share/Steam/game").read_text(), "game")
        names = {path.name for path in self.subvolumes}
        self.assertTrue({"Downloads.eitr-subvolume", "Steam.eitr-subvolume"} <= names)
        self.assertFalse((self.home / "Downloads.eitr-old").exists())
        self.assertFalse(self.pending.exists(), "the start-up job runs once")

    def test_caches_and_downloads_are_created_excluded_but_not_optional_folders(self):
        shutil.rmtree(self.home / "Downloads")
        home_snapshots.exclude([self.home])
        self.assertTrue((self.home / ".cache").is_dir())
        self.assertTrue((self.home / "Downloads").is_dir())
        self.assertFalse((self.home / "VirtualBox VMs").exists())

    def test_the_policy_limits_space(self):
        policy = " ".join(home_snapshots.POLICY)
        for setting in ("TIMELINE_LIMIT_HOURLY=24", "TIMELINE_LIMIT_DAILY=7", "TIMELINE_LIMIT_MONTHLY=0",
                        "FREE_LIMIT=0.2", "SYNC_ACL=yes"):
            self.assertIn(setting, policy)


class ResetCarryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.top = Path(directory.name)
        self.old = self.top / "previous/old@home"
        self.new = self.top / "@home"
        for relative in ("alex/Downloads", "alex/.local/share/Steam", "alex/.cache", "sam/.var/data",
                         "alex/VirtualBox VMs"):
            (self.old / relative).mkdir(parents=True)
            (self.old / relative / "file").write_text(relative)
        (self.new / "alex/Downloads").mkdir(parents=True)  # The empty placeholder a snapshot leaves.
        (self.new / "alex/VirtualBox VMs").mkdir(parents=True)
        (self.new / "alex/VirtualBox VMs/other").write_text("not empty")
        listing = "\n".join(f"ID {256 + index} gen 1 top level 5 path previous/old@home/{relative}"
                            for index, relative in enumerate(["alex/.cache", "alex/.local/share/Steam",
                                                              "alex/Downloads", "alex/VirtualBox VMs", "sam/.var/data"]))
        patcher = patch.object(factory_reset, "output", return_value=listing)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_keep_my_files_carries_downloads_vms_and_games(self):
        failed = factory_reset.carry_subvolumes(self.top, self.old, self.new, [{"name": "alex", "home": "alex"}],
                                                "2026-10-16 18.00")
        self.assertEqual(failed, [])
        self.assertEqual((self.new / "alex/Downloads/file").read_text(), "alex/Downloads")
        settings = self.new / "alex/Settings before reset 2026-10-16 18.00"
        self.assertEqual((settings / ".local/share/Steam/file").read_text(), "alex/.local/share/Steam",
                         "hidden folders follow the other hidden settings")
        self.assertEqual((self.new / "alex/VirtualBox VMs (kept by reset)/file").read_text(), "alex/VirtualBox VMs",
                         "an occupied place is never overwritten")
        self.assertEqual((self.new / "sam/.var/data/file").read_text(), "sam/.var/data",
                         "accounts added later keep their layout")
        self.assertTrue((self.old / "alex/.cache").exists(), "caches stay behind and are deleted with the old home")

    def test_a_failed_carry_keeps_the_old_home_for_review(self):
        source = (DISTRO / "system/factory-reset.py").read_text()
        self.assertIn('write_state(previous, "carry-failed" if failed else "swapped")', source)
        self.assertIn('if state.get("state") != "swapped":', source)


class RestoreFileTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home_root = Path(directory.name)
        for name, value in (("HOME_ROOT", self.home_root), ("SNAPSHOTS", self.home_root / ".snapshots")):
            patcher = patch.object(restore_file, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.file = self.home_root / "alex/report.txt"
        self.file.parent.mkdir()
        self.file.write_text("today")
        for number, text in ((3, "monday"), (5, "tuesday")):
            copy = self.home_root / f".snapshots/{number}/snapshot/alex/report.txt"
            copy.parent.mkdir(parents=True)
            copy.write_text(text)
        listing = {"home": [{"number": 0}, {"number": 3, "date": "2026-10-12 09:00:00"},
                            {"number": 5, "date": "2026-10-13 09:00:00"}, {"number": 7, "date": "2026-10-14 09:00:00"}]}
        patcher = patch.object(restore_file.subprocess, "run", side_effect=self.fake_run(listing))
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def fake_run(listing):
        real = subprocess.run

        def run(args, **kwargs):
            if args[0] == "snapper":
                return subprocess.CompletedProcess(args, 0, json.dumps(listing), "")
            if args[0] == "notify-send":
                return subprocess.CompletedProcess(args, 0, "", "")
            return real(args, **kwargs)
        return run

    def test_versions_come_newest_first_and_only_where_the_file_exists(self):
        self.assertEqual([version[0] for version in restore_file.versions(self.file)], [5, 3])

    def test_a_restore_lands_beside_the_current_file(self):
        target = restore_file.restore(self.file, 3, "2026-10-12 09:00:00")
        self.assertEqual(target.name, "report (restored 2026-10-12 09.00).txt")
        self.assertEqual(target.read_text(), "monday")
        self.assertEqual(self.file.read_text(), "today", "the current file is never replaced")
        self.assertEqual(restore_file.restore(self.file, 3, "2026-10-12 09:00:00").name,
                         "report (restored 2026-10-12 09.00, 2).txt")

    def test_a_deleted_file_comes_back_in_its_place(self):
        self.file.unlink()
        self.assertEqual(restore_file.restore(self.file, 5, "2026-10-13 09:00:00"), self.file)
        self.assertEqual(self.file.read_text(), "tuesday")

    def test_the_command_line_restores_a_chosen_snapshot(self):
        self.assertEqual(restore_file.main([str(self.file), "--snapshot", "5"]), 0)
        self.assertEqual(restore_file.main([str(self.file), "--snapshot", "7"]), 1, "snapshot 7 lacks the file")


class HomeSnapshotMenuTests(unittest.TestCase):
    def test_menus_package_and_command(self):
        names = [entry["text"] for entry in {"entries": json.loads((ROOT / "elephant/menu-rows/snapshots.json").read_text())}["entries"]]
        self.assertIn("Home Folder Snapshots", names)
        self.assertIn("Restore a File or Folder", names)
        pkgbuild = (DISTRO / "pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn('"$pkgdir/usr/lib/eitr/eitr-home-snapshots"', pkgbuild)
        self.assertIn("distro/system/eitr-home-exclusions.service", pkgbuild)
        self.assertIn("Before=display-manager.service systemd-user-sessions.service",
                      (DISTRO / "system/eitr-home-exclusions.service").read_text())
        self.assertIn('"system/restore-file.py"', (DISTRO / "bin/eitr").read_text())
        self.assertIn("[y/N]", (ROOT / "walker/scripts/actions/system/home-snapshots.py").read_text())


if __name__ == "__main__":
    unittest.main()
