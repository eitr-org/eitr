import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/themes/vscode-theme.py"
spec = importlib.util.spec_from_file_location("vscode_theme", SCRIPT)
vscode_theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vscode_theme)

COMMENTED = """// User settings
{
  /* editor */
  "editor.fontSize": 14, // keep
  "workbench.colorTheme": "Old Theme", // theme comment
  "nested": { "workbench.colorTheme": "inner" },
  "url": "http://example.com/*not a comment*/",
}
"""


class VSCodeThemeTests(unittest.TestCase):
    def test_replaces_only_top_level_value_and_keeps_comments(self):
        updated = vscode_theme.set_top_level_string(COMMENTED, "workbench.colorTheme", 'New "Theme"')
        self.assertEqual(updated, COMMENTED.replace('"Old Theme"', '"New \\"Theme\\""'))

    def test_inserts_missing_key(self):
        updated = vscode_theme.set_top_level_string('{\n  // only comment\n}\n', "workbench.colorTheme", "Nord")
        self.assertIn('"workbench.colorTheme": "Nord"\n', updated)
        self.assertIn("// only comment", updated)
        updated = vscode_theme.set_top_level_string('{"a": 1}', "workbench.colorTheme", "Nord")
        self.assertEqual(json.loads(updated), {"workbench.colorTheme": "Nord", "a": 1})

    def test_cli_reads_theme_and_updates_settings_in_place(self):
        with tempfile.TemporaryDirectory() as directory:
            theme = Path(directory) / "vscode.json"
            theme.write_text('{"name": "Nord", "extension": "arcticicestudio.nord-visual-studio-code"}')
            read = subprocess.run([sys.executable, str(SCRIPT), "read", str(theme)], capture_output=True, text=True)
            self.assertEqual(read.stdout.split("\n")[:3], ["Nord", "arcticicestudio.nord-visual-studio-code", ""])
            settings = Path(directory) / "settings.json"
            settings.write_text(COMMENTED)
            subprocess.run([sys.executable, str(SCRIPT), "set", str(settings), "Nord"], check=True)
            self.assertIn('"workbench.colorTheme": "Nord", // theme comment', settings.read_text())
            self.assertIn("/* editor */", settings.read_text())

    def test_invalid_settings_are_left_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "settings.json"
            settings.write_text('{"a": "unterminated}')
            result = subprocess.run([sys.executable, str(SCRIPT), "set", str(settings), "Nord"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(settings.read_text(), '{"a": "unterminated}')


if __name__ == "__main__":
    unittest.main()
