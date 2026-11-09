"""Every ControlRow and ToggleRow sets its required description.

A row without one fails to build, and the whole Settings page holding it shows empty;
offscreen fixtures do not always surface that, so this checks the sources directly.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
ROW = re.compile(r'\b(ToggleRow|ControlRow)\s*\{')


def own_properties(body):
    """The row's own lines, without the blocks nested inside it."""
    previous = None
    while previous != body:
        previous, body = body, re.sub(r'\{[^{}]*\}', '', body)
    return body


class ControlRowTests(unittest.TestCase):
    def test_every_row_sets_a_description(self):
        missing = []
        for path in (ROOT / 'quickshell').rglob('*.qml'):
            if path.name in ('ToggleRow.qml', 'ControlRow.qml'):
                continue
            text = path.read_text()
            for match in ROW.finditer(text):
                depth, index = 1, match.end()
                while depth and index < len(text):
                    depth += {'{': 1, '}': -1}.get(text[index], 0)
                    index += 1
                if not re.search(r'\bdescription\s*:', own_properties(text[match.end():index])):
                    missing.append(f'{path.relative_to(ROOT)}:{text[:match.start()].count(chr(10)) + 1}')
        self.assertEqual(missing, [])


if __name__ == '__main__':
    unittest.main()
