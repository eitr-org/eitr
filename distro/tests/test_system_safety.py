import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eitr_system", ROOT / "system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)


class SystemSafetyTests(unittest.TestCase):
    def test_auth_preserves_password_and_account_session_stack(self):
        original = "#%PAM-1.0\nauth include system-auth\naccount include system-auth\nsession include system-auth\n"
        changed = system.pam_with_method(original, "fido2")
        self.assertIn(original, changed)
        self.assertNotIn("nouserok", changed)
        self.assertNotIn("alwaysok", changed)
        self.assertEqual(system.pam_with_method(changed, "password"), original)
        self.assertEqual(system.pam_with_method(changed, "fido2"), changed)

    def test_switching_auth_replaces_only_eitr_owned_line(self):
        original = "auth include login\n"
        changed = system.pam_with_method(system.pam_with_method(original, "fido2"), "fingerprint")
        self.assertNotIn("pam_u2f", changed)
        self.assertIn("pam_fprintd", changed)
        self.assertIn(original, changed)

    def test_non_btrfs_and_separate_package_database_fail_closed(self):
        with patch.object(system, "output", return_value="ext4"):
            with self.assertRaises(RuntimeError): system.snapshot_supported()
        with patch.object(system, "output", return_value="btrfs"), \
                patch.object(system, "mount_source", side_effect=["root", "root", "root", "different"]):
            with self.assertRaises(RuntimeError): system.snapshot_supported()

    def test_snapshot_failure_never_creates_pending_record(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(system, "STATE", Path(temporary)), \
                patch.object(system, "snapshot_supported", side_effect=RuntimeError("not supported")), \
                patch.object(system, "run") as run:
            with self.assertRaises(RuntimeError): system.snapshot_pre()
            run.assert_not_called()
            self.assertFalse((Path(temporary) / "pending-upgrade.json").exists())

    def test_only_system_update_requests_snapshots(self):
        script = (ROOT.parent / "walker/scripts/actions/system/update.sh").read_text()
        protected = script.split("system)")[1].split(";;")[0]
        self.assertIn('sudo "$helper" snapshot-pre', protected)
        self.assertLess(protected.index("snapshot-pre"), protected.index("\n      full_update"))
        self.assertIn('sudo "$helper" snapshot-post', protected)
        self.assertNotIn("snapshot-pre", script.split("pacman)")[1])

    def test_auth_targets_are_narrow(self):
        self.assertEqual(system.SERVICES, ("hyprlock", "sddm", "sudo"))
        self.assertNotIn("system-auth", system.SERVICES)


class Account:
    def __init__(self, home, uid):
        self.pw_dir = str(home)
        self.pw_uid = uid


class SnapshotRecordTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)
        patcher = patch.object(system, "STATE", self.state)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_pending(self, identifier="7"):
        (self.state / "pending-upgrade.json").write_text('{"snapshot": "%s", "boot": ""}\n' % identifier)

    def test_post_records_outcome_and_clears_pending(self):
        self.write_pending()
        with patch.object(system, "run") as run:
            system.snapshot_post("failed")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--pre-number") + 1], "7")
        self.assertIn("Eitr after failed package upgrade", command)
        self.assertFalse((self.state / "pending-upgrade.json").exists())

    def test_post_without_pending_record_does_nothing(self):
        with patch.object(system, "run") as run:
            system.snapshot_post()
        run.assert_not_called()

    def test_pre_closes_stale_pending_record_before_new_snapshot(self):
        self.write_pending("3")
        calls = []
        with patch.object(system, "snapshot_supported"), \
                patch.object(system, "separate_boot_mounts", return_value=[]), \
                patch.object(system, "run", side_effect=lambda args, **_: calls.append(args)), \
                patch.object(system, "output", side_effect=lambda args: calls.append(args) or "4"), \
                patch("builtins.print"):
            system.snapshot_pre()
        posts = [call for call in calls if "post" in call]
        self.assertEqual(len(posts), 1)
        self.assertIn("Eitr after interrupted package upgrade", posts[0])
        self.assertLess(calls.index(posts[0]), next(i for i, c in enumerate(calls) if "pre" in c))
        pending = (self.state / "pending-upgrade.json").read_text()
        self.assertIn('"snapshot": "4"', pending)
        self.assertFalse(any(self.state.glob("boot-backups/*")), "no archive when /boot is in the root snapshot")

    def test_failed_boot_archive_creates_no_snapshot(self):
        with patch.object(system, "snapshot_supported"), \
                patch.object(system, "separate_boot_mounts", return_value=["/boot"]), \
                patch.object(system, "run", side_effect=lambda args, **_: (_ for _ in ()).throw(
                    system.subprocess.CalledProcessError(2, args)) if args[0] == "tar" else None), \
                patch.object(system, "output") as output:
            with self.assertRaises(system.subprocess.CalledProcessError):
                system.snapshot_pre()
        output.assert_not_called()
        self.assertFalse((self.state / "pending-upgrade.json").exists())
        self.assertEqual(list((self.state / "boot-backups").iterdir()), [])

    def test_separate_boot_is_archived_under_snapshot_number_and_pruned(self):
        archives = self.state / "boot-backups"
        for number in range(1, 12):
            (archives / str(number)).mkdir(parents=True)

        def run(args, **_):
            if args[0] == "tar":
                Path(args[4]).write_bytes(b"tar")

        with patch.object(system, "snapshot_supported"), \
                patch.object(system, "separate_boot_mounts", return_value=["/boot"]), \
                patch.object(system, "run", side_effect=run), \
                patch.object(system, "output", return_value="12"), patch("builtins.print"):
            system.snapshot_pre()
        self.assertTrue((archives / "12/boot.tar").is_file())
        remaining = sorted(int(path.name) for path in archives.iterdir())
        self.assertEqual(remaining, list(range(3, 13)))


class AuthenticationPolicyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.pam = self.root / "pam.d"
        self.pam.mkdir()
        for service in system.SERVICES:
            (self.pam / service).write_text(f"auth include {service}-original\n")
        for target, value in (("STATE", self.root / "state"), ("PAM", self.pam),
                              ("U2F_KEYS", self.root / "security/eitr/u2f_keys")):
            patcher = patch.object(system, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_u2f_authfile_is_readable_by_lockscreen_user(self):
        system.write_u2f_keys("alice", "alice:handle,key\n")
        self.assertEqual(system.U2F_KEYS.stat().st_mode & 0o777, 0o644)
        self.assertEqual(system.U2F_KEYS.parent.stat().st_mode & 0o777, 0o755)
        system.write_u2f_keys("bob", "bob:other\n")
        system.write_u2f_keys("alice", "alice:replaced\n")
        self.assertEqual(system.U2F_KEYS.read_text(), "bob:other\nalice:replaced\n")

    def test_fingerprint_follows_the_selected_method_everywhere(self):
        # The lockscreen must honor "password only", so fingerprint stays in
        # PAM rather than hyprlock's always-on native fingerprint option.
        backup, enabled = system.write_pam("fingerprint")
        self.assertEqual(enabled, system.SERVICES)
        for service in system.SERVICES:
            self.assertIn("pam_fprintd", (self.pam / service).read_text())
        hyprlock_conf = (ROOT.parent / "hypr/hyprlock.conf").read_text()
        self.assertNotRegex(hyprlock_conf, r"fingerprint \{\s*enabled = true")

    def test_failed_pam_write_restores_every_file(self):
        original = {service: (self.pam / service).read_text() for service in system.SERVICES}
        real_atomic = system.atomic
        writes = []

        def flaky(path, content, **kwargs):
            writes.append(path.name)
            if len(writes) == 2:
                raise OSError("disk full")
            real_atomic(path, content, **kwargs)

        with patch.object(system, "atomic", side_effect=flaky):
            with self.assertRaises(OSError):
                system.write_pam("fido2")
        self.assertEqual({service: (self.pam / service).read_text() for service in system.SERVICES}, original)

    def test_auth_restore_uses_named_backup_only(self):
        original = {service: (self.pam / service).read_text() for service in system.SERVICES}
        backup, _ = system.write_pam("fido2")
        self.assertIn("pam_u2f", (self.pam / "sudo").read_text())
        with patch("builtins.print"):
            system.restore_auth(backup.name)
        self.assertEqual({service: (self.pam / service).read_text() for service in system.SERVICES}, original)
        for name in ("../pam.d", "missing", "/etc"):
            with self.assertRaises(RuntimeError):
                system.restore_auth(name)

    def test_enable_auth_refuses_root_or_missing_sudo_user(self):
        for user in ("", "root"):
            with patch.dict(system.os.environ, {"SUDO_USER": user}), patch.object(system, "write_pam") as write:
                with self.assertRaises(RuntimeError):
                    system.enable_auth("fido2")
                write.assert_not_called()

    def test_fido2_registration_must_be_owned_regular_file(self):
        home = self.root / "home"
        registration = home / ".config/Yubico/u2f_keys"
        registration.parent.mkdir(parents=True)
        elsewhere = self.root / "elsewhere"
        elsewhere.write_text("alice:handle\n")
        registration.symlink_to(elsewhere)
        with self.assertRaises(OSError):
            system.read_user_u2f_keys("alice", Account(home, system.os.getuid()))
        registration.unlink()
        registration.write_text("alice:handle\n")
        with self.assertRaisesRegex(RuntimeError, "owned by the desktop user"):
            system.read_user_u2f_keys("alice", Account(home, system.os.getuid() + 1))
        self.assertEqual(system.read_user_u2f_keys("alice", Account(home, system.os.getuid())), "alice:handle\n")
        registration.write_text("mallory:handle\n")
        with self.assertRaisesRegex(RuntimeError, "Invalid"):
            system.read_user_u2f_keys("alice", Account(home, system.os.getuid()))


class BootMenuStyleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.esp = self.root / "boot"
        self.config = self.esp / "limine.conf"
        self.esp.mkdir()
        self.entries = "timeout: 5\n\n/Eitr\n    protocol: linux\n    path: boot():/vmlinuz-linux\n"
        self.config.write_text(self.entries)
        self.home = self.root / "home"
        (self.home / ".config/theme/current").mkdir(parents=True)
        self.colors = self.home / ".config/theme/current/colors.toml"
        self.colors.write_text(self.theme("#0b1015", "#d9e2e8", "#7ee0b5"))
        account = Account(self.home, system.os.getuid())
        for patcher in (patch.object(system, "detect_bootloader", return_value=("limine", {"limine": ["/boot/limine.conf"]})),
                        patch.object(system, "SYSTEM_ROOT", self.root),
                        patch.object(system, "STATE", self.root / "state"),
                        patch.object(system, "BOOT_MENU_STATE", self.root / "state/boot-menu-style.json"),
                        patch.object(system, "SECURE_BOOT_VARIABLE", self.root / "SecureBoot"),
                        patch.object(system, "output", return_value=str(self.esp)),
                        patch.object(system, "run"), patch.object(system, "in_chroot", return_value=False),
                        patch.object(system.pwd, "getpwnam", return_value=account),
                        patch.dict(system.os.environ, {"SUDO_USER": "alice"})):
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def theme(background, foreground, accent):
        colors = "".join(f'color{index} = "#{index:02x}{index:02x}{index:02x}"\n' for index in range(16))
        return f'mode = "dark"\nbackground = "{background}"\nforeground = "{foreground}"\naccent = "{accent}"\n{colors}'

    def test_style_uses_the_users_theme_and_keeps_entries(self):
        system.boot_menu_style(True)
        text = self.config.read_text()
        self.assertTrue(text.startswith(system.STYLE_BEGIN))
        self.assertTrue(text.endswith(self.entries))
        self.assertIn("interface_branding_colour: 7ee0b5\n", text)
        self.assertIn("term_foreground: d9e2e8\n", text)
        self.assertIn("backdrop: 0b1015\n", text)
        self.assertIn("term_palette: 000000;010101;020202;030303;040404;050505;060606;070707\n", text)
        self.assertTrue((self.esp / "eitr/boot-menu.png").is_file())
        self.assertEqual(system.json.loads(system.BOOT_MENU_STATE.read_text()), {"user": "alice"})
        system.run.assert_any_call(["systemctl", "enable", system.BOOT_MENU_UNIT],
                                   stdout=system.subprocess.DEVNULL, stderr=system.subprocess.DEVNULL)

    def test_refresh_follows_a_theme_change_and_skips_an_unchanged_one(self):
        system.boot_menu_style(True)
        backups = self.root / "state/boot-config-backups"
        count = len(list(backups.iterdir()))
        system.boot_menu_refresh()
        self.assertEqual(len(list(backups.iterdir())), count)
        self.colors.write_text(self.theme("#fafafa", "#202020", "#c4914f"))
        system.boot_menu_refresh()
        text = self.config.read_text()
        self.assertEqual(text.count(system.STYLE_BEGIN), 1)
        self.assertIn("interface_branding_colour: c4914f\n", text)
        self.assertTrue(text.endswith(self.entries))

    def test_unreadable_or_invalid_theme_falls_back_to_the_default(self):
        default = Path(__file__).resolve().parents[2] / "themes" / system.DEFAULT_THEME / "colors.toml"
        expected = system.theme_palette(default.read_text())
        self.colors.write_text('background = "red"\n')
        with patch.object(system, "CODE_ROOT", default.parents[2]):
            palette, source = system.boot_menu_palette("alice")
            self.assertEqual((palette, source), (expected, "the default theme"))
            self.colors.unlink()
            self.colors.symlink_to(default)
            self.assertEqual(system.boot_menu_palette("alice")[1], "the default theme")
        user_defaults = (Path(__file__).resolve().parents[1] / "user-defaults.json").read_text()
        self.assertIn(f'"themes/{system.DEFAULT_THEME}"', user_defaults)

    def test_remove_restores_the_original_config(self):
        system.boot_menu_style(True)
        system.boot_menu_style(False)
        self.assertEqual(self.config.read_text(), self.entries)
        self.assertFalse((self.esp / "eitr").exists())
        self.assertFalse(system.BOOT_MENU_STATE.exists())

    def test_refuses_other_loaders_secure_boot_and_broken_blocks(self):
        with patch.object(system, "detect_bootloader", return_value=("grub", {})), \
                self.assertRaisesRegex(RuntimeError, "needs Limine"):
            system.boot_menu_style(True)
        (self.root / "SecureBoot").write_bytes(b"\x06\x00\x00\x00\x01")
        with self.assertRaisesRegex(RuntimeError, "Secure Boot"):
            system.boot_menu_style(True)
        (self.root / "SecureBoot").unlink()
        self.config.write_text(system.STYLE_BEGIN + "\n" + self.entries)
        with self.assertRaisesRegex(RuntimeError, "unfinished"):
            system.boot_menu_style(True)
        self.assertEqual(self.config.read_text(), system.STYLE_BEGIN + "\n" + self.entries)

    def test_every_shipped_theme_has_the_colours_the_boot_menu_needs(self):
        for colors in sorted((Path(__file__).resolve().parents[2] / "themes").glob("*/colors.toml")):
            with self.subTest(theme=colors.parent.name):
                system.theme_palette(colors.read_text())

    def test_archinstall_limine_location_is_detected(self):
        config = self.root / "boot/EFI/arch-limine/limine.conf"
        config.parent.mkdir(parents=True)
        config.write_text(self.entries)
        self.config.unlink()
        self.assertEqual(system.bootloader_evidence(self.root), {"limine": ["/boot/EFI/arch-limine/limine.conf"]})
