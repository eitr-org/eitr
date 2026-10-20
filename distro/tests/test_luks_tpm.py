import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("eitr_system", ROOT / "distro/system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)

DEVICE = "/dev/nvme0n1p2"
TPM_LIST = "PATH        DEVICE      DRIVER\n/dev/tpmrm0 MSFT0101:00 tpm_crb\n"


class FakeCommands:
    """Records commands and answers the read-only queries the helper makes."""

    def __init__(self, slots=("password",), luks2=True, tpm=TPM_LIST):
        self.slots, self.luks2, self.tpm = list(slots), luks2, tpm
        self.calls = []

    def subprocess_run(self, args, **_):
        self.calls.append(args)
        if args[:2] == ["cryptsetup", "isLuks"]:
            return SimpleNamespace(returncode=0 if self.luks2 else 1)
        if args == ["systemd-cryptenroll", "--tpm2-device=list"]:
            return SimpleNamespace(returncode=0 if self.tpm else 1, stdout=self.tpm or "")
        raise AssertionError(f"unexpected subprocess.run {args}")

    def output(self, args):
        self.calls.append(args)
        assert args == ["systemd-cryptenroll", DEVICE], args
        return "SLOT TYPE\n" + "".join(f"   {index} {kind}\n" for index, kind in enumerate(self.slots))

    def run(self, args, **_):
        self.calls.append(args)

    def changes(self):
        return [call for call in self.calls if call[0] == "systemd-cryptenroll" and len(call) > 2]


class LuksTpmTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.etc = Path(temporary.name)
        self.write_hooks("base systemd autodetect microcode modconf kms keyboard sd-vconsole block sd-encrypt filesystems fsck")
        patcher = patch.object(system, "MKINITCPIO_CONFIGS", (self.etc / "mkinitcpio.conf", self.etc / "mkinitcpio.conf.d"))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(system, "is_block_device", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("builtins.print")
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_hooks(self, hooks, path="mkinitcpio.conf"):
        (self.etc / path).parent.mkdir(parents=True, exist_ok=True)
        (self.etc / path).write_text(f"MODULES=()\nHOOKS=({hooks})\n")

    def act(self, function, commands):
        with patch.object(system.subprocess, "run", side_effect=commands.subprocess_run), \
                patch.object(system, "output", side_effect=commands.output), \
                patch.object(system, "run", side_effect=commands.run):
            function(DEVICE)

    def test_enroll_adds_pcr7_tpm_slot_and_keeps_passphrase(self):
        commands = FakeCommands()
        self.act(system.luks_tpm_enroll, commands)
        self.assertEqual(commands.changes(), [["systemd-cryptenroll", "--tpm2-device=auto", "--tpm2-pcrs=7", DEVICE]])
        self.assertFalse([call for call in commands.calls if any("wipe" in part for part in call)])

    def test_enroll_refusals_change_nothing(self):
        cases = {
            "not a LUKS2": FakeCommands(luks2=False),
            "No TPM2 device": FakeCommands(tpm=""),
            "already has a TPM2": FakeCommands(slots=("password", "tpm2")),
            "No passphrase or recovery": FakeCommands(slots=("fido2",)),
        }
        for message, commands in cases.items():
            with self.subTest(message=message):
                with self.assertRaisesRegex(RuntimeError, message):
                    self.act(system.luks_tpm_enroll, commands)
                self.assertEqual(commands.changes(), [])

    def test_busybox_encrypt_hook_refuses_enrollment(self):
        self.write_hooks("base udev autodetect block encrypt filesystems fsck")
        commands = FakeCommands()
        with self.assertRaisesRegex(RuntimeError, "initramfs cannot use TPM2"):
            self.act(system.luks_tpm_enroll, commands)
        self.assertEqual(commands.changes(), [])

    def test_drop_in_hooks_override_main_config(self):
        self.write_hooks("base udev block encrypt filesystems")
        self.write_hooks("base systemd block sd-encrypt filesystems", "mkinitcpio.conf.d/10-eitr.conf")
        self.assertIn("sd-encrypt", system.initramfs_hooks())

    def test_device_must_be_a_dev_block_path(self):
        for device in ("", "nvme0n1p2", "/tmp/disk.img", None):
            with self.subTest(device=device), self.assertRaises(ValueError):
                system.luks2_device(device)
        with patch.object(system, "is_block_device", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "not a block device"):
                system.luks2_device(DEVICE)

    def test_remove_wipes_only_tpm2_and_keeps_a_fallback(self):
        commands = FakeCommands(slots=("password", "tpm2"))
        self.act(system.luks_tpm_remove, commands)
        self.assertEqual(commands.changes(), [["systemd-cryptenroll", "--wipe-slot=tpm2", DEVICE]])
        lonely = FakeCommands(slots=("tpm2",))
        with self.assertRaisesRegex(RuntimeError, "No passphrase or recovery"):
            self.act(system.luks_tpm_remove, lonely)
        self.assertEqual(lonely.changes(), [])
        absent = FakeCommands()
        self.act(system.luks_tpm_remove, absent)
        self.assertEqual(absent.changes(), [])

    def test_recovery_key_is_only_printed_by_cryptenroll(self):
        commands = FakeCommands()
        self.act(system.luks_recovery_key, commands)
        self.assertEqual(commands.changes(), [["systemd-cryptenroll", "--recovery-key", DEVICE]])

    def test_installer_never_touches_luks_or_tpm(self):
        installer = (ROOT / "distro/install.sh").read_text()
        for word in ("cryptenroll", "luks-", "sbctl", "tpm2"):
            self.assertNotIn(word, installer)


if __name__ == "__main__":
    unittest.main()
