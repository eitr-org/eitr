from pathlib import Path
import re
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/menus/shortcuts.sh"


def option_rows(source):
    options = re.search(r'^options="(.*?)"$', source, re.S | re.M)[1]
    return [row for row in options.splitlines() if row.startswith("  ")]


def case_branches(source):
    """Literal prefixes of each `"literal"*` alternative, in matching order."""
    branches = []
    for line in source.splitlines():
        if re.fullmatch(r'  "[^"]*"\*(?: \| "[^"]*"\*)*\)', line):
            branches.extend(re.findall(r'"([^"]*)"\*', line))
    return branches


class ShortcutsMenuTests(unittest.TestCase):
    def test_each_row_runs_its_own_branch(self):
        # Bash uses the first matching glob; "SUPER + C"* once caught the
        # "SUPER + Ctrl + V" row, and "SUPER + T"* caught "SUPER + Tab".
        source = SCRIPT.read_text(encoding="utf-8")
        branches = case_branches(source)
        for row in option_rows(source):
            key = re.split(r"\s{2,}", row.strip())[0]
            match = next((prefix for prefix in branches if row.startswith(prefix)), None)
            self.assertIsNotNone(match, row)
            self.assertEqual(match.strip(), key, row)


if __name__ == "__main__":
    unittest.main()
