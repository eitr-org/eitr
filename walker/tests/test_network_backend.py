import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("network_choice", ROOT / "walker/scripts/actions/system/network-backend.py")
choice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(choice)


class NetworkChoiceTests(unittest.TestCase):
    def helper(self):
        helper = Mock()
        helper.is_file.return_value = True
        helper.stat.return_value = SimpleNamespace(st_uid=0, st_mode=0o100755)
        helper.__str__ = Mock(return_value="/usr/lib/eitr/eitr-network")
        return helper

    def test_declining_reboot_saves_without_disconnecting_or_rebooting(self):
        with patch.object(choice, "HELPER", self.helper()), patch("builtins.input", side_effect=["yes", "n"]), patch("builtins.print"), \
                patch.object(choice.subprocess, "run") as run:
            choice.main(["networkmanager"])
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[-1], ["sudo", "/usr/lib/eitr/eitr-network", "stage", "networkmanager"])
        self.assertTrue(all(command[:2] in (["systemctl", "is-active"], ["sudo", "/usr/lib/eitr/eitr-network"])
                            for command in commands))

    def test_reboot_requires_separate_confirmation(self):
        with patch.object(choice, "HELPER", self.helper()), patch("builtins.input", side_effect=["y", "y"]), patch("builtins.print"), \
                patch.object(choice.subprocess, "run") as run:
            choice.main(["iwd"])
        self.assertEqual(run.call_args_list[-1].args[0], ["systemctl", "reboot"])

    def test_declining_selection_does_not_change_anything(self):
        with patch.object(choice, "HELPER", self.helper()), patch("builtins.input", return_value="n"), patch("builtins.print"), \
                patch.object(choice.subprocess, "run") as run:
            choice.main(["iwd"])
        self.assertTrue(all(call.args[0][:2] == ["systemctl", "is-active"] for call in run.call_args_list))


if __name__ == "__main__":
    unittest.main()
