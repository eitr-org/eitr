import json
from pathlib import Path
import os
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/menus/cmux.sh"


class CmuxMenuTests(unittest.TestCase):
    def choose(self, choice):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            binaries = home / "bin"
            binaries.mkdir()
            walker = home / ".config/walker/bin/walker-dmenu"
            walker.parent.mkdir(parents=True)
            walker.write_text('#!/bin/sh\ncat >/dev/null\nprintf "%s" "$CHOICE"\n')
            walker.chmod(0o755)
            for name, code in {"wl-copy": 'cat > "$HOME/copied"', "notify-send": "exit 0",
                               "cmux": 'touch "$HOME/executed"'}.items():
                file = binaries / name
                file.write_text("#!/bin/sh\n" + code + "\n")
                file.chmod(0o755)
            result = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True,
                                    env={**os.environ, "HOME": str(home), "CHOICE": choice,
                                         "EITR_CODE_ROOT": str(home / '.config'),
                                         "PATH": str(binaries) + ":/usr/bin:/bin"})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / "executed").exists())
            return (home / "copied").read_text() if (home / "copied").exists() else None

    def test_command_selection_only_copies(self):
        self.assertEqual(self.choose("  cmux --session work        Open a named session"), "cmux --session work")

    def test_cancel_and_headings_do_nothing(self):
        self.assertIsNone(self.choose(""))
        self.assertIsNone(self.choose("  Sessions"))

    def test_learn_entry_uses_the_reference(self):
        menu = {"entries": json.loads((ROOT / "elephant/menu-rows/learn.json").read_text())}
        entry = next(entry for entry in menu["entries"] if entry["text"] == "Cmux Commands")
        self.assertIn("bash /usr/share/eitr/walker/scripts/menus/cmux.sh", entry["actions"]["open"])
