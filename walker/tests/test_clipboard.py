import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("clipboard", Path(__file__).parents[1] / "scripts/menus/clipboard.py")
clipboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clipboard)


class ClipboardTests(unittest.TestCase):
    def test_image_preview_and_text_entry(self):
        with tempfile.TemporaryDirectory() as runtime, patch.dict(os.environ, {"XDG_RUNTIME_DIR": runtime}), \
                patch.object(clipboard.subprocess, "check_output", return_value="2\t[[ binary data 8 KiB png 418x109 ]]\n1\tHello\n"), \
                patch.object(clipboard.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=b"image")):
            rows = clipboard.entries()
            preview = Path(rows[0]["preview"])
            self.assertEqual(preview.suffix, ".png")
            self.assertEqual(preview.stat().st_mode & 0o777, 0o600)
            self.assertEqual(rows[1], {"id": "1", "label": "Hello", "preview": ""})
            self.assertEqual(preview.parent.stat().st_mode & 0o777, 0o700)

    def test_history_menu_keeps_newest_first(self):
        # Sorting by label would bury a fresh screenshot ("Image ...") mid-list.
        menu = (Path(__file__).parents[2] / "elephant/menus/clipboard.lua").read_text()
        self.assertIn("FixedOrder = true", menu)
        self.assertNotIn("alphabetical.lua", menu)

    def test_failed_decode_has_no_preview(self):
        with tempfile.TemporaryDirectory() as runtime, patch.dict(os.environ, {"XDG_RUNTIME_DIR": runtime}), \
                patch.object(clipboard.subprocess, "check_output", return_value="2\t[[ binary data 8 KiB png 418x109 ]]\n"), \
                patch.object(clipboard.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout=b"")):
            self.assertEqual(clipboard.entries()[0]["preview"], "")

    def test_invalid_identifier_never_runs_commands(self):
        with patch.object(clipboard.subprocess, "check_output") as command:
            with self.assertRaises(ValueError):
                clipboard.paste("1; touch /tmp/example")
            command.assert_not_called()

    def test_paste_preserves_binary_bytes(self):
        with patch.object(clipboard.subprocess, "check_output", return_value=b"\x89PNG\x00"), \
                patch.object(clipboard.subprocess, "run") as command, patch.object(clipboard.time, "sleep"):
            clipboard.paste("2")
            self.assertEqual(command.call_args_list[0].kwargs["input"], b"\x89PNG\x00")
            self.assertEqual(command.call_args_list[1].args[0][0], "wtype")

    def test_delete_only_selected_id_and_refreshes_previews(self):
        with patch.object(clipboard.subprocess, "run") as command, patch.object(clipboard, "entries") as refresh:
            clipboard.delete("2")
            command.assert_called_once_with(["cliphist", "delete"], input=b"2", check=True, timeout=5)
            refresh.assert_called_once()

    def test_invalid_delete_id_is_rejected(self):
        with patch.object(clipboard.subprocess, "run") as command:
            with self.assertRaises(ValueError):
                clipboard.delete("--all")
            command.assert_not_called()
