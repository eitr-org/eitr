import contextlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eitr_boot_guard", DISTRO / "system/boot-guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class FakeReset:
    """The factory reset's helpers, acting on a directory that stands in for the Btrfs top level."""
    ROOT_SUBVOLUME = "@"
    ResetError = RuntimeError

    def __init__(self, top, boot):
        self.top, self.boot, self.commands, self.fail_snapshot = top, boot, [], False

    def layout(self):
        return {"device": "/dev/fake", "uuid": "u", "boot_uuid": "b"}

    @contextlib.contextmanager
    def top_level(self, device):
        yield self.top

    def snapshot(self, source, target, readonly=False):
        if self.fail_snapshot:
            raise subprocess.CalledProcessError(1, "btrfs")
        shutil.copytree(source, target, symlinks=True)
        (target / ".snapshots").mkdir()  # A Btrfs snapshot leaves nested subvolumes as empty directories.

    def delete(self, path):
        shutil.rmtree(path)

    def extract(self, archive, directory):
        directory.mkdir()
        with tarfile.open(archive) as tar:
            tar.extractall(directory, filter="data")

    def copy_boot(self, source, *, undo_source=None):
        if undo_source and (self.boot / "added").exists():
            (self.boot / "added").unlink()
        shutil.copytree(source, self.boot, dirs_exist_ok=True)

    def run(self, args, **kwargs):
        self.commands.append(args)
        if args[:2] == ["tar", "-C"]:
            with tarfile.open(args[4], "w") as tar:
                tar.add(self.boot, arcname=".")


class BootGuardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.top, self.boot, state = self.base / "top", self.base / "boot", self.base / "state"
        root = self.top / "@"
        (root / "etc").mkdir(parents=True)
        (root / "etc/version").write_text("after the update\n")
        snapshot = root / ".snapshots/7/snapshot"
        (snapshot / "etc").mkdir(parents=True)
        (snapshot / "etc/version").write_text("before the update\n")
        self.boot.mkdir()
        (self.boot / "vmlinuz").write_text("new kernel\n")
        archive = self.base / "archive"
        archive.mkdir()
        (self.base / "old-boot").mkdir()
        (self.base / "old-boot/vmlinuz").write_text("old kernel\n")
        with tarfile.open(archive / "boot.tar", "w") as tar:
            tar.add(self.base / "old-boot", arcname=".")
        self.archive = archive
        self.reset = FakeReset(self.top, self.boot)
        (self.base / "scratch").mkdir()
        self.boot_id = self.base / "boot-id"
        self.boot_id.write_text("initial")
        for name, value in (("BOOT_ID", self.boot_id), ("ARMED", state / "boot-guard.json"), ("NOTICE", state / "boot-guard-notice.json"),
                            ("SCRATCH", self.base / "scratch")):
            patcher = patch.object(guard, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(guard, "factory_reset", return_value=self.reset)
        patcher.start()
        self.addCleanup(patcher.stop)

    def armed(self):
        return json.loads(guard.ARMED.read_text())

    def start(self, number):
        self.boot_id.write_text(str(number))
        guard.boot()

    def test_only_eitrs_layout_is_armed_and_a_missing_archive_is_an_error(self):
        with self.assertRaises(RuntimeError):
            guard.arm("x", str(self.archive))
        with self.assertRaises(RuntimeError):
            guard.arm("7", str(self.base / "no-archive"))
        with patch.object(self.reset, "layout", side_effect=RuntimeError("not Eitr's layout")):
            self.assertFalse(guard.arm("7", str(self.archive)))
        self.assertFalse(guard.ARMED.exists())
        self.assertTrue(guard.arm("7", str(self.archive)))
        self.assertEqual(self.armed()["starts"], 0)

    def test_two_failed_starts_are_tolerated_and_the_third_restores(self):
        guard.arm("7", str(self.archive))
        self.start(1)
        self.start(2)
        self.assertEqual(self.armed()["starts"], 2)
        self.assertEqual((self.top / "@/etc/version").read_text(), "after the update\n")
        self.start(3)
        self.assertEqual((self.top / "@/etc/version").read_text(), "before the update\n")
        self.assertEqual((self.boot / "vmlinuz").read_text(), "old kernel\n", "boot files match the restored system")
        self.assertTrue((self.top / "@/.snapshots/7/snapshot").is_dir(), "the snapshot history moves along")
        self.assertEqual((self.top / guard.FAILED / "etc/version").read_text(), "after the update\n")
        notice = json.loads((self.top / "@" / str(guard.NOTICE).lstrip("/")).read_text())
        self.assertEqual((notice["snapshot"], notice["failed"], notice["cleaned"]), ("7", guard.FAILED, False))
        self.assertIn(["systemctl", "reboot", "--no-wall"], self.reset.commands)

    def test_a_record_copied_into_the_snapshot_does_not_arm_the_restored_system(self):
        stale = self.top / "@/.snapshots/7/snapshot" / str(guard.ARMED).lstrip("/")
        stale.parent.mkdir(parents=True)
        stale.write_text(json.dumps({"snapshot": "1", "boot": "x", "starts": 2}))
        guard.arm("7", str(self.archive))
        for number in range(3):
            self.start(number)
        self.assertFalse((self.top / "@" / str(guard.ARMED).lstrip("/")).exists())

    def test_a_failure_halfway_puts_everything_back(self):
        guard.arm("7", str(self.archive))
        self.reset.fail_snapshot = True
        with self.assertRaises(subprocess.CalledProcessError):
            guard.restore(self.armed())
        self.assertEqual((self.top / "@/etc/version").read_text(), "after the update\n")
        self.assertTrue((self.top / "@/.snapshots/7/snapshot").is_dir())
        self.assertFalse((self.top / guard.FAILED).exists())
        self.assertEqual((self.boot / "vmlinuz").read_text(), "new kernel\n")
        self.assertNotIn(["systemctl", "reboot", "--no-wall"], self.reset.commands)

    def test_partial_boot_copy_is_rolled_back_before_any_root_swap(self):
        guard.arm("7", str(self.archive))
        copy_boot = self.reset.copy_boot

        def partial_copy(source, *, undo_source=None):
            if undo_source is not None:
                self.assertTrue((self.top / guard.ROLLBACK / "boot.tar").exists())
                return copy_boot(source, undo_source=undo_source)
            (self.boot / "vmlinuz").write_text("truncated")
            (self.boot / "added").write_text("added")
            raise OSError("EFI full")

        with patch.object(self.reset, "copy_boot", side_effect=partial_copy), self.assertRaises(OSError):
            guard.restore(self.armed())
        self.assertEqual((self.boot / "vmlinuz").read_text(), "new kernel\n")
        self.assertFalse((self.boot / "added").exists())
        self.assertEqual((self.top / "@/etc/version").read_text(), "after the update\n")
        self.assertFalse((self.top / guard.ROLLBACK).exists())

    def test_failed_rollback_keeps_the_saved_efi_archive(self):
        guard.arm("7", str(self.archive))
        with patch.object(self.reset, "copy_boot", side_effect=OSError("EFI unavailable")), self.assertRaises(OSError):
            guard.restore(self.armed())
        self.assertTrue((self.top / guard.ROLLBACK / "boot.tar").is_file())
        self.assertNotIn(["systemctl", "reboot", "--no-wall"], self.reset.commands)

    def test_second_restore_keeps_both_failed_roots_until_healthy(self):
        guard.arm("7", str(self.archive))
        guard.restore(self.armed())
        (self.top / "@/etc/version").write_text("second failed root")
        guard.restore(self.armed())
        self.assertEqual((self.top / guard.FAILED / "etc/version").read_text(), "second failed root")
        (previous,) = self.top.glob(f"{guard.FAILED}-*")
        self.assertEqual((previous / "etc/version").read_text(), "after the update\n")
        guard.NOTICE.write_text('{"cleaned": false}')
        with patch.object(guard, "graphical_sessions", return_value={"greeter"}):
            guard.healthy(wait=0)
        self.assertFalse(list(self.top.glob(f"{guard.FAILED}*")))

    def test_a_missing_snapshot_changes_nothing(self):
        shutil.rmtree(self.top / "@/.snapshots/7")
        guard.arm("7", str(self.archive))
        with self.assertRaisesRegex(RuntimeError, "nothing was changed"):
            guard.restore(self.armed())
        self.assertEqual((self.boot / "vmlinuz").read_text(), "new kernel\n")

    def test_a_healthy_start_disarms_and_cleans_up_after_a_restore(self):
        guard.arm("7", str(self.archive))
        (self.top / guard.FAILED).mkdir()
        guard.NOTICE.write_text(json.dumps({"snapshot": "7", "restored": "now", "failed": guard.FAILED,
                                            "cleaned": False}))
        self.start(1)
        with patch.object(guard, "graphical_sessions", return_value={"greeter"}):
            guard.healthy(wait=0)
        self.assertFalse(guard.ARMED.exists())
        self.assertFalse((self.top / guard.FAILED).exists())
        self.assertTrue(json.loads(guard.NOTICE.read_text())["cleaned"])

    def test_active_display_manager_without_graphical_session_does_not_disarm(self):
        guard.arm("7", str(self.archive))
        self.start(1)
        listing = '[{"session":"tty","seat":"seat0","class":"user"}]'
        results = [subprocess.CompletedProcess([], 0, listing), subprocess.CompletedProcess([], 0, "Type=tty\nActive=yes")]
        with patch.object(guard.subprocess, "run", side_effect=results), \
                patch.object(guard.time, "sleep", side_effect=InterruptedError):
            with self.assertRaises(InterruptedError):
                guard.healthy()
        guard.boot()  # Restarting the service does not count the same boot again.
        self.assertEqual(self.armed()["starts"], 1)

    def test_login_greeter_can_confirm_readiness_without_user_login(self):
        listing = '[{"session":"greeter","seat":"seat0","class":"greeter"}]'
        results = [subprocess.CompletedProcess([], 0, listing), subprocess.CompletedProcess([], 0, "Type=x11\nActive=yes")]
        with patch.object(guard.subprocess, "run", side_effect=results):
            self.assertEqual(guard.graphical_sessions(), {"greeter"})

    def test_both_services_are_installed_and_enabled(self):
        pkgbuild = (DISTRO / "pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn('"$pkgdir/usr/lib/eitr/eitr-boot-guard"', pkgbuild)
        for unit in ("eitr-boot-guard.service", "eitr-boot-guard-healthy.service"):
            self.assertIn(unit, pkgbuild)
            self.assertIn(unit, (DISTRO / "system/configure-desktop.sh").read_text())
            self.assertIn(unit, (DISTRO / "pkg/eitr-desktop/eitr-desktop.install").read_text())
        self.assertIn("Before=display-manager.service", (DISTRO / "system/eitr-boot-guard.service").read_text())


class BootGuardNoticeTests(unittest.TestCase):
    def test_the_desktop_announces_a_restore_once(self):
        script = DISTRO.parent / "quickshell/desktop-bar/scripts/boot-guard-notice.sh"
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            helper = folder / "eitr-boot-guard"
            helper.write_text('#!/bin/sh\necho \'{"restored": "2026-10-16T10:00:00+00:00", "snapshot": "7"}\'\n')
            notify = folder / "notify-send"
            notify.write_text(f'#!/bin/sh\necho "$@" >> "{folder}/notified"\n')
            for tool in (helper, notify):
                tool.chmod(0o755)
            environment = {"PATH": f"{folder}:/usr/bin:/bin", "EITR_BOOT_GUARD": str(helper),
                           "XDG_STATE_HOME": str(folder / "state"), "HOME": str(folder)}
            for _ in range(2):
                subprocess.run(["bash", str(script)], check=True, env=environment)
            notified = (folder / "notified").read_text().splitlines()
            self.assertEqual(len(notified), 1, "a restore is announced only once")
            self.assertIn("Eitr undid the last update", notified[0])


if __name__ == "__main__":
    unittest.main()
