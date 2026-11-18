from menu_data import load as load_menu
import json
import importlib.util
import os
from pathlib import Path
import tomllib
import unittest

import menu_data
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("factory_reset_action",
                                              ROOT / "walker/scripts/actions/system/factory-reset.py")
action = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action)


class FactoryResetActionTests(unittest.TestCase):
    def run_reset(self, mode, answers):
        """`answers`: the first warning's key (Enter continues, Esc cancels), then the typed phrase."""
        calls = []
        keys, typed = answers[:1], answers[1:]
        with patch("eitr_terminal.read_key", side_effect=keys), \
                patch("builtins.input", side_effect=typed), patch("builtins.print"), \
                patch.object(action.subprocess, "run", side_effect=lambda args, **kwargs: calls.append(args)):
            action.main(mode)
        return calls

    def test_escape_at_the_first_warning_cancels(self):
        for mode in ("everything", "keep-files"):
            self.assertEqual(self.run_reset(mode, ["\x1b"]), [])
            self.assertEqual(self.run_reset(mode, ["\x03"]), [])

    def test_second_warning_requires_the_exact_phrase(self):
        for typed in ("", "reset my computer", "RESET MY COMPUTER ", "yes"):
            with self.subTest(typed=typed):
                calls = self.run_reset("everything", ["\r", typed])
                self.assertEqual(calls, [["sudo", action.HELPER, "status"]])

    def test_confirmed_reset_passes_mode_and_phrase_to_the_helper(self):
        calls = self.run_reset("keep-files", ["\r", "RESET MY COMPUTER"])
        self.assertEqual(calls, [["sudo", action.HELPER, "status"],
                                 ["sudo", action.HELPER, "reset", "--mode", "keep-files",
                                  "--confirm", "RESET MY COMPUTER"]])

    def test_warnings_explain_what_each_reset_removes(self):
        self.assertIn("ALL files", " ".join(action.FIRST_WARNINGS["everything"]))
        self.assertIn("Settings before reset", " ".join(action.FIRST_WARNINGS["keep-files"]))
        self.assertIn("restarts", " ".join(action.SECOND_WARNING))

    def test_warnings_wrap_to_the_terminal(self):
        printed = []
        with patch.object(action.shutil, "get_terminal_size", return_value=os.terminal_size((50, 20))), \
                patch("builtins.print", side_effect=lambda *args: printed.append(" ".join(args))):
            action.show(action.SECOND_WARNING, host="laptop")
        lines = "\n".join(printed).splitlines()
        self.assertTrue(all(len(line) <= 49 for line in lines))
        self.assertIn('the computer named "laptop".', " ".join(lines))

    def test_menu_lives_under_maintenance_and_runs_the_task_terminal(self):
        menu = load_menu("factory-reset")
        self.assertEqual(menu["parent"], "system-maintenance")
        system = menu_data.load("system-maintenance")
        entry = next(entry for entry in system["entries"] if entry.get("submenu") == "factory-reset")
        self.assertEqual(entry["subtext"], ">")
        modes = {}
        for item in menu["entries"]:
            command = item["actions"]["open"]
            self.assertIn("system/factory-reset.py", command)
            modes[item["text"]] = command.rsplit(" ", 1)[1]
        self.assertEqual(modes, {"Erase Everything": "everything", "Keep My Files": "keep-files",
                                 "Reset Status": "status"})


if __name__ == "__main__":
    unittest.main()
