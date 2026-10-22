import os
import os
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

import menu_data

ROOT = Path(__file__).resolve().parents[2]
PRESENTER = ROOT / "walker/scripts/actions/task-terminal.py"


class TaskTerminalTests(unittest.TestCase):
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
