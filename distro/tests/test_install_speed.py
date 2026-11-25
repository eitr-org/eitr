"""Test the guided install's fast path without mounting disks or installing packages."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from test_guided_install import DISK, guided

backend = guided.install_backend
prefetch_payload = guided.prefetch_payload


class BackendTests(unittest.TestCase):
    def test_backend_file_change_disables_optimization(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)

            class Backend:
                version = "4.5"

                def locate_file(self, name):
                    return root / name

            filename = root / "archinstall" / next(iter(backend.BACKEND_FILES))
            filename.parent.mkdir(parents=True)
            filename.write_text("changed")
            with patch.object(backend, "distribution", return_value=Backend()):
                self.assertFalse(backend.reviewed_backend())

    def test_fallback_leaves_hooks_and_pacman_config_alone(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            conf = root / "pacman.conf"
            conf.write_text("[options]\n")
            with patch.object(backend, "reviewed_backend", return_value=False), patch("builtins.print"):
                with backend.deferred_hooks(root / "target", root, root, conf) as optimized:
                    self.assertFalse(optimized)
                    self.assertFalse((root / "target").exists())
                    self.assertEqual(conf.read_text(), "[options]\n")

    def test_overrides_are_removed_after_success_or_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail), TemporaryDirectory() as directory:
                root = Path(directory)
                conf = root / "pacman.conf"
                conf.write_text("[options]\n")
                target = root / "target"
                override = root / backend.KERNEL_HOOK
                override.write_text("staged")
                with patch.object(backend, "prepare_backend", return_value=override):
                    try:
                        with backend.deferred_hooks(target, root, root, conf) as optimized:
                            self.assertTrue(optimized)
                            self.assertIn(f"HookDir = {target / backend.HOOK_DIR}", conf.read_text())
                            backend.install_overrides(target, override, root / "overrides")
                            self.assertEqual((target / backend.HOOK_DIR / backend.THEME_HOOK).readlink(), Path("/dev/null"))
                            if fail:
                                raise RuntimeError("install failed")
                    except RuntimeError as error:
                        self.assertEqual(str(error), "install failed")
                    self.assertEqual(list((target / backend.HOOK_DIR).iterdir()), [])
                    self.assertEqual(conf.read_text(), "[options]\n")

    def test_early_hook_keeps_kernel_setup_and_defers_only_build(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            owned = root / "owned"
            owned.mkdir()
            override = root / "staged"
            override.touch()
            backend.install_overrides(root, override, owned)
            result = subprocess.check_output(
                ["env", f"BASH_ENV={root / backend.HOOK_DIR / backend.HOOK_ENV}", "bash", "-ec",
                 'echo "copied kernel and generated preset"; mkinitcpio -P; echo "hook finished"'],
                text=True)
            self.assertEqual(result.splitlines(), ["copied kernel and generated preset", "hook finished"])

    def test_features_are_batched_and_chroot_configuration_still_runs(self):
        calls = []

        class Pacman:
            target = Path("/unused")

            def strap(self, packages):
                calls.append(packages)

        class Installer:
            def arch_chroot(self, cmd, **kwargs):
                calls.append(cmd)

        with TemporaryDirectory() as directory:
            owned = Path(directory)
            override = owned / "staged"
            with patch.object(backend, "install_overrides") as install:
                install.side_effect = lambda *_args: (owned / backend.KERNEL_HOOK).touch()
                backend.adapt_backend(Installer, Pacman, ["zram-generator", "plymouth", "bluez"], override, owned)
                pacman, installer = Pacman(), Installer()
                pacman.strap(["base", "linux"])
                installer.arch_chroot("mkinitcpio -P", peek_output=True)
                pacman.strap("zram-generator")
                pacman.strap(["plymouth"])
                installer.arch_chroot("plymouth-set-default-theme script")
                installer.arch_chroot("mkinitcpio -P")
                pacman.strap(["bluez"])
                pacman.strap(["other"])
                install.assert_called_once()
        self.assertEqual(calls, [["base", "linux"], ["zram-generator", "plymouth", "bluez"],
                                 "plymouth-set-default-theme script", ["other"]])

    def test_verified_build_checks_each_image_and_encryption(self):
        def output(command):
            if command[0] == "bash":
                return "/boot/first.img\n/boot/second.img"
            if command[1] == "-l":
                return "hooks/plymouth\nusr/share/plymouth/themes/eitr/eitr.plymouth\nhooks/encrypt"
            return "HOOKS=(base plymouth encrypt)"

        calls = []
        backend.build_initramfs(True, calls.append, output)
        self.assertEqual(calls, [["plymouth-set-default-theme", "eitr"], ["mkinitcpio", "-P"]])
        with self.assertRaisesRegex(OSError, "encrypted root hook"):
            backend.build_initramfs(True, calls.append, lambda command: output(command).replace("hooks/encrypt", ""))

    def test_install_stage_builds_before_styling_and_capture(self):
        with TemporaryDirectory() as directory:
            work = Path(directory)
            target = work / "target"
            order = []
            choices = dict(disk=DISK, encrypted=False, layout="erase", hostname="eitr", timezone="UTC",
                           timezone_detected=True, keyboard="us", language="en_US.UTF-8", username="eitr",
                           password="fixture")
            (target / "var/log").mkdir(parents=True)

            def record(name):
                def operation(*args, **kwargs):
                    order.append(name)
                return operation

            def build_output(command):
                if command[2] == "bash":
                    return "/boot/initramfs-linux.img"
                if command[3] == "-l":
                    return "hooks/plymouth\nusr/share/plymouth/themes/eitr/eitr.plymouth"
                return "HOOKS=(base plymouth)"

            with patch.multiple(guided, TARGET=target, ANSWERS="fixture.json", PROFILE=None,
                                answered_choices=lambda *_args: choices, use_payload=lambda: None,
                                run_archinstall=record("base"), ensure_system_locale=record("locale"),
                                install_desktop=record("desktop packages"), installed_user=lambda name: {"name": name},
                                set_up_desktop=record("desktop setup"), restore_online_sources=record("sources"),
                                schedule_mirror_ranking=record("mirrors"), set_up_boot=record("menu"),
                                save_factory_reset_point=record("capture"), output=build_output,
                                chroot=lambda command, _log: order.append(command)):
                with patch.object(backend, "reviewed_backend", return_value=False), patch.object(
                    guided.tempfile, "TemporaryDirectory", return_value=TemporaryDirectory(dir=work)
                ), patch.object(guided.os, "geteuid", return_value=0), patch.object(
                    Path, "is_mount", return_value=True
                ), patch.object(Path, "is_dir", return_value=True), patch.object(
                    guided.shutil, "which", return_value="/fake"
                ), patch.object(guided.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)), patch.object(
                    prefetch_payload.subprocess, "Popen", side_effect=OSError
                ), patch("builtins.print"):
                    guided.main()
            self.assertEqual(order, ["base", "locale", "desktop packages", "desktop setup", "sources", "mirrors",
                                     ["plymouth-set-default-theme", "eitr"], ["mkinitcpio", "-P"], "menu", "capture"])
            self.assertIn("Building the boot image", (target / "var/log/eitr-install.log").read_text())


class PrefetchTests(unittest.TestCase):
    def test_low_budget_reads_only_base_packages_that_fit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            pool = root / "pool"
            pool.mkdir()
            base = pool / "base-1-any.pkg.tar.zst"
            linux = pool / "linux-1-any.pkg.tar.zst"
            desktop = pool / "desktop-1-any.pkg.tar.zst"
            for path, size in ((base, 3), (linux, 5), (desktop, 1)):
                path.write_bytes(b"0" * size)
            opened = []
            original_open = Path.open

            def open_file(path, *args, **kwargs):
                opened.append(path)
                return original_open(path, *args, **kwargs)

            with patch.object(prefetch_payload, "BLOCK", 1), patch.object(
                prefetch_payload, "memory_available", return_value=prefetch_payload.RESERVE + 4
            ), patch.object(prefetch_payload, "base_files", return_value={base, linux}), patch.object(
                Path, "open", open_file
            ):
                prefetch_payload.prefetch(root, Path("transactions"))
            self.assertEqual(opened, [base])


if __name__ == "__main__":
    unittest.main()
