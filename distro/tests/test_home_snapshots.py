import importlib.machinery
import importlib.util
import json
import os
import pwd
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
                REAL_RUN(["cp", "-a", args[4], args[5]], check=True, **kwargs)
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

    def apply_exclusions(self):
        with home_snapshots.directory(self.home) as descriptor:
            home_snapshots.exclude_home(descriptor)

    def test_symlinked_home_ancestor_is_refused(self):
        alias = self.home.parent / "alias"
        alias.symlink_to(self.home.parent, target_is_directory=True)
        with self.assertRaises(OSError):
            with home_snapshots.directory(alias / self.home.name):
                self.fail("symlinked ancestor accepted")

    def test_symlinked_exclusion_ancestor_is_left_alone(self):
        shutil.rmtree(self.home / ".local")
        (self.home / ".local").symlink_to(self.home / "Downloads", target_is_directory=True)
        before = sorted(path.name for path in (self.home / "Downloads").iterdir())
        self.apply_exclusions()
        self.assertTrue((self.home / ".local").is_symlink())
        self.assertEqual(sorted(path.name for path in (self.home / "Downloads").iterdir()), before)

    def test_symlinked_exclusion_is_left_alone(self):
        # Downloads on another disk is common; it must neither block the run nor be followed.
        shutil.rmtree(self.home / "Downloads")
        (self.home / "Downloads").symlink_to(self.home / ".local", target_is_directory=True)
        before = sorted(path.name for path in (self.home / ".local").iterdir())
        self.apply_exclusions()
        self.assertTrue((self.home / "Downloads").is_symlink())
        self.assertEqual(sorted(path.name for path in (self.home / ".local").iterdir()), before)

    def test_dangling_staging_symlink_keeps_leftover_message(self):
        path = self.home / "Downloads"
        path.with_name("Downloads.eitr-subvolume").symlink_to(self.home / "absent")
        with self.assertRaisesRegex(RuntimeError, "left over from an earlier attempt"):
            home_snapshots.convert(path)

    def test_leftovers_prevent_recreating_missing_original(self):
        (self.home / "Downloads").rename(self.home / "Downloads.eitr-old")
        with self.assertRaisesRegex(RuntimeError, "left over from an earlier attempt"):
            self.apply_exclusions()
        self.assertFalse((self.home / "Downloads").exists())
        self.assertEqual((self.home / "Downloads.eitr-old/video.mkv").read_text(), "big file")

    def test_staging_symlink_swap_never_reaches_copy_or_chown(self):
        path = self.home / "Downloads"
        victim = self.home.parent / "victim"
        victim.write_text("unchanged")

        def swap_staging(args, **kwargs):
            if args[:3] == ["btrfs", "subvolume", "create"]:
                Path(args[3]).symlink_to(victim)
            else:
                self.fail("copy must not run after a staging symlink swap")

        with patch.object(home_snapshots, "run", side_effect=swap_staging), \
                patch.object(home_snapshots.os, "chown") as chown:
            with self.assertRaisesRegex(RuntimeError, "conversion stopped"):
                home_snapshots.convert(path)
            chown.assert_not_called()
        self.assertEqual(victim.read_text(), "unchanged")
        self.assertEqual((path / "video.mkv").read_text(), "big file")

    def test_nested_filesystem_is_refused_before_copy(self):
        original_lstat = os.lstat

        def foreign_device(path, **kwargs):
            info = original_lstat(path, **kwargs)
            if Path(path).name == "video.mkv":
                fields = list(info)
                fields[2] = -1
                return os.stat_result(fields)
            return info

        with patch.object(home_snapshots.os, "lstat", side_effect=foreign_device):
            with self.assertRaisesRegex(RuntimeError, "filesystem"):
                home_snapshots.convert(self.home / "Downloads")
        self.assertFalse((self.home / "Downloads.eitr-subvolume").exists())

    def test_failed_copy_leaves_source_and_staging_without_root_cleanup(self):
        original_run = home_snapshots.run.side_effect

        def fail_copy(args, **kwargs):
            if args[0] == "cp":
                raise subprocess.CalledProcessError(1, args)
            return original_run(args, **kwargs)

        with patch.object(home_snapshots, "run", side_effect=fail_copy) as command:
            with self.assertRaisesRegex(RuntimeError, "conversion stopped"):
                home_snapshots.convert(self.home / "Downloads")
        self.assertEqual((self.home / "Downloads/video.mkv").read_text(), "big file")
        self.assertTrue((self.home / "Downloads.eitr-subvolume").is_dir())
        self.assertFalse(any(call.args[0][:3] == ["btrfs", "subvolume", "delete"]
                             for call in command.call_args_list))

    def test_failed_publish_preserves_original_in_old_folder(self):
        original_rename = Path.rename

        def fail_publish(path, destination):
            if path.name.endswith(".eitr-subvolume"):
                raise OSError("publish failed")
            return original_rename(path, destination)

        with patch.object(Path, "rename", autospec=True, side_effect=fail_publish):
            with self.assertRaisesRegex(RuntimeError, "conversion stopped"):
                home_snapshots.convert(self.home / "Downloads")
        self.assertEqual((self.home / "Downloads.eitr-old/video.mkv").read_text(), "big file")
        self.assertTrue((self.home / "Downloads.eitr-subvolume").exists())

    def test_filesystem_boundary_is_refused(self):
        with self.assertRaisesRegex(RuntimeError, "filesystem"):
            with home_snapshots.directory(self.home, device=-1):
                self.fail("foreign filesystem accepted")

    def test_root_cannot_mutate_home(self):
        with patch.object(home_snapshots.os, "geteuid", return_value=0), \
                patch.object(home_snapshots.os, "chown") as chown, \
                patch.object(home_snapshots.os, "chmod") as chmod:
            with self.assertRaisesRegex(RuntimeError, "root"):
                home_snapshots.convert(self.home / "Downloads")
            with home_snapshots.directory(self.home) as descriptor:
                with self.assertRaisesRegex(RuntimeError, "root"):
                    home_snapshots.exclude_home(descriptor)
            chown.assert_not_called()
            chmod.assert_not_called()

    def test_child_drops_privileges_before_touching_home(self):
        events = []
        with patch.object(home_snapshots.os, "fork", return_value=0), \
                patch.object(home_snapshots.os, "_exit", side_effect=SystemExit) as terminate, \
                patch.object(home_snapshots, "drop_privileges", side_effect=lambda owner: events.append("drop")), \
                patch.object(home_snapshots, "exclude_home", side_effect=lambda descriptor: events.append("write")):
            with self.assertRaises(SystemExit):
                home_snapshots.exclude([self.home])
            terminate.assert_called_once_with(0)
        self.assertEqual(events, ["drop", "write"])
        self.assertTrue(self.pending.exists())

    def test_failed_privilege_drop_never_touches_home(self):
        with patch.object(home_snapshots.os, "fork", return_value=0), \
                patch.object(home_snapshots.os, "_exit", side_effect=SystemExit) as terminate, \
                patch.object(home_snapshots, "drop_privileges", side_effect=PermissionError("denied")), \
                patch.object(home_snapshots, "exclude_home") as worker:
            with self.assertRaises(SystemExit):
                home_snapshots.exclude([self.home])
            terminate.assert_called_once_with(1)
            worker.assert_not_called()
        self.assertTrue(self.pending.exists())

    def test_parent_waits_and_retains_pending_on_failure(self):
        for child_status in (0, 256):
            self.pending.touch()
            with patch.object(home_snapshots.os, "fork", return_value=123), \
                    patch.object(home_snapshots.os, "waitpid", return_value=(123, child_status)), \
                    patch.object(home_snapshots, "exclude_home") as worker, \
                    patch.object(home_snapshots, "drop_privileges") as drop:
                if child_status:
                    with self.assertRaisesRegex(RuntimeError, "pending setup retained"):
                        home_snapshots.exclude([self.home])
                else:
                    home_snapshots.exclude([self.home])
                worker.assert_not_called()
                drop.assert_not_called()
            self.assertEqual(self.pending.exists(), bool(child_status))

    def test_privilege_drop_sets_supplementary_groups_before_gid_and_uid(self):
        owner = self.home.stat()
        calls = []
        with patch.object(home_snapshots.os, "setgroups", side_effect=lambda groups: calls.append(("groups", groups))), \
                patch.object(home_snapshots.os, "setgid", side_effect=lambda gid: calls.append(("gid", gid))), \
                patch.object(home_snapshots.os, "setuid", side_effect=lambda uid: calls.append(("uid", uid))), \
                patch.object(home_snapshots.os, "umask"):
            home_snapshots.drop_privileges(owner)
        self.assertEqual([call[0] for call in calls], ["groups", "gid", "uid"])
        account = pwd.getpwuid(owner.st_uid)
        self.assertIn(account.pw_gid, calls[0][1])
        self.assertEqual(calls[1:], [("gid", account.pw_gid), ("uid", owner.st_uid)])

    def test_existing_folders_keep_their_files_and_become_subvolumes(self):
        self.apply_exclusions()
        self.assertEqual((self.home / "Downloads/video.mkv").read_text(), "big file")
        self.assertEqual((self.home / ".local/share/Steam/game").read_text(), "game")
        names = {path.name for path in self.subvolumes}
        self.assertTrue({"Downloads.eitr-subvolume", "Steam.eitr-subvolume"} <= names)
        self.assertFalse((self.home / "Downloads.eitr-old").exists())


    def test_caches_and_downloads_are_created_excluded_but_not_optional_folders(self):
        shutil.rmtree(self.home / "Downloads")
        self.apply_exclusions()
        self.assertTrue((self.home / ".cache").is_dir())
        self.assertTrue((self.home / "Downloads").is_dir())
        self.assertFalse((self.home / "VirtualBox VMs").exists())
        self.assertEqual((self.home / "Downloads").stat().st_mode & 0o777, 0o755)
        self.assertEqual((self.home / ".cache").stat().st_mode & 0o777, 0o700)

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
