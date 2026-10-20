import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eitr_system", DISTRO / "system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)


def manifest(name):
    path = DISTRO / "bootloader" / name
    return [line.strip() for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


class BootloaderDetectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def touch(self, *paths):
        for path in paths:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text("")

    def test_grub_from_config_or_efi_image(self):
        self.touch("boot/grub/grub.cfg")
        self.assertEqual(system.detect_bootloader(self.root)[0], "grub")
        efi_only = self.root / "efi-only"
        (efi_only / "efi/EFI/GRUB").mkdir(parents=True)
        (efi_only / "efi/EFI/GRUB/grubx64.efi").write_text("")
        name, evidence = system.detect_bootloader(efi_only)
        self.assertEqual(name, "grub")
        self.assertEqual(evidence["grub"], ["/efi/EFI/GRUB/grubx64.efi"])

    def test_limine_config_locations(self):
        for location in ("boot/limine.conf", "efi/limine/limine.conf", "boot/efi/EFI/limine/limine.conf",
                         "boot/EFI/BOOT/limine.conf"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / location).parent.mkdir(parents=True)
                (root / location).write_text("")
                self.assertEqual(system.detect_bootloader(root), ("limine", {"limine": ["/" + location]}))

    def test_systemd_boot_from_loader_conf_or_image(self):
        self.touch("efi/loader/loader.conf")
        self.assertEqual(system.detect_bootloader(self.root)[0], "systemd-boot")
        other = self.root / "image"
        (other / "boot/EFI/systemd").mkdir(parents=True)
        (other / "boot/EFI/systemd/systemd-bootx64.efi").write_text("")
        self.assertEqual(system.detect_bootloader(other)[0], "systemd-boot")

    def test_leftover_second_loader_is_ambiguous_and_empty_is_unknown(self):
        self.assertEqual(system.detect_bootloader(self.root), ("unknown", {}))
        self.touch("boot/grub/grub.cfg", "boot/loader/loader.conf")
        name, evidence = system.detect_bootloader(self.root)
        self.assertEqual(name, "ambiguous")
        self.assertEqual(set(evidence), {"grub", "systemd-boot"})


class BootSnapshotSetupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "root"
        self.state = Path(temporary.name) / "state"
        for target, value in (("SYSTEM_ROOT", self.root), ("STATE", self.state)):
            patcher = patch.object(system, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name in ("snapshot_supported", "separate_boot_mounts"):
            patcher = patch.object(system, name, return_value=[])
            patcher.start()
            self.addCleanup(patcher.stop)

    def touch(self, *paths, content=""):
        for path in paths:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(content)

    def setup(self, which=lambda name: "/usr/bin/" + name):
        calls = []
        with patch.object(system, "run", side_effect=lambda args, **_: calls.append(args)), \
                patch.object(system.shutil, "which", side_effect=which), patch("builtins.print"):
            system.setup_boot_snapshots()
        return calls

    def test_unsupported_loaders_refuse_before_changing_anything(self):
        for layout in ([], ["efi/loader/loader.conf"], ["boot/grub/grub.cfg", "boot/limine.conf"]):
            with self.subTest(layout=layout):
                for path in layout:
                    self.touch(path)
                calls = []
                with patch.object(system, "run", side_effect=lambda args, **_: calls.append(args)):
                    with self.assertRaises(RuntimeError):
                        system.setup_boot_snapshots()
                self.assertTrue(all(call[0] == "snapper" for call in calls), calls)
                self.assertFalse(self.state.exists())
                for path in layout:
                    (self.root / path).unlink()

    def test_systemd_boot_refusal_explains_why(self):
        self.touch("efi/loader/loader.conf")
        with patch.object(system, "run"):
            with self.assertRaisesRegex(RuntimeError, "systemd-boot.*cannot boot"):
                system.setup_boot_snapshots()

    def test_missing_integration_packages_refuse(self):
        self.touch("boot/grub/grub.cfg")
        with self.assertRaisesRegex(RuntimeError, "41_snapshots-btrfs"):
            self.setup()
        self.assertFalse((self.state / "boot-config-backups").exists())

    def test_grub_backs_up_regenerates_and_enables_daemon(self):
        self.touch("boot/grub/grub.cfg", content="menuentry 'Arch' {}\n")
        self.touch("etc/grub.d/41_snapshots-btrfs")
        calls = self.setup()
        self.assertIn(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"], calls)
        self.assertIn(["systemctl", "enable", "grub-btrfsd.service"], calls)
        self.assertFalse([call for call in calls if "--now" in call or "start" in call])
        backups = list(self.state.glob("boot-config-backups/*/grub.cfg"))
        self.assertEqual([path.read_text() for path in backups], ["menuentry 'Arch' {}\n"])

    def test_limine_enables_sync_without_rewriting_the_menu(self):
        self.touch("boot/limine.conf", content="/Arch Linux\n")
        self.touch("usr/lib/systemd/system/limine-snapper-sync.service")
        calls = self.setup()
        self.assertEqual([call for call in calls if call[0] != "snapper"],
                         [["systemctl", "enable", "limine-snapper-sync.service"]])
        self.assertEqual(len(list(self.state.glob("boot-config-backups/*/limine.conf"))), 1)

    def test_status_reports_enabled_integration(self):
        self.touch("boot/grub/grub.cfg", "etc/grub.d/41_snapshots-btrfs")
        with patch.object(system.shutil, "which", return_value="/usr/bin/x"), \
                patch.object(system, "unit_enabled", return_value=True) as enabled, patch("builtins.print"):
            self.assertEqual(system.boot_snapshot_status(), 0)
        enabled.assert_called_once_with("grub-btrfsd.service")
        self.touch("efi/loader/loader.conf")
        with patch("builtins.print"):
            self.assertEqual(system.boot_snapshot_status(), 1)


class BootloaderManifestTests(unittest.TestCase):
    def test_manifests_separate_official_and_aur_packages(self):
        # Verified with pacman -Si and the AUR RPC: grub-btrfs and inotify-tools
        # are in [extra]; the Limine snapshot tools are AUR-only.
        self.assertEqual(manifest("grub.txt"), ["grub-btrfs", "inotify-tools"])
        self.assertEqual(manifest("limine.txt"), ["inotify-tools"])
        self.assertEqual(manifest("limine-aur.txt"), ["limine-snapper-sync", "limine-mkinitcpio-hook"])
        self.assertFalse((DISTRO / "bootloader/systemd-boot.txt").exists())
        for loader in system.BOOT_INTEGRATIONS:
            self.assertTrue((DISTRO / "bootloader" / f"{loader}.txt").is_file(), loader)

    def test_installer_only_offers_boot_entries(self):
        installer = (DISTRO / "install.sh").read_text()
        self.assertIn('distro/bootloader/setup.sh" --offer', installer)
        self.assertNotIn("snapshots-boot-setup", installer)
        setup = (DISTRO / "bootloader/setup.sh").read_text()
        self.assertIn("Type yes", setup)
        self.assertLess(setup.index("Type yes"), setup.index("snapshots-boot-setup"))


@unittest.skipIf(os.geteuid() == 0, "Uses an unprivileged mock helper")
class BootSetupScriptTests(unittest.TestCase):
    def run_setup(self, loader, *args, env_extra=None, stdin=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "calls"
            helper = root / "eitr-system"
            helper.write_text(f'#!/bin/sh\necho "helper $*" >> "{log}"\n'
                              f'[ "$1" = bootloader-detect ] && echo {loader}\nexit 0\n')
            helper.chmod(0o755)
            binaries = root / "bin"
            binaries.mkdir()
            for name in ("sudo", "pacman", "yay"):
                body = '"$@"' if name == "sudo" else f'echo "{name} $*" >> "{log}"'
                (binaries / name).write_text(f"#!/bin/sh\n{body}\n")
                (binaries / name).chmod(0o755)
            env = dict(os.environ, EITR_SYSTEM_HELPER=str(helper),
                       PATH=str(binaries) + os.pathsep + os.environ["PATH"])
            env.pop("EITR_BOOT_SNAPSHOTS", None)
            env.update(env_extra or {})
            result = subprocess.run(["bash", str(DISTRO / "bootloader/setup.sh"), *args], env=env,
                                    input=stdin, capture_output=True, text=True)
            return result, log.read_text() if log.exists() else ""

    def test_without_a_terminal_nothing_is_installed(self):
        result, calls = self.run_setup("grub", "--offer", stdin="yes\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not configured", result.stdout)
        self.assertNotIn("pacman", calls)
        self.assertNotIn("snapshots-boot-setup", calls)

    def test_explicit_opt_in_installs_matching_manifests(self):
        result, calls = self.run_setup("limine", env_extra={"EITR_BOOT_SNAPSHOTS": "yes"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pacman -S --needed -- inotify-tools", calls)
        self.assertIn("limine-snapper-sync limine-mkinitcpio-hook", calls)
        self.assertNotIn("grub-btrfs", calls)
        self.assertTrue(calls.rstrip().endswith("helper snapshots-boot-setup"))

    def test_unsupported_loader_is_reported_not_configured(self):
        offer, calls = self.run_setup("systemd-boot", "--offer", env_extra={"EITR_BOOT_SNAPSHOTS": "yes"})
        self.assertEqual(offer.returncode, 0, offer.stderr)
        self.assertIn("snapshots-boot-status", calls)
        self.assertNotIn("snapshots-boot-setup", calls)
        direct, _ = self.run_setup("systemd-boot", env_extra={"EITR_BOOT_SNAPSHOTS": "yes"})
        self.assertEqual(direct.returncode, 1)

    def test_check_only_reports(self):
        result, calls = self.run_setup("grub", "--check", env_extra={"EITR_BOOT_SNAPSHOTS": "yes"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("grub-btrfs inotify-tools", result.stdout)
        self.assertNotIn("pacman", calls)



class SnapshotSetupTests(unittest.TestCase):
    def setup_calls(self, bus_exists, chroot=False):
        calls = []

        def fake_run(args, **kwargs):
            calls.append(list(args))
            return subprocess.CompletedProcess(args, 1 if args[-1] == "get-config" else 0)

        with patch.object(system, "snapshot_supported"), \
                patch.object(system, "in_chroot", return_value=chroot), \
                patch.object(system.Path, "exists", return_value=bus_exists), \
                patch.object(system.subprocess, "run", side_effect=fake_run):
            system.setup_snapshots()
        return calls

    def test_setup_uses_snapperd_on_a_running_system(self):
        calls = self.setup_calls(bus_exists=True)
        self.assertEqual(calls[1][:4], ["snapper", "-c", "root", "create-config"])
        self.assertEqual(calls[-1], ["systemctl", "enable", "snapper-cleanup.timer"])

    def test_installer_chroot_skips_dbus_even_with_the_live_bus_visible(self):
        for bus_exists, chroot in ((False, False), (True, True)):
            calls = self.setup_calls(bus_exists, chroot)
            snapper = [call for call in calls if call[0] == "snapper"]
            self.assertEqual(len(snapper), 3)
            self.assertTrue(all(call[1] == "--no-dbus" for call in snapper), snapper)


if __name__ == "__main__":
    unittest.main()
