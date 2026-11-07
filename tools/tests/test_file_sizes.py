"""Source files stay small: new ones under the limit, older large ones may only shrink.

The limit and the list of older files above it live in tools/file-size-baseline.json.
Split a file by responsibility instead of raising its entry; lower the entry (or drop
it) after splitting one.
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
    def test_files_stay_under_the_limit_or_their_baseline(self):
        baseline = json.loads(BASELINE.read_text())
        limit, allowed = baseline["limit"], baseline["files"]
        problems = []
        for name, lines in source_files():
            ceiling = max(limit, allowed.get(name, 0))
            if lines > ceiling:
                reason = "grew past its baseline" if name in allowed else f"is over {limit} lines"
                problems.append(f"{name} has {lines} lines and {reason}: split it by responsibility")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_baseline_lists_only_files_that_still_need_it(self):
        baseline = json.loads(BASELINE.read_text())
        sizes = dict(source_files())
        # A ratchet: an entry drops out once its file is under the limit, and follows it down.
        stale = [f"{name} (now {sizes.get(name, 0)} lines)" for name, lines in baseline["files"].items()
                 if sizes.get(name, 0) < lines]
        self.assertEqual(stale, [], "Lower or remove these in tools/file-size-baseline.json: " + ", ".join(stale))


if __name__ == "__main__":
    unittest.main()
