import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("factory_reset", DISTRO / "system/factory-reset.py")
reset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reset)

MOUNTS = {
    "/": {"device": "/dev/mapper/root", "fstype": "btrfs", "uuid": "fs-1", "subvolume": "/@"},
    "/home": {"device": "/dev/mapper/root", "fstype": "btrfs", "uuid": "fs-1", "subvolume": "/@home"},
    "/boot": {"device": "/dev/vda1", "fstype": "vfat", "uuid": "ABCD-1234", "subvolume": ""},
}


class FactoryResetTests(unittest.TestCase):
    def test_layout_accepts_only_the_guided_install_subvolumes(self):
        with patch.object(reset, "mount_info", side_effect=MOUNTS.get):
            self.assertEqual(reset.layout(), {"device": "/dev/mapper/root", "uuid": "fs-1", "boot_uuid": "ABCD-1234"})
        for path, change in (("/", {"subvolume": "/@root"}), ("/home", {"uuid": "fs-2"}),
                             ("/boot", {"fstype": "ext4"}), ("/", {"fstype": "ext4"})):
            mounts = dict(MOUNTS, **{path: dict(MOUNTS[path], **change)})
            with self.subTest(path=path, change=change), patch.object(reset, "mount_info", side_effect=mounts.get):
                with self.assertRaises(reset.ResetError):
                    reset.layout()

    def test_wrong_confirmation_or_mode_changes_nothing(self):
        with patch.object(reset, "run") as run, patch.object(reset, "layout") as layout:
            for mode, confirmation in (("everything", "reset my computer"), ("everything", ""),
                                       ("all", reset.CONFIRMATION)):
                with self.subTest(mode=mode, confirmation=confirmation), self.assertRaises(reset.ResetError):
                    reset.reset(mode, confirmation)
        run.assert_not_called()
        layout.assert_not_called()

    def test_restore_point_lives_outside_snapper_and_is_never_replaced(self):
        # A top-level subvolume, not inside @/.snapshots where Snapper lists and cleans up.
        self.assertNotIn("/", reset.FACTORY)
        source = (DISTRO / "system/factory-reset.py").read_text()
        self.assertIn("it is never replaced", source)
        self.assertIn('"ro", "true"', source)

    def test_login_users_are_the_accounts_with_homes(self):
        passwd = ("root:x:0:0::/root:/bin/bash\nalex:x:1000:1000::/home/alex:/usr/bin/zsh\n"
                  "svc:x:1001:1001::/home/svc:/usr/bin/nologin\nnobody:x:65534:65534::/:/usr/bin/nologin\n")
        self.assertEqual(reset.login_users(passwd), [{"name": "alex", "home": "alex"}])

    def test_restored_accounts_keep_their_current_passwords(self):
        restored = "root:!:19000::::::\nalex:$6$old:19000:0:99999:7:::\nsddm:!*:19000::::::\n"
        current = "root:!:19000::::::\nalex:$6$new:20000:0:99999:7:::\nlater:$6$x:20001::::::\n"
        self.assertEqual(reset.merged_shadow(restored, current),
                         "root:!:19000::::::\nalex:$6$new:20000:0:99999:7:::\nsddm:!*:19000::::::\n")

    def test_keep_files_moves_settings_aside_and_restores_the_originals(self):
        with tempfile.TemporaryDirectory() as directory:
            home, factory = Path(directory) / "home", Path(directory) / "factory"
            (home / "alex/.config/app").mkdir(parents=True)
            (home / "alex/.config/app/changed").write_text("new")
            (home / "alex/.ssh").mkdir()
            (home / "alex/.ssh/id_ed25519").write_text("key")
            (home / "alex/Documents").mkdir()
            (home / "alex/Documents/report.txt").write_text("keep")
            (home / "later/Pictures").mkdir(parents=True)
            (factory / "alex/.config/app").mkdir(parents=True)
            (factory / "alex/.config/app/default").write_text("original")
            (factory / "alex/.zshrc").write_text("zsh")
            (factory / "alex/Documents").mkdir()
            (factory / "sam/.config").mkdir(parents=True)
            users = [{"name": "alex", "home": "alex"}, {"name": "sam", "home": "sam"}]
            reset.keep_files(home, factory, users, "2026-10-13 09.00")
            alex = home / "alex"
            aside = alex / reset.settings_folder("2026-10-13 09.00")
            self.assertEqual((alex / "Documents/report.txt").read_text(), "keep")
            self.assertEqual((aside / ".ssh/id_ed25519").read_text(), "key")
            self.assertEqual((aside / ".config/app/changed").read_text(), "new")
            self.assertEqual(oct(aside.stat().st_mode & 0o777), "0o700")
            self.assertEqual((alex / ".config/app/default").read_text(), "original")
            self.assertFalse((alex / ".config/app/changed").exists())
            self.assertEqual((alex / ".zshrc").read_text(), "zsh")
            self.assertTrue((home / "sam/.config").is_dir())
            self.assertTrue((home / "later/Pictures").is_dir())

    def test_restored_root_gets_snapper_subvolume_passwords_and_finish_service(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "etc").mkdir()
            (root / ".snapshots").mkdir()
            (root / "etc/shadow").write_text("alex:$6$old:1::::::\n")
            os.chmod(root / "etc/shadow", 0o600)
            created = []
            with patch.object(reset, "run", side_effect=lambda args, **kwargs: (
                    created.append(args), Path(args[-1]).mkdir())):
                reset.prepare_root(root, "alex:$6$new:2::::::\n")
            self.assertEqual(created, [["btrfs", "subvolume", "create", str(root / ".snapshots")]])
            self.assertEqual((root / "etc/shadow").read_text(), "alex:$6$new:2::::::\n")
            self.assertEqual(oct((root / "etc/shadow").stat().st_mode & 0o777), "0o600")
            link = root / reset.FINISH_LINK
            self.assertEqual(os.readlink(link), "/usr/lib/systemd/system/" + reset.FINISH_UNIT)

    def test_secure_boot_blocks_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            variable = Path(directory) / "SecureBoot"
            with patch.object(reset, "SECURE_BOOT", variable):
                self.assertFalse(reset.secure_boot_enabled())
                variable.write_bytes(b"\x06\x00\x00\x00\x01")
                self.assertTrue(reset.secure_boot_enabled())
                variable.write_bytes(b"\x06\x00\x00\x00\x00")
                self.assertFalse(reset.secure_boot_enabled())

    def test_pending_reset_blocks_another_one(self):
        with tempfile.TemporaryDirectory() as directory:
            top = Path(directory)
            (top / reset.PREVIOUS).mkdir()
            with patch.object(reset, "in_chroot", return_value=False), \
                    patch.object(reset, "secure_boot_enabled", return_value=False), \
                    self.assertRaisesRegex(reset.ResetError, "has not finished"):
                reset.check_ready(top, {"uuid": "fs-1", "boot_uuid": "ABCD-1234"})

    def test_finish_service_is_packaged_and_not_enabled_by_the_installer(self):
        unit = (DISTRO / "system/eitr-factory-reset-finish.service").read_text()
        self.assertIn("ExecStart=/usr/lib/eitr/eitr-factory-reset finish", unit)
        package = (DISTRO / "pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn('"$pkgdir/usr/lib/eitr/eitr-factory-reset"', package)
        self.assertIn("eitr-factory-reset-finish.service", package)
        self.assertNotIn("eitr-factory-reset-finish", (DISTRO / "system/configure-desktop.sh").read_text())
        installer = (DISTRO / "archinstall/eitr-guided-install").read_text()
        self.assertIn('"/usr/lib/eitr/eitr-factory-reset", "capture"', installer)


if __name__ == "__main__":
    unittest.main()
