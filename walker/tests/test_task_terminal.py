import os
import os
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import io

import menu_data

ROOT = Path(__file__).resolve().parents[2]
PRESENTER = ROOT / "walker/scripts/actions/task-terminal.py"


class TaskTerminalTests(unittest.TestCase):
    def presenter(self):
        spec = importlib.util.spec_from_file_location("task_terminal", PRESENTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_capture_is_bounded_and_strips_split_ansi_and_utf8(self):
        module = self.presenter()
        tail = module.OutputTail()
        tail.feed(b"old\n" * 210 + b"\x1b[3")
        tail.feed(b"1mred\x1b[0m\n" + "é".encode()[:1])
        tail.feed("é".encode()[1:])
        lines = tail.text().splitlines()
        self.assertEqual(len(lines), 200)
        self.assertEqual(lines[-2:], ["red", "é"])
        tail.feed(b"x" * 100000)
        self.assertLessEqual(len(tail.pending), 8192)

    def test_pty_passes_bytes_through_and_restores_terminal(self):
        module = self.presenter()
        tail = module.OutputTail()
        with patch.object(module.sys.stdin, "fileno", return_value=10), patch.object(module.sys.stdout, "fileno", return_value=11), patch.object(module.pty, "fork", return_value=(42, 12)), patch.object(module.termios, "tcgetattr", return_value=["original"]), patch.object(module.termios, "tcsetattr") as restore, patch.object(module.fcntl, "ioctl", return_value=b"geometry"), patch.object(module.signal, "signal"), patch.object(module.tty, "setraw"), patch.object(module.select, "select", side_effect=[([10], [], []), ([12], [], []), ([12], [], [])]), patch.object(module.os, "read", side_effect=[b"input", b"\x1b[31moutput\x1b[0m\r\n", b""]), patch.object(module.os, "write", side_effect=[5, 18]) as write, patch.object(module.os, "close") as close, patch.object(module.os, "waitpid", side_effect=[(0, 0), (0, 0), (0, 0), (42, 7 << 8)]):
            self.assertEqual(module.run_captured(["task"], tail), 7)
            self.assertEqual(bytes(write.call_args_list[0].args[1]), b"input")
            self.assertEqual(bytes(write.call_args_list[1].args[1]), b"\x1b[31moutput\x1b[0m\r\n")
            self.assertEqual(tail.text(), "output")
            restore.assert_called_once_with(10, module.termios.TCSADRAIN, ["original"])
            close.assert_called_once_with(12)

    def test_the_task_ending_ends_the_wait_even_if_the_terminal_stays_open(self):
        # Something the task started in the background may keep the terminal open.
        module = self.presenter()
        with patch.object(module.sys.stdin, "fileno", return_value=10), patch.object(module.pty, "fork", return_value=(42, 12)), \
                patch.object(module.termios, "tcgetattr", return_value=["original"]), patch.object(module.termios, "tcsetattr"), \
                patch.object(module.fcntl, "ioctl", return_value=b"geometry"), patch.object(module.signal, "signal"), \
                patch.object(module.tty, "setraw"), patch.object(module.select, "select", return_value=([], [], [])) as select, \
                patch.object(module.os, "read") as read, patch.object(module.os, "close"), \
                patch.object(module.os, "waitpid", side_effect=[(0, 0), (42, 3 << 8)]) as waitpid:
            self.assertEqual(module.run_captured(["task"], module.OutputTail()), 3)
        self.assertEqual(select.call_count, 2)
        self.assertEqual(waitpid.call_count, 2)
        read.assert_not_called()

    def test_failure_offers_assistant_and_redacts_secrets(self):
        module = self.presenter()
        tail = module.OutputTail()
        tail.feed(b"failure\npassword=abc\nTOKEN=def\nsecret=ghi\nAuthorization: Bearer xyz\n-----BEGIN PRIVATE KEY-----\n")
        for assistant in ("gemini", "copilot", "claude"):
            with self.subTest(assistant=assistant), patch.object(module, "default_assistant", return_value=assistant), patch.object(module, "open_default") as opened, patch.object(module, "read_key", side_effect=["A", "\x1b"]), patch("sys.stdout", new_callable=io.StringIO) as output:
                module.failure_help(["/usr/bin/python3", "/some/task.py", "--token=abc", "extra"], tail)
                self.assertIn("A: ask the AI", output.getvalue())
                arguments = opened.call_args.args[0]
                self.assertEqual(len(arguments), 2 if assistant in {"gemini", "copilot"} else 1)
                prompt = arguments[-1]
                self.assertIn("python3 task.py [hidden]", prompt)
                self.assertIn("untrusted data", prompt)
                self.assertIn("unless I agree", prompt)
                self.assertEqual(prompt.count("[hidden]"), 6)
                for value in ("abc", "def", "ghi", "xyz", "/some", "extra"):
                    self.assertNotIn(value, prompt)

    def test_failure_without_assistant_uses_existing_dismissal(self):
        module = self.presenter()
        with patch.object(module, "default_assistant", return_value=None), patch.object(module, "wait_for_escape") as wait, patch.object(module, "read_key") as key, patch.object(module, "open_default") as opened:
            module.failure_help(["task"], module.OutputTail())
            wait.assert_called_once_with()
            key.assert_not_called()
            opened.assert_not_called()

    def test_task_result_controls_failure_help(self):
        module = self.presenter()
        for result in (0, 1, 130):
            with self.subTest(result=result), patch.object(module, "banner"), patch.object(module.sys.stdin, "isatty", return_value=True), patch.object(module, "run_captured", return_value=result), patch.object(module, "failure_help") as help_task, patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(module.main(["task"]), result)
                self.assertEqual(help_task.call_count, int(result == 1))

    def test_plain_fallback_never_offers_ai(self):
        module = self.presenter()
        with patch.object(module, "banner"), patch.object(module.sys.stdin, "isatty", return_value=True), patch.object(module, "run_captured", side_effect=module.PtyUnavailable), patch.object(module.subprocess, "run") as run, patch.object(module, "wait_for_escape") as wait, patch.object(module, "failure_help") as help_task, patch("sys.stdout", new_callable=io.StringIO):
            run.return_value.returncode = 1
            self.assertEqual(module.main(["task"]), 1)
            run.assert_called_once_with(["task"])
            wait.assert_called_once_with()
            help_task.assert_not_called()

    def test_task_and_status_terminal_launches_use_banner(self):
        for name, data in menu_data.static_menus().items():
            for entry in data.get("entries", []):
                command = entry.get("actions", {}).get("open", "")
                if "kitty" in command and " -e " in command:
                    with self.subTest(menu=name, entry=entry["text"]):
                        self.assertIn("task-terminal.py", command)

    def test_banner_only_does_not_attempt_to_launch_a_command(self):
        result = subprocess.run(["python3", str(PRESENTER), "--banner-only"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertIn("\033[38;2;", result.stdout)

    def test_banner_draws_the_packaged_wordmark_not_the_rune_fallback(self):
        result = subprocess.run(["python3", str(PRESENTER), "--banner-only"], capture_output=True, text=True,
                                timeout=10, env=dict(os.environ, EITR_CODE_ROOT=str(ROOT), COLUMNS="80"))
        # The wordmark comes before the reset code; the Futhark band follows it.
        wordmark = result.stdout.split("\033[0m", 1)[0]
        self.assertNotIn("ᛖ", wordmark)
        self.assertGreater(wordmark.count("\n"), 4)

    def test_banner_ends_with_the_futhark_in_the_accent(self):
        result = subprocess.run(["python3", str(PRESENTER), "--banner-only"], capture_output=True, text=True,
                                timeout=10, env=dict(os.environ, EITR_CODE_ROOT=str(ROOT), COLUMNS="80"))
        band = result.stdout.split("\033[0m", 1)[1]
        self.assertEqual("".join(character for character in band if "\u16a0" <= character <= "\u16ff"),
                         "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ")
        narrow = subprocess.run(["python3", str(PRESENTER), "--banner-only"], capture_output=True, text=True,
                                timeout=10, env=dict(os.environ, EITR_CODE_ROOT=str(ROOT), COLUMNS="20"))
        # A narrow terminal gets a shorter band that still fits: one rune and one space each.
        runes = [character for character in narrow.stdout.split("\033[0m", 1)[1] if "\u16a0" <= character <= "\u16ff"]
        self.assertEqual("".join(runes), "ᚠᚢᚦᚨᚱᚲᚷᚹᚺ")

    def test_cloud_tasks_print_banner_after_clear_and_keep_return_behavior(self):
        source = (ROOT / "walker/scripts/menus/cloud/common.sh").read_text()
        self.assertIn('clear\n\npython3 "$EITR_CODE_ROOT/walker/scripts/actions/task-terminal.py" --banner-only', source)
        self.assertIn('return-on-success', source)

    def test_centering_preserves_wordmark_alignment(self):
        spec = importlib.util.spec_from_file_location("task_terminal", PRESENTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.centered("██  \n  ██", 10), "   ██  \n     ██")
        self.assertEqual(module.centered("████", 2), "████")

    def test_wordmark_proportions_account_for_terminal_cells(self):
        spec = importlib.util.spec_from_file_location("task_terminal", PRESENTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.raster_height(48, 2.4, 0.5), 20)
        self.assertEqual(module.raster_height(48, 2.4, 0.6), 24)
        self.assertEqual(module.raster_height(1, 2.4, 0.5), 2)

    def test_accent_success_and_argument_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            palette = Path(directory) / "theme/current"
            palette.mkdir(parents=True)
            (palette / "colors.toml").write_text('accent = "#123456"')
            result = subprocess.run(
                ["python3", str(PRESENTER), "printf", "%s", "one; two"],
                env=dict(os.environ, XDG_CONFIG_HOME=directory), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("\033[38;2;18;52;86m", result.stdout)
            self.assertTrue(result.stdout.endswith("one; two"))
            self.assertNotIn("Press Enter", result.stdout)

    def test_failure_status_is_preserved_without_noninteractive_wait(self):
        result = subprocess.run(["python3", str(PRESENTER), "bash", "-c", "exit 7"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 7)

    def test_all_static_submenus_have_visible_arrows(self):
        for name, data in menu_data.static_menus().items():
            for entry in data.get("entries", []):
                if entry.get("submenu"):
                    with self.subTest(menu=name, entry=entry["text"]):
                        self.assertEqual(entry.get("subtext"), ">")
                        layout = ROOT / f"walker/themes/current/item_menus-{name}.xml"
                        self.assertIn("ItemSubtext", layout.read_text())

    def test_update_terminals_use_presenter_without_hold(self):
        for name in ("update",):
            data = menu_data.load(name)
            for entry in data["entries"]:
                if "actions" in entry:
                    command = entry["actions"]["open"]
                    self.assertIn("task-terminal.py", command)
                    self.assertNotIn("--hold", command)
