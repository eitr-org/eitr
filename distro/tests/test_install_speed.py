"""Exercise the image path without formatting disks or building an ISO."""
from contextlib import ExitStack, nullcontext
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from test_guided_install import DISK, TEMPLATE, guided

backend = guided.image_install
builder = guided.load("eitr_build_image", guided.SOURCE / "distro/payload/build-system-image.py")
COMMIT = "a" * 40


class ImageTests(unittest.TestCase):
    def medium(self, root):
        for folder in ("pool", "repo", "assets"):
            (root / folder).mkdir()
        for name in ("core", "extra", "multilib", "eitr"):
            (root / ("repo" if name == "eitr" else "pool") / (name + ".db")).touch()
        image = root / "system.sfs"
        image.write_bytes(b"test image")
        manifest = {"source_commit": COMMIT,
                    "system_image": {"format": 1, "source_commit": COMMIT,
                                     "packages": {"linux": "1", "pacman": "1", "eitr-desktop": "1"},
                                     "explicit": ["linux", "eitr-desktop"], "desktop_dependencies": [],
                                     "bytes": image.stat().st_size, "sha256": guided.system_image.sha256(image),
                                     "repositories": {"pool": [], "repo": []},
                                     "databases": guided.system_image.database_hashes(root)}}
        (root / "manifest.json").write_text(json.dumps(manifest))
        return image

    def test_rejects_bad_image_or_commit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            image = self.medium(root)
            self.assertEqual(guided.system_image.read(root, COMMIT)["source_commit"], COMMIT)
            with self.assertRaisesRegex(ValueError, "commit"):
                guided.system_image.read(root, "b" * 40)
            image.write_bytes(b"bad image!")
            with self.assertRaisesRegex(ValueError, "checksum"):
                guided.system_image.read(root, COMMIT)

    def test_missing_image_refuses_before_loading_disk_backend(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            image = self.medium(root)
            image.unlink()
            stamp = root / "distro/archinstall/source-commit"
            stamp.parent.mkdir(parents=True)
            stamp.write_text(COMMIT)
            with patch.multiple(guided, SOURCE=root, PAYLOAD=root), \
                    patch.object(guided.os, "geteuid", return_value=0), \
                    patch.object(Path, "is_mount", return_value=True), \
                    patch.object(Path, "is_dir", return_value=True), \
                    patch.object(guided.shutil, "which", return_value="/bin/tool"), \
                    patch.object(guided.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)), \
                    patch.object(backend, "reviewed_backend") as reviewed:
                with self.assertRaisesRegex(guided.GuidedInstallError, "missing or mismatched system image"):
                    guided.main()
                reviewed.assert_not_called()

    def test_generalization_preserves_package_state_and_public_keyrings(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            private = ("etc/machine-id", "etc/ssh/ssh_host_ed25519_key",
                       "etc/pacman.d/gnupg/private-keys.d/secret", "boot/initramfs-linux.img",
                       "boot/loader/random-seed", "var/lib/systemd/random-seed",
                       "var/log/pacman.log", "var/cache/pacman/pkg/archive", "root/.bash_history")
            public = ("etc/passwd", "usr/share/pacman/keyrings/eitr.gpg",
                      "var/lib/pacman/local/linux/desc", "boot/vmlinuz-linux", "etc/mkinitcpio.d/linux.preset")
            for name in (*private, *public):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            (root / "var/log/journal").mkdir()
            builder.generalize(root)
            self.assertTrue((root / "var/log/journal").is_dir())
            self.assertFalse(any((root / name).exists() for name in private))
            self.assertTrue(all((root / name).exists() for name in public))

    def test_builder_uses_reviewed_kernel_hook_and_supplements_only(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            pool = root / "pool"
            pool.mkdir()
            (pool / "mkinitcpio-1-1-any.pkg.tar.zst").touch()
            with patch.object(builder, "output", side_effect=[
                builder.image_hooks.KERNEL_COMMAND, '#!/usr/bin/env bash\n    mkinitcpio "${args[@]}"\nfi'
            ]):
                context = builder.package_hooks(root, pool)
            hooks = root / "etc/pacman.d/hooks"
            with context:
                self.assertIn("BASH_ENV=", (hooks / builder.image_hooks.KERNEL_HOOK).read_text())
                self.assertEqual((hooks / builder.image_hooks.THEME_HOOK).readlink(), Path("/dev/null"))
                self.assertEqual((hooks / "eitr-image-bash-env").read_text(), "mkinitcpio() { :; }\n")
            self.assertEqual(list(hooks.iterdir()), [])
            medium = root / "medium"
            (medium / "pool").mkdir(parents=True)
            kept = medium / "pool/steam-1-1-any.pkg.tar.zst"
            duplicate = medium / "pool/linux-1-1-any.pkg.tar.zst"
            for path in (kept, duplicate, Path(f"{duplicate}.sig")):
                path.touch()
            builder.prune(medium, {kept}, {"linux": "1-1"})
            self.assertEqual(list((medium / "pool").iterdir()), [kept])

    def test_build_generalizes_before_writing_image_and_records_final_inventory(self):
        with TemporaryDirectory() as directory:
            work = Path(directory)
            source = work / "payload"
            source.mkdir()
            self.medium(source)
            (source / "system.sfs").unlink()
            (source / "pool/pacman-1-1-x86_64.pkg.tar.zst").touch()
            medium = work / "medium"
            commands = []

            def run(*args):
                commands.append(args)
                if args[0] == "mksquashfs":
                    root, image = args[1:3]
                    self.assertFalse((root / "etc/machine-id").exists())
                    self.assertFalse((root / "etc/pacman.d/gnupg").exists())
                    self.assertFalse((root / "boot").exists())
                    self.assertTrue((root / "usr/lib/eitr/install-boot/vmlinuz-linux").is_file())
                    self.assertIn("-xattrs", args)
                    image.write_bytes(b"built system")

            def strap(root, conf, packages):
                self.assertIn("SigLevel = Required DatabaseOptional", conf.read_text())
                for name in ("etc/machine-id", "etc/pacman.d/gnupg/private", "boot/vmlinuz-linux",
                             "etc/mkinitcpio.d/linux.preset", "var/lib/pacman/local", "usr/lib/eitr"):
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if name in {"var/lib/pacman/local", "usr/lib/eitr"}:
                        path.mkdir(exist_ok=True)
                    else:
                        path.touch()
                commands.append(("strap", packages))

            with patch.multiple(builder, run=run, strap=strap, package_hooks=Mock(return_value=nullcontext()), configure=Mock(),
                                resolve=Mock(return_value=set())), patch.object(
                    builder, "output", side_effect=["linux\npacman", "[options]", "linux 1\npacman 1\neitr-desktop 1",
                                                    "linux\npacman\neitr-desktop"]):
                builder.build(source, medium, work / "staging", COMMIT)
            manifest = guided.system_image.read(medium, COMMIT)
            self.assertEqual(manifest["system_image"]["repositories"], {"pool": [], "repo": []})
            self.assertEqual(manifest["system_image"]["packages"]["eitr-desktop"], "1")
            self.assertTrue((source / "pool/pacman-1-1-x86_64.pkg.tar.zst").is_file())
            self.assertEqual([args[0] for args in commands],
                             ["pacman-key", "pacman-key", "strap", "strap", "strap", "gpgconf", "mksquashfs"])

    def test_cleanup_releases_mounts_before_luks_after_failure(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "mnt"
            mapper = Path(directory) / "root"
            with patch.object(backend, "mounted", side_effect=[False, False, True]), \
                    patch.object(backend, "run") as run:
                with self.assertRaisesRegex(ValueError, "fixture"):
                    with backend.target_mounts(target, True, mapper):
                        mapper.touch()
                        raise ValueError("fixture")
                self.assertEqual([call.args[0] for call in run.call_args_list],
                                 [["umount", "-R", target], ["cryptsetup", "close", "root"]])

    def test_offline_mount_and_config_removed_on_transaction_failure(self):
        with TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "etc/pacman.d").mkdir(parents=True)
            with patch.object(backend, "run") as run, self.assertRaisesRegex(ValueError, "fixture"):
                with backend.offline_repository(target, Path("/iso/eitr")):
                    self.assertTrue((target / backend.OFFLINE_CONF.relative_to("/")).is_file())
                    raise ValueError("fixture")
            self.assertEqual([call.args[0][0] for call in run.call_args_list], ["mount", "umount"])
            self.assertFalse((target / backend.OFFLINE_CONF.relative_to("/")).exists())
            self.assertFalse((target / backend.MEDIA.relative_to("/")).exists())

    def test_available_profile_packages_join_the_hardware_transaction(self):
        with TemporaryDirectory() as directory:
            medium = Path(directory)
            (medium / "pool").mkdir()
            file = "chromium-1-1-x86_64.pkg.tar.zst"
            (medium / "pool" / file).touch()
            chroot = Mock()
            with patch.object(backend, "offline_repository"):
                backend.install_packages(medium, medium, ["steam", "mesa", "vulkan-icd-loader"], ["chromium"],
                                         ["vulkan-icd-loader"], chroot,
                                         Mock(return_value=f"file://{backend.MEDIA}/pool/{file}"))
            self.assertEqual(chroot.call_args_list[1].args[0][-4:], ["steam", "mesa", "vulkan-icd-loader", "chromium"])
            self.assertEqual(chroot.call_args_list[2].args[0], ["pacman", "-D", "--asexplicit", "--", "vulkan-icd-loader"])


class TargetTests(unittest.TestCase):
    def test_target_writers_use_reference_fstab_hostname_user_and_keyring(self):
        # Normalized from the encrypted VM reference.
        fstab = "UUID=UUID / btrfs rw,relatime,compress=zstd:3,space_cache=v2,subvol=/@ 0 0\n"
        encrypted_hooks = ("HOOKS=(base udev autodetect microcode modconf kms keyboard keymap "
                           "consolefont block plymouth encrypt filesystems fsck)")
        with TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "etc").mkdir()
            (target / "etc/mkinitcpio.conf").write_text(f"HOOKS=({builder.HOOKS})\n")
            installer = Mock(target=target)
            installer.genfstab.side_effect = lambda: (target / "etc/fstab").write_text(
                fstab)
            installer.set_hostname.side_effect = lambda host: (target / "etc/hostname").write_text(host + "\n")
            installer.set_timezone.return_value = True
            def create_user(user):
                (target / "etc/shadow").write_text(f"{user.username}:{user.password.enc_password}:1::::::\n")
                (target / "etc/sudoers.d").mkdir()
                (target / f"etc/sudoers.d/01_{user.username}").write_text(f"{user.username} ALL=(ALL) ALL\n")

            installer.create_users.side_effect = create_user
            modules = {}
            for name, attrs in {
                "locale": {"LocaleConfiguration": SimpleNamespace(
                    parse_arg=lambda value: SimpleNamespace(kb_layout=value["kb_layout"]))},
                "users": {"Password": lambda plaintext: SimpleNamespace(enc_password="hashed"),
                          "User": lambda user, passwd, sudo: SimpleNamespace(username=user, password=passwd, sudo=sudo)}
            }.items():
                path = f"archinstall.lib.models.{name}"
                modules[path] = ModuleType(path)
                vars(modules[path]).update(attrs)
            keyring = Mock()
            config = {"hostname": "fixture", "timezone": "UTC", "locale_config": {"kb_layout": "us"}}
            with patch.dict(sys.modules, modules), patch.object(backend, "run") as run:
                backend.configure(installer, config, "alex", "private fixture password", True, keyring)
            self.assertEqual((target / "etc/hostname").read_text(), "fixture\n")
            self.assertEqual((target / "etc/fstab").read_text(), fstab)
            self.assertEqual((target / "etc/sudoers.d/00_alex").read_text(), "alex ALL=(ALL) ALL\n")
            self.assertEqual((target / "etc/mkinitcpio.conf").read_text().strip(), encrypted_hooks)
            user = installer.create_users.call_args.args[0]
            self.assertEqual((user.username, user.sudo), ("alex", True))
            self.assertNotIn("private fixture password", str(run.call_args_list))
            keyring.install.assert_called_once_with(target)

    def test_keyring_builds_from_image_keyrings_beside_extraction(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            work, target, medium = root / "work", root / "target", root / "medium"
            for folder in (work, target / "etc/pacman.d"):
                folder.mkdir(parents=True)

            def unsquash(command, **_kwargs):
                keyrings = Path(command[command.index("-d") + 1]) / backend.KEYRINGS
                keyrings.mkdir(parents=True)
                (keyrings / "eitr.gpg").touch()

            def populate(command, stdout, **_kwargs):
                gnupg = Path(command[command.index("populate") + 2])
                gnupg.mkdir()
                (gnupg / "pubring.gpg").write_text("keys")
                (gnupg / "S.gpg-agent").touch()
                stdout.write("==> Appending keys\n")
                return Mock(wait=Mock(return_value=0), poll=Mock(return_value=0))

            lines = []
            with patch.object(backend, "run", side_effect=unsquash) as run, \
                    patch.object(backend.subprocess, "Popen", side_effect=populate) as popen:
                keyring = backend.PacmanKeyring(medium, work, lines.append)
                keyring.install(target)
                with self.assertRaisesRegex(OSError, "already contains"):
                    keyring.install(target)
                keyring.close()
            self.assertEqual(run.call_args.args[0][-1], backend.KEYRINGS)
            command = popen.call_args.args[0]
            self.assertEqual(command[:4], ["unshare", "--mount", "--propagation", "private"])
            self.assertEqual(command[-2:], ["archlinux", "eitr"])
            gnupg = target / backend.GNUPG
            self.assertEqual((gnupg / "pubring.gpg").read_text(), "keys")
            self.assertFalse((gnupg / "S.gpg-agent").exists())
            self.assertEqual(lines, ["==> Appending keys\n"] * 2)

    def test_keyring_failure_stops_the_installation(self):
        with TemporaryDirectory() as directory:
            work = Path(directory)
            failed = Mock(wait=Mock(return_value=1), poll=Mock(return_value=1))
            with patch.object(backend, "run"), patch.object(backend.subprocess, "Popen", return_value=failed):
                keyring = backend.PacmanKeyring(work, work, Mock())
                with self.assertRaisesRegex(OSError, "keyring"):
                    keyring.install(work / "target")
                keyring.close()
            self.assertFalse((work / "target").exists())

    def test_limine_uses_mounted_partitions_and_reference_kernel_options(self):
        for removable in (True, False):
            with self.subTest(removable=removable), TemporaryDirectory() as directory:
                target = Path(directory)
                (target / "boot").mkdir()
                calls = []
                installer = Mock(target=target, _kernel_params=[])
                installer._add_limine_bootloader.side_effect = lambda *_args, **_kwargs: installer.pacman.strap("limine")
                backend.install_limine(installer, removable, calls.append)
                self.assertEqual(installer._kernel_params, ["quiet", "splash"])
                self.assertTrue(installer._zram_enabled)
                installer._add_limine_bootloader.assert_called_once_with(
                    installer._get_boot_partition.return_value, installer._get_efi_partition.return_value,
                    installer._get_root.return_value, bootloader_removable=removable)
                self.assertEqual(calls, [["pacman", "-Q", "limine"]])
                self.assertEqual((target / "boot/loader/random-seed").stat().st_size, 32)

    def test_stage_order_through_boot_and_reset(self):
        order = []
        choices = dict(username="alex", password="fixture", input_method="", encrypted=False,
                       timezone_detected=True, language="en_US.UTF-8")
        config = guided.build_config(TEMPLATE, DISK, encrypted=False)
        with ExitStack() as stack:
            for module, names in (
                (backend, ("prepare", "extract", "configure", "install_packages", "install_limine")),
                (guided, ("ensure_system_locale", "set_up_desktop", "restore_online_sources",
                          "schedule_mirror_ranking", "set_up_boot", "save_factory_reset_point")),
                (guided.install_boot, ("finish_boot_image",)),
            ):
                for name in names:
                    stack.enter_context(patch.object(module, name, Mock(
                        side_effect=lambda *args, name=name, **kwargs: order.append(name))))
            stack.enter_context(patch.object(backend, "package_hooks"))
            stack.enter_context(patch.object(backend, "pacman_keyring", lambda *args: (
                order.append("pacman_keyring"), nullcontext())[1]))
            stack.enter_context(patch.multiple(guided, installed_user=Mock(), hardware_packages=Mock()))
            stages = guided.installation_stages(config, choices, {"desktop_dependencies": []}, stack)
            for _, operation in stages:
                operation(Mock())
        self.assertEqual(order, ["prepare", "pacman_keyring", "extract", "configure", "ensure_system_locale", "install_packages",
                                 "set_up_desktop", "restore_online_sources", "schedule_mirror_ranking",
                                 "finish_boot_image", "install_limine", "set_up_boot", "save_factory_reset_point"])

    def test_boot_builder_checks_each_image_and_encryption(self):
        def output(command):
            if command[0] == "bash":
                return "/boot/first.img\n/boot/second.img"
            if command[1] == "-l":
                return "hooks/plymouth\nusr/share/plymouth/themes/eitr/eitr.plymouth\nhooks/encrypt"
            return "HOOKS=(base plymouth encrypt)"

        calls = []
        guided.install_boot.build_initramfs(True, calls.append, output)
        self.assertEqual(calls, [["plymouth-set-default-theme", "eitr"], ["mkinitcpio", "-P"]])
        with self.assertRaisesRegex(OSError, "encrypted root hook"):
            guided.install_boot.build_initramfs(
                True, calls.append, lambda command: output(command).replace("hooks/encrypt", ""))
