import ast
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
GUIDED = DISTRO / "archinstall"
loader = importlib.machinery.SourceFileLoader("eitr_guided_install", str(GUIDED / "eitr-guided-install"))
spec = importlib.util.spec_from_loader("eitr_guided_install", loader)
guided = importlib.util.module_from_spec(spec)
loader.exec_module(guided)

TEMPLATE = json.loads((GUIDED / "user_configuration.json").read_text())
DISK = {"path": "/dev/test-disk", "size": 500 * 1024 ** 3, "sector_size": 4096,
        "model": "Test", "transport": "nvme", "alongside": False}
MIB_SECTORS = 1024 ** 2 // 512
# A Windows disk after shrinking C: in Disk Management: ESP, MSR, C:, recovery.
WINDOWS_TABLE = {"label": "gpt", "firstlba": 34, "lastlba": 1048575966, "partitions": [
    {"start": 2048, "size": 200 * MIB_SECTORS},
    {"start": 2048 + 200 * MIB_SECTORS, "size": 16 * MIB_SECTORS},
    {"start": 2048 + 216 * MIB_SECTORS, "size": 300 * 1024 * MIB_SECTORS},
    {"start": 1048575967 - 1024 * MIB_SECTORS, "size": 1024 * MIB_SECTORS}]}


def root_snapshot_paths():
    """The paths eitr-system's snapshots-check requires inside the root snapshot."""
    tree = ast.parse((DISTRO / "system/eitr-system.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Tuple) and all(isinstance(item, ast.Constant) for item in node.elts):
            values = [item.value for item in node.elts]
            if "/var/lib/pacman" in values:
                return values
    raise AssertionError("snapshot_supported() paths not found in eitr-system.py")


def root_partition(config):
    (device,) = config["disk_config"]["device_modifications"]
    return next(part for part in device["partitions"] if part["btrfs"])


class ConfigurationTests(unittest.TestCase):
    def test_subvolumes_keep_snapshot_paths_inside_root(self):
        subvolumes = {item["mountpoint"]: item["name"] for item in root_partition(TEMPLATE)["btrfs"]}
        self.assertEqual(subvolumes["/"], "@")
        required = [PurePosixPath(path) for path in root_snapshot_paths()]
        self.assertTrue(required)
        for mountpoint in subvolumes:
            if mountpoint == "/":
                continue
            for path in required:
                self.assertFalse(path == PurePosixPath(mountpoint) or PurePosixPath(mountpoint) in path.parents,
                                 f"{mountpoint} would split {path} out of the root snapshot")
        # Snapper's `create-config /` must create /.snapshots itself.
        self.assertIn('"create-config", "/"', (DISTRO / "system/eitr-system.py").read_text())
        self.assertNotIn("/.snapshots", subvolumes)
        self.assertEqual(set(subvolumes), {"/", "/home", "/var/log", "/var/cache/pacman/pkg"})

    def test_encrypted_btrfs_root_with_limine_on_a_fat_boot_partition(self):
        disk = TEMPLATE["disk_config"]
        (device,) = disk["device_modifications"]
        esp = next(part for part in device["partitions"] if part["mountpoint"] == "/boot")
        root = root_partition(TEMPLATE)
        self.assertEqual((esp["fs_type"], set(esp["flags"])), ("fat32", {"boot", "esp"}))
        self.assertEqual(root["fs_type"], "btrfs")
        self.assertEqual(disk["disk_encryption"]["encryption_type"], "luks")
        self.assertEqual(disk["disk_encryption"]["partitions"], [root["obj_id"]])
        # archinstall's 10-second default makes every boot wait after the passphrase.
        self.assertEqual(disk["disk_encryption"]["iter_time"], 2000)
        self.assertEqual(TEMPLATE["bootloader_config"]["bootloader"], "Limine")
        self.assertFalse(TEMPLATE["bootloader_config"]["uki"])
        self.assertNotIn("btrfs_options", disk)  # Eitr's snapshots-setup owns Snapper.

    def test_networking_audio_and_profile(self):
        services = set(TEMPLATE["services"])
        self.assertEqual(services, {"iwd", "systemd-networkd", "systemd-resolved"})
        self.assertNotIn("network_config", TEMPLATE)  # archinstall's iwd mode would also run DHCP in iwd.
        text = json.dumps(TEMPLATE).lower()
        self.assertNotIn("networkmanager", text)
        self.assertEqual(TEMPLATE["app_config"]["audio_config"]["audio"], "pipewire")
        self.assertEqual(TEMPLATE["profile_config"]["profile"]["main"], "Minimal")
        self.assertIn("multilib", TEMPLATE["mirror_config"]["optional_repositories"])
        self.assertLessEqual({"git", "python", "sudo", "iwd"}, set(TEMPLATE["packages"]))

    def test_nothing_personal_or_machine_specific_is_hardcoded(self):
        for key in ("users", "!users", "auth_config", "root_enc_password", "!root-password",
                    "encryption_password", "hostname", "locale_config", "timezone",
                    "archinstall-language", "network_config"):
            self.assertNotIn(key, TEMPLATE)
        (device,) = TEMPLATE["disk_config"]["device_modifications"]
        self.assertIsNone(device["device"])
        self.assertTrue(all(part["dev_path"] is None for part in device["partitions"]))
        disk_names = re.compile(r"/dev/(sd|hd|vd|xvd|nvme|mmcblk|disk/by-)")
        for path in (GUIDED / "user_configuration.json", GUIDED / "eitr-guided-install"):
            self.assertIsNone(disk_names.search(path.read_text()), path)


class GuidedInstallTests(unittest.TestCase):
    def test_unencrypted_choice_removes_only_encryption_configuration(self):
        config = guided.build_config(TEMPLATE, DISK, encrypted=False)
        self.assertNotIn("disk_encryption", config["disk_config"])
        self.assertEqual(root_partition(config)["fs_type"], "btrfs")
        self.assertIn("disk_encryption", TEMPLATE["disk_config"])

    def test_backend_credentials_use_inherited_pipe_not_config_or_arguments(self):
        credentials = {"encryption_password": "private-test-passphrase",
                       "users": [{"username": "alex", "!password": "private-test-password", "sudo": True}]}
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            target = work / "target"
            (target / "etc").mkdir(parents=True)
            (target / "etc/fstab").touch()

            def run(args, **kwargs):
                if args[0] == "archinstall":
                    self.assertIn("--silent", args)
                    self.assertLessEqual({"--offline", "--skip-ntp", "--skip-wkd"}, set(args))
                    self.assertNotIn("private-test-password", " ".join(args))
                    fd = kwargs["pass_fds"][0]
                    self.assertEqual(json.loads(os.read(fd, 4096)), credentials)
                    config = (work / "user_configuration.json").read_text()
                    self.assertNotIn("private-test-password", config)
                    self.assertNotIn("private-test-passphrase", config)
                return subprocess.CompletedProcess(args, 0)

            with patch.object(guided, "TARGET", target), patch.object(guided.subprocess, "run", side_effect=run):
                guided.run_archinstall(guided.build_config(TEMPLATE, DISK), credentials, work)

    def test_build_config_fills_only_the_selected_disk(self):
        config = guided.build_config(TEMPLATE, DISK)
        (device,) = config["disk_config"]["device_modifications"]
        self.assertEqual(device["device"], DISK["path"])
        esp, root = device["partitions"]
        self.assertEqual(root["start"]["value"], esp["start"]["value"] + esp["size"]["value"])
        end = root["start"]["value"] + root["size"]["value"]
        self.assertEqual(end, DISK["size"] // 1024 ** 2 - 1)
        self.assertEqual({part["start"]["sector_size"]["value"] for part in (esp, root)}, {4096})
        self.assertNotIn("eitr_comment", config)
        self.assertIsNone(TEMPLATE["disk_config"]["device_modifications"][0]["device"])

    def test_free_region_is_the_largest_whole_mib_gap(self):
        start, size = guided.free_region(WINDOWS_TABLE, 512)
        self.assertEqual(start, 1 + 216 + 300 * 1024)
        self.assertEqual(start + size, (1048575967 - 1024 * MIB_SECTORS) // MIB_SECTORS)
        empty = {"label": "gpt", "firstlba": 34, "lastlba": 1048575966, "partitions": []}
        self.assertEqual(guided.free_region(empty, 512), (1, 1048575967 // MIB_SECTORS - 1))
        full = dict(empty, partitions=[{"start": 34, "size": 1048575933}])
        self.assertEqual(guided.free_region(full, 512), (0, 0))

    def test_alongside_needs_gpt_and_enough_free_space(self):
        self.assertEqual(guided.alongside_status(WINDOWS_TABLE, (100, 40 * 1024)), (True, ""))
        self.assertIn("MBR", guided.alongside_status(dict(WINDOWS_TABLE, label="dos"), (100, 40 * 1024))[1])
        allowed, reason = guided.alongside_status(WINDOWS_TABLE, (100, 20 * 1024))
        self.assertFalse(allowed)
        self.assertIn("Shrink a partition", reason)

    def test_alongside_config_keeps_existing_partitions_and_uses_a_boot_entry(self):
        region = guided.free_region(WINDOWS_TABLE, 512)
        disk = dict(DISK, size=1048576000 * 512, sector_size=512, alongside=True, free_region=list(region))
        config = guided.build_config(TEMPLATE, disk, layout="alongside")
        (device,) = config["disk_config"]["device_modifications"]
        self.assertFalse(device["wipe"])
        self.assertEqual(config["disk_config"]["config_type"], "manual_partitioning")
        self.assertFalse(config["bootloader_config"]["removable"])
        esp, root = device["partitions"]
        self.assertEqual(esp["start"]["value"], region[0])
        self.assertEqual(root["start"]["value"], region[0] + guided.ESP_MIB)
        self.assertEqual(root["start"]["value"] + root["size"]["value"], region[0] + region[1])
        self.assertTrue(all(part["status"] == "create" for part in device["partitions"]))
        self.assertTrue(TEMPLATE["bootloader_config"]["removable"])
        self.assertTrue(TEMPLATE["disk_config"]["device_modifications"][0]["wipe"])
        with self.assertRaises(guided.GuidedInstallError):
            guided.build_config(TEMPLATE, dict(disk, alongside=False), layout="alongside")

    def test_windows_boot_managers_join_the_limine_menu(self):
        partitions = [
            {"path": "/dev/sda1", "parttype": guided.ESP_TYPE, "partuuid": "AAAA-1"},
            {"path": "/dev/sda2", "parttype": "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7", "partuuid": "aaaa-2"},
            {"path": "/dev/sdb1", "parttype": guided.ESP_TYPE.upper(), "partuuid": "bbbb-1"},
            {"path": "/dev/sdc1", "parttype": guided.ESP_TYPE, "partuuid": "cccc-1"},
            {"path": "/dev/sdd", "parttype": None, "partuuid": None}]
        checked = []

        def has_loader(path):
            checked.append(path)
            return path != "/dev/sdc1"

        entries = guided.windows_entries(partitions, "BBBB-1", has_loader)
        self.assertEqual(checked, ["/dev/sda1", "/dev/sdc1"])
        self.assertEqual(entries, ["\n/Windows\n    protocol: efi\n"
                                   "    path: guid(aaaa-1):/EFI/Microsoft/Boot/bootmgfw.efi\n"])

    def test_install_log_lists_step_times(self):
        log = guided.install_log([("Installing the base system", 61.04), ("Installing the Eitr desktop", 95.5)], 156.54)
        self.assertEqual(log, "Eitr installation step times\n   61.0 s  Installing the base system\n"
                              "   95.5 s  Installing the Eitr desktop\n  156.5 s  total\n")

    def test_boot_menu_names_eitr_and_appends_windows(self):
        config = ("timeout: 5\n\n/Arch Linux (linux)\n    protocol: linux\n"
                  "    path: boot():/vmlinuz-linux\n")
        windows = ["\n/Windows\n    protocol: efi\n    path: guid(a):/EFI/Microsoft/Boot/bootmgfw.efi\n"]
        menu = guided.boot_menu(config, windows)
        self.assertTrue(menu.startswith("timeout: 5\n\n/Eitr\n    protocol: linux\n"))
        self.assertTrue(menu.endswith(windows[0]))
        with self.assertRaises(guided.GuidedInstallError):
            guided.boot_menu("timeout: 5\n", [])

    def test_small_disks_are_rejected(self):
        with self.assertRaises(guided.GuidedInstallError):
            guided.build_config(TEMPLATE, dict(DISK, size=20 * 1024 ** 3))

    def test_candidate_disks_skip_media_read_only_and_small_devices(self):
        big = str(200 * 1024 ** 3)
        lsblk = {"blockdevices": [
            {"path": "/dev/a", "size": big, "type": "disk", "ro": False, "model": "Disk A ", "tran": "sata", "log-sec": 512},
            {"path": "/dev/live", "size": big, "type": "disk", "ro": False, "model": None, "tran": "usb", "log-sec": 512},
            {"path": "/dev/rom", "size": big, "type": "rom", "ro": False},
            {"path": "/dev/loop0", "size": big, "type": "loop", "ro": False},
            {"path": "/dev/locked", "size": big, "type": "disk", "ro": True},
            {"path": "/dev/tiny", "size": str(8 * 1024 ** 3), "type": "disk", "ro": False},
        ]}
        disks = guided.candidate_disks(lsblk, {"/dev/live"}, {})
        self.assertEqual([disk["path"] for disk in disks], ["/dev/a"])
        self.assertEqual(disks[0]["model"], "Disk A")

    def test_disk_choices_describe_size_connection_and_contents(self):
        big = str(500 * 1024 ** 3)
        lsblk = {"blockdevices": [
            {"path": "/dev/nvme0n1", "size": big, "type": "disk", "ro": False, "model": "Fast SSD",
             "tran": "nvme", "log-sec": 512, "children": [
                 {"path": "/dev/nvme0n1p1", "type": "part", "fstype": "vfat"},
                 {"path": "/dev/nvme0n1p2", "type": "part", "fstype": "ntfs"},
                 {"path": "/dev/nvme0n1p3", "type": "part", "fstype": "ntfs"},
                 {"path": "/dev/nvme0n1p4", "type": "part", "fstype": "ext4"}]},
            {"path": "/dev/sda", "size": big, "type": "disk", "ro": False, "model": None, "tran": "sata"},
        ]}
        nvme, sata = guided.candidate_disks(lsblk, set(), {"/dev/nvme0n1": dict(WINDOWS_TABLE, lastlba=500 * 1024 * 2048 - 34)})
        self.assertEqual(nvme["contents"], "4 partitions: FAT, Windows (NTFS), Linux (ext4)")
        self.assertEqual(sata["contents"], "empty")
        self.assertEqual(guided.disk_label(nvme), "/dev/nvme0n1  500.0 GiB  NVMe  Fast SSD")
        self.assertEqual(nvme["details"], ["Contents: 4 partitions: FAT, Windows (NTFS), Linux (ext4)",
                                           "Unallocated: 198.8 GiB, enough to install alongside"])
        self.assertEqual(sata["details"][1], "Unallocated: 0.0 GiB")
        self.assertFalse(sata["alongside"])
        # Without the NAME column lsblk prints a flat list and every disk looks empty.
        self.assertIn('"NAME,PATH,SIZE,TYPE,RO,MODEL,TRAN,LOG-SEC,FSTYPE"', (GUIDED / "eitr-guided-install").read_text())
        self.assertIn("no partition table", sata["alongside_reason"])
        self.assertIn("SATA  unknown model", guided.disk_label(sata))

    def test_desktop_users_are_regular_login_accounts(self):
        passwd = ("root:x:0:0::/root:/bin/bash\n"
                  "nobody:x:65534:65534:Kernel Overflow User:/:/usr/bin/nologin\n"
                  "alex:x:1000:1000::/home/alex:/bin/bash\n"
                  "svc:x:1001:1001::/home/svc:/usr/bin/nologin\n")
        self.assertEqual(guided.desktop_users(passwd),
                         [{"name": "alex", "uid": 1000, "gid": 1000, "home": "/home/alex"}])

    def test_desktop_packages_follow_hardware_detection_for_the_target(self):
        def run(args, **kwargs):
            self.assertEqual(kwargs["env"]["HARDWARE_MODULES_ROOT"], str(guided.TARGET / "usr/lib/modules"))
            self.assertEqual(kwargs["env"]["DISTRO_NVIDIA_DRIVER"], "open")
            return subprocess.CompletedProcess(args, 0, "mesa\nvulkan-radeon\nhyprland\n", "Detected GPU vendors: amd\n")

        logged = []
        with patch.dict(os.environ, {}, clear=False), patch.object(guided.subprocess, "run", side_effect=run):
            os.environ.pop("DISTRO_NVIDIA_DRIVER", None)
            packages = guided.desktop_packages(logged.append)
        self.assertEqual(logged, ["Detected GPU vendors: amd"])
        self.assertIn("vulkan-radeon", packages)
        self.assertEqual(packages.count("hyprland"), 1)
        self.assertEqual(packages[-1], "eitr-desktop")
        self.assertLess(packages.index("hyprland"), packages.index("yay"))

    def test_installed_system_switches_to_online_mirrors(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            target, medium = work / "target", work / "medium"
            (target / "etc/pacman.d").mkdir(parents=True)
            (target / "var/lib/pacman/sync").mkdir(parents=True)
            (target / "var/tmp/eitr-setup").mkdir(parents=True)
            (target / "etc/pacman.conf").write_text("[core]\nServer = file:///run/archiso/bootmnt/eitr/pool\n")
            (target / "etc/pacman.d/mirrorlist").write_text("")
            (target / "var/lib/pacman/sync/eitr.db").write_text("")
            package = work / "package"
            (package / "etc").mkdir(parents=True)
            (package / "etc/pacman.conf").write_text("[options]\n\n[core]\nInclude = /etc/pacman.d/mirrorlist\n\n"
                                                    "#[custom]\n#Server = file:///home/custompkgs\n"
                                                    "#[multilib]\n#Include = /etc/pacman.d/mirrorlist\n")
            (medium / "pool").mkdir(parents=True)
            archive = medium / "pool/pacman-7.1.0-1-x86_64.pkg.tar.gz"
            subprocess.run(["tar", "-czf", str(archive), "-C", str(package), "etc"], check=True)
            (medium / "pool/pacman-7.1.0-1-x86_64.pkg.tar.gz.sig").write_text("")
            logged = []
            with patch.object(guided, "TARGET", target), patch.object(guided, "PAYLOAD", medium), \
                    patch.object(guided, "output", side_effect=lambda args: (
                        "pacman 7.1.0-1" if args[0] == "pacman" else subprocess.check_output(args, text=True))):
                guided.restore_online_sources(logged.append)
            conf = (target / "etc/pacman.conf").read_text()
            self.assertIn("[multilib]\nInclude = /etc/pacman.d/mirrorlist", conf)
            self.assertFalse([line for line in conf.splitlines() if "file://" in line and not line.startswith("#")])
            self.assertIn("Server = https://", (target / "etc/pacman.d/mirrorlist").read_text())
            self.assertFalse((target / "var/lib/pacman/sync/eitr.db").exists())
            self.assertFalse((target / "var/tmp/eitr-setup").exists())

    def test_installation_runs_every_step_before_the_reboot(self):
        script = (GUIDED / "eitr-guided-install").read_text()
        order = ["run_archinstall(config", "install_desktop),", "set_up_desktop(installed_user",
                 "set_up_boot(choices", "restore_online_sources),", "save_factory_reset_point)]", "eitr-install.log", "ui.finished(total)",
                 '"systemctl", "poweroff"']
        positions = [script.index(item) for item in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("https://archlinux.org", script)
        self.assertNotIn(".bash_profile", script)
        self.assertNotIn("NOPASSWD", script)
        self.assertEqual(TEMPLATE["bootloader_config"]["plymouth"], "script")

    def test_build_iso_ships_the_guided_installer(self):
        script = (DISTRO / "build-iso.sh").read_text()
        self.assertIn('-map "$payload" /eitr', script)
        self.assertIn("-boot_image any replay", script)
        self.assertIn("copytoram=n", script)
        self.assertIn("s/ kms / kms plymouth /", script)
        self.assertIn("rebuild it first", script)
        self.assertEqual(guided.PAYLOAD, Path("/run/archiso/bootmnt/eitr"))
        self.assertIn("/usr/local/bin/eitr-guided-install", script)
        self.assertIn("source-version.sh", script)
        self.assertIn("file_permissions[%q]", script)


class AnsweredInstallTests(unittest.TestCase):
    """Automated VM tests answer the wizard from a file instead of the keyboard."""

    ui = guided.load("eitr_installer_ui", GUIDED / "installer-ui.py")
    disk = {**DISK, "free": 0, "alongside_reason": "no free space"}

    def choices(self, **answers):
        values = {"disk": "/dev/test-disk", "hostname": "eitr-test", "username": "tester", "password": "secret",
                  **answers}
        with tempfile.NamedTemporaryFile("w", suffix=".json") as file:
            json.dump(values, file)
            file.flush()
            with patch("builtins.print"), patch.object(guided.time, "sleep"):
                return guided.answered_choices(file.name, self.ui, [("Check", lambda: None)],
                                               lambda: [("Test disk", self.disk)])

    def test_an_answers_drive_counts_down_before_installing(self):
        printed = []
        with patch("builtins.print", side_effect=lambda *args, **kwargs: printed.append(" ".join(map(str, args)))):
            guided.confirm_unattended({"disk": self.disk, "layout": "erase", "username": "tester",
                                       "encrypted": True}, seconds=3, sleep=lambda seconds: None)
        text = "\n".join(printed)
        self.assertIn("ERASE the whole disk", text)
        self.assertIn(guided.disk_label(self.disk), text)
        self.assertIn("Starting in  1 s. Press Ctrl+C to cancel.", text)

    def test_ctrl_c_during_the_countdown_changes_nothing(self):
        def interrupt(seconds):
            raise KeyboardInterrupt
        with patch("builtins.print"), self.assertRaisesRegex(guided.GuidedInstallError, "before any disk was changed"):
            guided.confirm_unattended({"disk": self.disk, "layout": "erase", "username": "tester",
                                       "encrypted": False}, sleep=interrupt)

    def test_only_the_vm_tests_skip_the_countdown(self):
        source = (GUIDED / "eitr-guided-install").read_text()
        self.assertIn('TEST_ANSWERS = "/sys/firmware/qemu_fw_cfg/"', source)
        self.assertIn("if not str(path).startswith(TEST_ANSWERS):\n        confirm_unattended(choices)", source)
        build = (GUIDED.parent / "build-iso.sh").read_text()
        # FAT labels hold 11 characters: EITRANSWERS fits, EITR-ANSWERS only on other filesystems.
        self.assertIn("for label in EITRANSWERS EITR-ANSWERS", build)
        self.assertLessEqual(len("EITRANSWERS"), 11)
        self.assertIn("eitr-guided-install --answers /run/eitr-answers/eitr-answers.json", build)

    def test_answers_fill_the_wizard_choices(self):
        choices = self.choices(ssh_authorized_key="ssh-ed25519 KEY test")
        self.assertEqual(choices["disk"], self.disk)
        self.assertEqual((choices["layout"], choices["encrypted"], choices["keyboard"]), ("erase", False, "us"))
        self.assertEqual((choices["timezone"], choices["timezone_detected"]), ("UTC", False))
        self.assertEqual(choices["ssh_authorized_key"], "ssh-ed25519 KEY test")

    def test_answers_are_validated_like_the_wizard(self):
        for answers, message in [({"disk": "/dev/other"}, "eligible disks"), ({"username": "Root!"}, "username"),
                                 ({"hostname": "-bad"}, "hostname"), ({"password": ""}, "password"),
                                 ({"encrypted": True}, "passphrase"),
                                 ({"encrypted": True, "passphrase": "123456789012"}, "passphrase"),
                                 ({"layout": "alongside"}, "not available")]:
            with self.subTest(answers=answers), self.assertRaisesRegex(guided.GuidedInstallError, message):
                self.choices(**answers)

    def test_plain_installation_runs_every_stage_in_order(self):
        seen = []
        with patch("builtins.print") as printed:
            durations = guided.plain_installation([("First", lambda log: (seen.append(1), log("one"))),
                                                   ("Second", lambda log: seen.append(2))])
        self.assertEqual(seen, [1, 2])
        self.assertEqual([title for title, _ in durations], ["First", "Second"])
        printed.assert_any_call("one", flush=True)

    def test_ssh_is_enabled_only_when_the_answers_name_a_key(self):
        script = (GUIDED / "eitr-guided-install").read_text()
        self.assertIn('if choices.get("ssh_authorized_key") else []', script)
        self.assertIn('"systemctl", "enable", "sshd.service"', script)
        self.assertIn("plain_installation(stages) if ANSWERS else ui.installation(stages)", script)

    def test_live_iso_takes_answers_only_from_qemu_firmware_config(self):
        script = (DISTRO / "build-iso.sh").read_text()
        self.assertIn("answers=/sys/firmware/qemu_fw_cfg/by_name/opt/eitr/answers/raw", script)
        self.assertIn('eitr-guided-install --answers "$answers" 2>&1 | tee /dev/ttyS0', script)
        self.assertIn("  else\n    eitr-guided-install\n", script)


class InstallerTreeTests(unittest.TestCase):
    """The live image's copy of the repository leaves out media the payload
    package already ships, but keeps everything the installer reads."""

    def test_installer_copy_keeps_scripts_and_drops_payload_media(self):
        root = DISTRO.parent
        if subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True).returncode:
            self.skipTest("not a Git checkout")
        script = (DISTRO / "build-iso.sh").read_text()
        excludes = re.findall(r"^  '(:\(exclude,glob\)[^']+)'$", script.split("installer_excludes=(", 1)[1], re.M)
        self.assertEqual(len(excludes), 4)
        files = set(subprocess.check_output(["git", "-C", str(root), "ls-files", "--", ".", *excludes],
                                            text=True).splitlines())
        for needed in ("distro/install.sh", "distro/system/configure-desktop.sh", "distro/network/20-wifi.network",
                       "distro/archinstall/installer-ui.py", "fastfetch/eitr.py", "fastfetch/assets/eitr-wordmark.png",
                       "themes/norse/colors.toml", "HOME_FILES/.zshrc", "hypr/hyprland.lua"):
            self.assertIn(needed, files)
        self.assertFalse([name for name in files if "/backgrounds/" in name or name.endswith(".mp4")
                          or name.endswith("/preview.png") and name.startswith("themes/")])


@unittest.skipUnless(importlib.util.find_spec("archinstall"), "archinstall is not installed")
class ArchinstallParserTests(unittest.TestCase):
    """Parse the generated config with archinstall's own models (runs where archinstall exists)."""

    def setUp(self):
        # Unprivileged archinstall writes install.log into the working directory.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(directory.name)

    def test_archinstall_accepts_the_generated_layout(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from archinstall.lib.args import ArchConfig, Arguments
        from archinstall.lib.disk.device_handler import device_handler
        from archinstall.lib.models.device import SectorSize, Size, Unit

        for sector in (512, 4096):
            disk = dict(DISK, size=DISK["size"] + 12345, sector_size=sector)
            config = guided.build_config(TEMPLATE, disk)
            config["encryption_password"] = "test passphrase"
            size = SectorSize(sector, Unit.B)
            device = SimpleNamespace(device_info=SimpleNamespace(
                path=Path(disk["path"]), total_size=Size(disk["size"], Unit.B, size), sector_size=size))
            with self.subTest(sector=sector), \
                    patch.object(type(device_handler), "get_device",
                                 lambda _self, path: device if str(path) == disk["path"] else None):
                arch = ArchConfig.from_config(config, Arguments())
                (modification,) = arch.disk_config.device_modifications
                esp, root = modification.partitions
                self.assertEqual(str(esp.mountpoint), "/boot")
                self.assertEqual([str(item.mountpoint) for item in root.btrfs_subvols],
                                 ["/", "/home", "/var/log", "/var/cache/pacman/pkg"])
                self.assertEqual(arch.disk_config.disk_encryption.partitions, [root])
                self.assertEqual(arch.disk_config.disk_encryption.iter_time, 2000)
                self.assertNotIn("test passphrase", arch.user_config_to_json())

    def test_archinstall_accepts_the_alongside_layout(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from archinstall.lib.args import ArchConfig, Arguments
        from archinstall.lib.disk.device_handler import device_handler
        from archinstall.lib.models.device import DiskLayoutType, SectorSize, Size, Unit

        region = guided.free_region(WINDOWS_TABLE, 512)
        disk = dict(DISK, size=1048576000 * 512, sector_size=512, alongside=True, free_region=list(region))
        config = guided.build_config(TEMPLATE, disk, encrypted=False, layout="alongside")
        size = SectorSize(512, Unit.B)
        device = SimpleNamespace(disk=SimpleNamespace(type="gpt"), device_info=SimpleNamespace(
            path=Path(disk["path"]), total_size=Size(disk["size"], Unit.B, size), sector_size=size))
        with patch.object(type(device_handler), "get_device",
                          lambda _self, path: device if str(path) == disk["path"] else None):
            arch = ArchConfig.from_config(config, Arguments())
        self.assertEqual(arch.disk_config.config_type, DiskLayoutType.Manual)
        (modification,) = arch.disk_config.device_modifications
        self.assertFalse(modification.wipe)
        esp, root = modification.partitions
        self.assertEqual(esp.start.convert(Unit.MiB).value, region[0])
        self.assertFalse(arch.bootloader_config.removable)


if __name__ == "__main__":
    unittest.main()
