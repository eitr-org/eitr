"""The optional bar slot extends schema 2 without changing old declarations."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from eitr_plugin_manifest import validate_ui


class ClockSlotManifestTests(unittest.TestCase):
    def test_default_status_and_clock_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Clock.qml').write_text('import QtQuick\nItem {}\n')
            for slot in (None, 'status', 'clock'):
                entry = {'id': 'clock', 'title': 'Clock', 'qml': 'Clock.qml'}
                if slot is not None:
                    entry['slot'] = slot
                validate_ui(root, {'barItems': [entry]})

    def test_unknown_and_wrong_type_slots_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Clock.qml').write_text('import QtQuick\nItem {}\n')
            for slot in ('left', '', 1, None, [], {}):
                with self.subTest(slot=slot), self.assertRaises(ValueError):
                    validate_ui(root, {'barItems': [{'id': 'clock', 'title': 'Clock', 'qml': 'Clock.qml', 'slot': slot}]})

    def test_slot_is_not_allowed_on_other_visual_kinds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Clock.qml').write_text('import QtQuick\nItem {}\n')
            for kind in ('tiles', 'panels', 'widgets'):
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    validate_ui(root, {kind: [{'id': 'clock', 'title': 'Clock', 'qml': 'Clock.qml', 'slot': 'clock'}]})
