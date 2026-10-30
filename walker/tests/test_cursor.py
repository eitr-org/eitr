import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cursor", ROOT / "walker/scripts/actions/style/cursor.py")
cursor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cursor)


class CursorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        for key, value in {"HOME": self.home, "CONFIG": self.home / ".config", "PREFERENCE": self.home / ".config/eitr/cursor.json"}.items():
            self.patch = patch.object(cursor, key, value)
            self.patch.start(); self.addCleanup(self.patch.stop)

    def test_six_variants_and_auto_follows_category_not_family(self):
        self.assertEqual(len({value for variants in cursor.FAMILIES.values() for value in variants.values()}), 6)
        marker = cursor.CONFIG / "theme/current/light.mode"
        marker.parent.mkdir(parents=True)
        for family in cursor.FAMILIES:
            choice = {"family": family, "color": "auto", "size": 24}
            self.assertEqual(cursor.resolve(choice), cursor.FAMILIES[family]["dark"])
            marker.touch()
            self.assertEqual(cursor.resolve(choice), cursor.FAMILIES[family]["light"])
            choice["color"] = "dark"
            self.assertEqual(cursor.resolve(choice), cursor.FAMILIES[family]["dark"])
            marker.unlink()

    def test_sync_preserves_gtk_keys_and_skips_session_in_installer(self):
        gtk = cursor.CONFIG / "gtk-3.0/settings.ini"
        gtk.parent.mkdir(parents=True)
        gtk.write_text("[Settings]\ngtk-theme-name=Existing\n")
        with patch.object(cursor, "installed", return_value=True), patch.dict(os.environ, EITR_NO_SESSION="1"), patch.object(cursor.subprocess, "run") as run:
            cursor.sync(dict(cursor.DEFAULTS))
            run.assert_not_called()
        self.assertIn("gtk-theme-name=Existing", gtk.read_text())
        self.assertIn("gtk-cursor-theme-name=Bibata-Modern-Classic", gtk.read_text())
        self.assertIn("XCURSOR_SIZE,24", (cursor.CONFIG / "hypr/cursor-env.conf").read_text())

    def test_sync_reloads_hyprland_only_when_the_cursor_changes(self):
        with patch.object(cursor, "installed", return_value=True), patch.dict(os.environ, {"EITR_NO_SESSION": ""}), \
                patch.object(cursor.subprocess, "run") as run:
            cursor.sync(dict(cursor.DEFAULTS))
            self.assertIn(["hyprctl", "reload"], [call.args[0] for call in run.call_args_list])
            run.reset_mock()
            cursor.sync(dict(cursor.DEFAULTS))
            commands = [call.args[0] for call in run.call_args_list]
            self.assertNotIn(["hyprctl", "reload"], commands)
            self.assertIn(["hyprctl", "setcursor", "Bibata-Modern-Classic", "24"], commands)

    def test_bad_preferences_and_missing_assets_do_not_save_selection(self):
        cursor.PREFERENCE.parent.mkdir(parents=True)
        for data in ('[]', '{"family": [], "color": {}, "size": true}', 'null'):
            cursor.PREFERENCE.write_text(data)
        with self.assertRaises(ValueError):
            cursor.read()
        previous = cursor.PREFERENCE.read_text()
        with patch.object(cursor, "installed", return_value=False), self.assertRaises(ValueError):
            cursor.main(["set", "family", "dmz"])
        self.assertEqual(cursor.PREFERENCE.read_text(), previous)

    def test_selected_entries_replace_preview_with_theme_checkmark(self):
        with patch.object(cursor, "preview", return_value="/preview.png"):
            for group in ("family", "color", "size"):
                rows = cursor.main(["entries", group])
                selected = [row for row in rows if row["selected"]]
                self.assertEqual(len(selected), 1)
                self.assertEqual(selected[0]["icon"], "")
                self.assertNotIn("✓", selected[0]["detail"])
                self.assertTrue(all(row["icon"] == "/preview.png" for row in rows if not row["selected"]))
        self.assertEqual([row["id"] for row in cursor.entries("size")], [str(size) for size in cursor.SIZES])

    def test_preview_reads_actual_xcursor_pixels(self):
        import struct
        theme = self.home / ".local/share/icons/Bibata-Modern-Classic/cursors"
        theme.mkdir(parents=True)
        data = struct.pack("<4I", 0x72756358, 16, 1, 1)
        data += struct.pack("<3I", 0xfffd0002, 32, 28)
        data += struct.pack("<9I", 36, 0xfffd0002, 32, 1, 1, 1, 0, 0, 0)
        data += bytes([0, 0, 255, 255])
        (theme / "left_ptr").write_bytes(data)
        from PIL import Image
        with Image.open(cursor.preview("Bibata-Modern-Classic")) as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))

class CursorSummaryTests(unittest.TestCase):
    def test_summary_reads_once_and_does_not_generate_previews(self):
        choice = {"family": "breeze", "size": 32, "color": "light"}
        with patch.object(cursor, 'read', return_value=choice) as read, \
                patch.object(cursor, 'installed', return_value=False), \
                patch.object(cursor, 'preview') as preview:
            result = cursor.main(['summary'])
        read.assert_called_once()
        preview.assert_not_called()
        self.assertEqual(result['current'], choice)
        for group, rows in result['choices'].items():
            self.assertEqual([row['id'] for row in rows if row['selected']], [str(choice[group])])
            self.assertTrue(all(not row['available'] for row in rows))
