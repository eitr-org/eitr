import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("security", ROOT / "walker/scripts/actions/system/security.py")
security = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security)


class FidoEnrollmentTests(unittest.TestCase):
    def enroll(self, home, output):
        with patch.object(security.getpass, "getuser", return_value="alice"), \
                patch.object(security.Path, "home", return_value=home), \
                patch.object(security.subprocess, "run", return_value=SimpleNamespace(stdout=output)), \
                patch("builtins.print"):
            security.fido_enroll()
        return (home / ".config/Yubico/u2f_keys").read_text()

    def test_new_key_is_merged_and_duplicate_is_not_repeated(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(self.enroll(home, "alice:handle1,key1,es256,+presence\n"),
                             "alice:handle1,key1,es256,+presence\n")
            merged = self.enroll(home, "alice:handle2,key2,es256,+presence\n")
            self.assertEqual(merged, "alice:handle1,key1,es256,+presence:handle2,key2,es256,+presence\n")
            self.assertEqual(self.enroll(home, "alice:handle2,key2,es256,+presence\n"), merged)
            self.assertEqual((home / ".config/Yubico/u2f_keys").stat().st_mode & 0o777, 0o600)

    def test_foreign_or_malformed_registrations_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with self.assertRaises(ValueError):
                self.enroll(home, "mallory:handle,key\n")
            path = home / ".config/Yubico/u2f_keys"
            path.write_text("bob:handle,key\n")
            with self.assertRaisesRegex(ValueError, "manual review"):
                self.enroll(home, "alice:handle,key\n")
            self.assertEqual(path.read_text(), "bob:handle,key\n")


class PolicyConfirmationTests(unittest.TestCase):
    def test_policy_changes_require_typed_enable(self):
        with tempfile.NamedTemporaryFile() as helper:
            for answer, expected_calls in (("enable", 0), ("", 0), ("ENABLE", 1)):
                with self.subTest(answer=answer), patch.object(security, "ROOT_HELPERS", ("/nonexistent/eitr-system", helper.name)), \
                        patch("builtins.input", return_value=answer), patch("builtins.print"), \
                        patch.object(security.subprocess, "run") as run:
                    security.main("enable-fido2")
                    self.assertEqual(run.call_count, expected_calls)
                    if expected_calls:
                        run.assert_called_once_with(["sudo", helper.name, "auth-enable", "fido2"], check=True)

    def test_missing_root_helper_never_prompts(self):
        with patch.object(security, "ROOT_HELPERS", ("/nonexistent/eitr-system",)), \
                patch("builtins.input") as prompt, patch.object(security.subprocess, "run") as run:
            with self.assertRaises(RuntimeError):
                security.main("password-only")
            prompt.assert_not_called()
            run.assert_not_called()

    def test_packaged_helper_is_preferred_over_manual_install(self):
        self.assertEqual(security.ROOT_HELPERS[0], "/usr/lib/eitr/eitr-system")
        self.assertIn("/usr/local/lib/eitr/eitr-system", security.ROOT_HELPERS)

class TpmUnlockTests(unittest.TestCase):
    LSBLK = SimpleNamespace(stdout="/dev/nvme0n1\n/dev/nvme0n1p1 vfat\n/dev/nvme0n1p2 crypto_LUKS\n")

    def run_tpm(self, action, answers):
        with tempfile.NamedTemporaryFile() as helper, patch.object(security, "ROOT_HELPERS", (helper.name,)), \
                patch("builtins.input", side_effect=answers), patch("builtins.print"), \
                patch.object(security.subprocess, "run", return_value=self.LSBLK) as run:
            security.main(action)
        commands = [call.args[0] for call in run.call_args_list]
        return [command[2:] for command in commands if command[0] == "sudo"]

    def test_enroll_offers_recovery_key_then_requires_typed_phrase(self):
        self.assertEqual(self.run_tpm("tpm-enroll", ["", "", "ENROLL TPM"]), [
            ["luks-tpm-check", "/dev/nvme0n1p2"], ["luks-recovery-key", "/dev/nvme0n1p2"],
            ["luks-tpm-enroll", "/dev/nvme0n1p2"]])

    def test_enroll_without_phrase_changes_nothing(self):
        for answers in (["n", "enroll tpm"], ["n", "yes"], ["n", ""]):
            with self.subTest(answers=answers):
                self.assertEqual(self.run_tpm("tpm-enroll", answers), [["luks-tpm-check", "/dev/nvme0n1p2"]])

    def test_remove_requires_typed_phrase(self):
        self.assertEqual(self.run_tpm("tpm-remove", ["yes"]), [])
        self.assertEqual(self.run_tpm("tpm-remove", ["REMOVE TPM"]), [["luks-tpm-remove", "/dev/nvme0n1p2"]])

    def test_several_luks_devices_need_a_valid_choice(self):
        many = SimpleNamespace(stdout="/dev/sda2 crypto_LUKS\n/dev/sdb1 crypto_LUKS\n")
        with patch.object(security.subprocess, "run", return_value=many), patch("builtins.print"):
            with patch("builtins.input", return_value="2"):
                self.assertEqual(security.choose_luks_device(), "/dev/sdb1")
            for answer in ("0", "3", "x"):
                with patch("builtins.input", return_value=answer), self.assertRaises(ValueError):
                    security.choose_luks_device()
