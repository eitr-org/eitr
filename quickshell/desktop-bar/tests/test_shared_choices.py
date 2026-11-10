"""Shared panel controls, monitor fixtures and inert offscreen captures."""
import re
from pathlib import Path
import tempfile
import unittest

from layout_render import BAR, copy_runtime, render_environment, render, capture_path


class SharedChoicesTests(unittest.TestCase):
    def test_shared_ownership_and_map_sources(self):
        registry = (BAR / 'qmldir').read_text()
        manifest = (BAR.parents[1] / 'distro/layout-manifest.json').read_text()
        for name in ('ChoiceSegmented', 'ChoiceDropdown', 'PictureChoices', 'TabStrip',
                     'ChoiceLevel', 'ControlCard', 'ControlRow', 'ToggleRow', 'MonitorMap',
                     'BarPreview', 'PositionPreview', 'AppearancePreview', 'MediaPreview',
                     'CornersPreview', 'GapsPreview', 'LockscreenPreview', 'PalettePreview'):
            self.assertIn(f'{name} components/{name}.qml', registry)
            self.assertIn(f'components/{name}.qml', manifest)
            source = (BAR / 'components' / f'{name}.qml').read_text()
            self.assertNotIn('SettingsPalette.', source)
            self.assertNotIn('SettingsInk.', source)
        dropdown = (BAR / 'components/ChoiceDropdown.qml').read_text()
        # Lists float in the window overlay and register their surface for bar input.
        # Every inline selector uses this dropdown without resizing its host.
        for contract in ('Popup {', 'Popup.CloseOnPressOutsideParent', 'control.registerPopup(true)',
                         'control.Window.contentItem', 'implicitHeight: labelRoom + button.height', 'upward = below < wanted'):
            self.assertIn(contract, dropdown)
        self.assertNotIn('visible: control.expanded', dropdown)
        call_sites = {'panels/AudioMenu.qml': 1, 'panels/DisplaySettingsEditor.qml': 5, 'panels/RecordingMenu.qml': 1,
                      'settings/SettingsAppearancePage.qml': 5, 'settings/SettingsBarPage.qml': 1, 'settings/SettingsDefaultAppsPage.qml': 1, 'components/SettingsSummaryEntry.qml': 1,
                      'settings/SettingsInputPage.qml': 1, 'settings/SettingsAssistantPage.qml': 2,
                      'components/SettingsAudioDeviceCard.qml': 1, 'components/SettingsWifiCredentials.qml': 1}
        for path, count in call_sites.items():
            with self.subTest(call_site=path):
                self.assertEqual((BAR / path).read_text().count('ChoiceDropdown {'), count)
        audio = (BAR / 'panels/AudioMenu.qml').read_text()
        self.assertNotIn('picking', audio)
        self.assertIn('onActionTriggered: value => section.startRename(section.deviceFor(value))', audio)
        keyboard = (BAR / 'settings/SettingsInputPage.qml').read_text()
        self.assertNotIn('adding', keyboard)
        panel = (BAR / 'panels/BrightnessMenu.qml').read_text()
        for contract in ('MonitorMap {', 'settings: menu.displaySettings.monitors',
                         'pending: menu.pendingMonitor', 'menu.settingsFor = name'):
            self.assertIn(contract, panel)
        self.assertNotIn('MonitorMap {', (BAR / 'panels/DisplaySettingsEditor.qml').read_text())  # the Display panel draws the one map
        self.assertIn('setLineDash([5, 4])', (BAR / 'components/MonitorMap.qml').read_text())

    def test_panels_and_monitor_maps_offscreen(self):
        for theme, foreground, background in [('dark', '#e4e5ef', '#191b25'), ('light', '#202431', '#f5f3ee')]:
            with self.subTest(theme=theme), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                mocks = {
                    'DesktopData': '''property var topics: ({})
property var client: QtObject { function detachAction(identifier) {} }
function observe(topic, owner, interval) { return topic; }
function release(token) {}
function releaseOwner(owner) {}
function refresh(topic) {}''',
                    'DisplayService': '''property var topology: ({monitors: [], primary: ""})
function open(owner, interval) {}
function close(owner) {}
function pauseBrightness(owner) {}
function resumeBrightness(owner) {}
function pauseNightlight(owner) {}
function resumeNightlight(owner) {}
function refresh() {}
function refreshBrightness() {}''',
                    'PowerService': '''property var profile: ({available: false, profiles: []})
property var battery: ({available: false})
property bool busy: false
function observe(owner, interval, radios) { return []; }
function release(tokens) {}
function refresh() {}''',
                    'ObsStatus': '''property int detailObservers: 0
property var details: ({status: "idle"})
signal detailsReceived(var snapshot)
function refresh() {}''',
                }
                for name, body in mocks.items():
                    (folder / 'services' / f'{name}.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject {\n' + body + '\n}\n')
                # Keep production content; only replace layer-shell windows for the offscreen backend.
                picker_path = folder / 'panels/AppearancePicker.qml'
                picker = picker_path.read_text().replace('PanelWindow {', 'FloatingWindow {\n            implicitWidth: 1280; implicitHeight: 960')
                picker = re.sub(r'^\s*(?:anchors \{ top: true; bottom: true; left: true; right: true \}|exclusionMode:.*|WlrLayershell\..*)$', '', picker, flags=re.M)
                picker = picker.replace('id: picker', 'id: picker\n    readonly property alias previewItem: content')
                picker_path.write_text(picker)
                output_folder = capture_path('SETTINGS', directory, 'placeholder').parent
                fixture = (BAR / 'tests/fixtures/settings/shared-choices.qml.in').read_text()
                for original, replacement in {'FOREGROUND': foreground, 'BACKGROUND': background,
                                              'THEME': theme, 'OUTPUT': str(output_folder)}.items():
                    fixture = fixture.replace(original, replacement)
                (folder / 'fixture.qml').write_text(fixture)
                code, output = render(folder / 'fixture.qml', render_environment(folder, (1280, 960)), 25)
                self.assertEqual(code, 0, output)
                self.assertIn('SHARED_CHOICES_OK', output)
                for diagnostic in ('TypeError:', 'ReferenceError:', 'Unable to assign', 'Binding loop', 'Error:', 'FAIL!'):
                    self.assertNotIn(diagnostic, output)
                for name in ('WorkspaceStyleMenu', 'BrightnessMenu',
                             'DisplaySettingsEditor', 'RecordingMenu', 'PowerControls', 'AppearancePicker',
                             'monitor-one', 'monitor-two', 'monitor-rotated', 'monitor-trial'):
                    self.assertTrue((output_folder / f'{theme}-{name}.png').is_file(), name)
