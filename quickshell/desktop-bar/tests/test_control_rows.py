"""Every ControlRow and ToggleRow sets its required description.

A row without one fails to build, and the whole Settings page holding it shows empty;
offscreen fixtures do not always surface that, so this checks the sources directly.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
ROW = re.compile(r'\b(ToggleRow|ControlRow|SettingsChoiceSection)\s*\{')


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
            if path.name in ('ToggleRow.qml', 'ControlRow.qml', 'SettingsChoiceSection.qml'):
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


# Transient forms and searches already explain their input in labels/placeholders.
# Counts make an additional bare control fail even in an excepted file.
BARE_EXCEPTIONS = {
    ('FamilySidebar.qml', 'TextField'): (1, 'Settings search'),
    ('SettingsKeybindsPage.qml', 'TextField'): (1, 'Shortcut search'),
    ('SettingsAccountSheet.qml', 'ChoiceSegmented'): (1, 'Destructive review with its own explanation'),
    ('SettingsPasswordSheet.qml', 'PanelTextField'): (3, 'Labelled password confirmation form'),
    ('SettingsAudioDeviceCard.qml', 'TextField'): (1, 'Temporary device rename editor'),
    ('SettingsWifiCredentials.qml', 'PanelTextField'): (5, 'Labelled network credential form'),
}
CONTROLS = {
    'ChoiceDropdown', 'ChoiceSegmented', 'ChoiceLevel', 'PictureChoices',
    'PanelSlider', 'PanelSwitch', 'PanelTextField', 'TextField', 'Slider',
    'Switch', 'ComboBox', 'SpinBox', 'AudioLevelControl',
}


# Owners that give a control its title and description.
DESCRIBED = ('ControlRow', 'ToggleRow', 'SettingsChoiceSection')


def source_blocks(text):
    """Small structural scan, preserving each object's enclosing source range."""
    result = []
    for match in re.finditer(r'\b([A-Z]\w*)\s*\{', text):
        depth, index = 1, match.end()
        while depth and index < len(text):
            depth += {'{': 1, '}': -1}.get(text[index], 0)
            index += 1
        result.append((match[1], match.start(), index, text[match.end():index - 1]))
    return result


def bare_controls(text):
    blocks = source_blocks(text)
    return [(kind, start, body) for kind, start, end, body in blocks
            if kind in CONTROLS and not any(
                owner in DESCRIBED and first < start and last >= end
                for owner, first, last, unused in blocks)]


class SettingsControlCoverageTests(unittest.TestCase):
    def test_settings_controls_have_rows_or_documented_exceptions(self):
        bar = ROOT / 'quickshell/desktop-bar'
        counts = {}
        failures = []
        for path in [*bar.glob('settings/*.qml'), *bar.glob('components/Settings*.qml')]:
            for kind, start, body in bare_controls(path.read_text()):
                key = (path.name, kind)
                counts[key] = counts.get(key, 0) + 1
                if key not in BARE_EXCEPTIONS:
                    failures.append(f'{path.name}:{kind}')
                if kind == 'ChoiceDropdown' and re.search(r'\blabel\s*:', own_properties(body)):
                    failures.append(f'{path.name}: labelled dropdown outside a row')
        self.assertEqual(failures, [])
        self.assertEqual(counts, {key: entry[0] for key, entry in BARE_EXCEPTIONS.items()})

    def test_scan_catches_new_and_nested_bare_controls(self):
        self.assertEqual(len(bare_controls('Column { ChoiceDropdown { label: "Name" } }')), 1)
        self.assertEqual(len(bare_controls('Column { Slider {} PanelSwitch {} }')), 2)
        self.assertEqual(bare_controls('ControlRow { description: "Help"; Row { ChoiceDropdown {} } }'), [])
        self.assertEqual(bare_controls('ToggleRow { description: "Help"; PanelSwitch {} }'), [])
        self.assertEqual(bare_controls('SettingsChoiceSection { description: "Help"; PictureChoices {} }'), [])

    def test_settings_descriptions_are_not_empty_literals(self):
        bar = ROOT / 'quickshell/desktop-bar'
        for path in [*bar.glob('settings/*.qml'), *bar.glob('components/Settings*.qml')]:
            for kind, start, end, body in source_blocks(path.read_text()):
                if kind in DESCRIBED:
                    self.assertNotRegex(own_properties(body), r'\bdescription\s*:\s*""', path.name)


if __name__ == '__main__':
    unittest.main()
