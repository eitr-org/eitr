"""Source files over the size limit are a recorded decision, never an accident.

tools/file-size-baseline.json holds the limit and every file allowed above it, each
with its current size and a one-line reason. A file over the limit must be listed;
a listed file may grow only when the same change updates its size (and reason).
"""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "tools/file-size-baseline.json"
PATTERNS = ("*.qml", "*.js", "*.py", "*.lua", "*.sh")
# Files written by generators from their own sources.
GENERATED = {"quickshell/Eitr/Catalogs.js", "quickshell/desktop-bar/ChoiceLists.js",
             "distro/lib/eitr_choice_lists.py", "elephant/choice-lists.lua"}


def source_files():
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", *PATTERNS],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    for name in listed:
        path = ROOT / name
        # Test runs leave tmp* folders in the checkout while they run.
        if ("/tests/" in name or name.startswith(("website/", "tmp")) or name in GENERATED
                or not path.is_file()):
            continue
        yield name, sum(1 for _ in path.open(errors="ignore"))


class FileSizeTests(unittest.TestCase):
    def test_large_files_are_listed_with_a_reason(self):
        baseline = json.loads(BASELINE.read_text())
        limit, allowed = baseline["limit"], baseline["files"]
        problems = []
        for name, lines in source_files():
            entry = allowed.get(name)
            if lines <= limit:
                continue
            if entry is None:
                problems.append(f"{name} has {lines} lines: split it by responsibility, or list it "
                                f"in tools/file-size-baseline.json with its size and the reason it stays whole")
            elif lines > entry["lines"]:
                problems.append(f"{name} grew to {lines} lines (recorded {entry['lines']}): "
                                "update its entry if growing it was intended")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_every_entry_has_a_reason(self):
        for name, entry in json.loads(BASELINE.read_text())["files"].items():
            with self.subTest(file=name):
                self.assertIsInstance(entry["lines"], int)
                self.assertTrue(entry.get("reason", "").strip())


if __name__ == "__main__":
    unittest.main()
