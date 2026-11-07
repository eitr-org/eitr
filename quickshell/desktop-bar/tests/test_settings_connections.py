"""Settings > Connections: row-click connect, the single Scan action and Bluetooth grouping."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from layout_render import BAR, copy_runtime, render_environment, render, capture_path


class SettingsConnectionsTests(unittest.TestCase):
    def test_bluetooth_device_model(self):
        script = (BAR / 'components/BluetoothDevices.js').read_text() + '''
const assert = require('node:assert/strict');
const device = (name, fields) => Object.assign({name: name, address: '02:00:00:00:00:01', connected: false, paired: false, pairing: false}, fields || {});
const result = groups([device('zeta'), device('02-00-00-00-00-01'), device(''), device('Alpha', {paired: true}), device('Phone', {connected: true, paired: true}), device('Beta'), device('AA:BB:CC:DD:EE:FF')]);
assert.deepEqual(result.connected.map(entry => entry.name), ['Phone']);
assert.deepEqual(result.known.map(entry => entry.name), ['Alpha']);
assert.deepEqual(result.other.map(entry => entry.name), ['Beta', 'zeta']);
assert.equal(result.unnamed.length, 3);
assert.equal(named(device('02:00:00:00:00:01')), false);
assert.equal(glyph({icon: 'audio-headset'}), '\\u{F02CB}');
assert.equal(glyph({icon: 'input-keyboard'}), '\\u{F030C}');
assert.equal(glyph({icon: '', connected: true}), '\\u{F00B1}');
assert.equal(rowAction(device('New')), 'pair');
assert.equal(rowAction(device('Known', {paired: true})), 'connect');
assert.equal(rowAction(device('Busy', {pairing: true})), '');
assert.equal(rowAction(device('Live', {connected: true, paired: true})), '');
assert.equal(state(device('New'), 'pair'), 'pairing');
assert.equal(state(device('Known', {paired: true}), 'connect'), 'connecting');
assert.equal(state(device('02-00-00-00-00-01'), ''), 'unnamed');
assert.equal(batteryText({batteryAvailable: true, battery: 0.456}), '46%');
'''
        subprocess.run(['node', '-e', script], check=True, capture_output=True)

    def test_spinning_icons_turn_around_their_own_centre(self):
        # A Text turns around its line box, taller than the glyph, so the icon bobbed.
        spinner = (BAR / 'components/SpinningGlyph.qml').read_text()
        self.assertIn('height: width', spinner)
        self.assertIn('anchors.fill: parent', spinner)
        self.assertIn('verticalAlignment: Text.AlignVCenter', spinner)
        for name in ('components/PanelButton.qml', 'components/ConnectionRow.qml'):
            source = (BAR / name).read_text()
            self.assertIn('SpinningGlyph {', source)
            self.assertNotIn('RotationAnimator', source)

    def test_sources_share_the_panel_service_and_rows(self):
        devices = (BAR / 'settings/SettingsDevicesPage.qml').read_text()
        self.assertIn('SettingsBluetoothPage {', devices)
        self.assertNotIn('BluetoothMenu {', devices)
        bluetooth = (BAR / 'settings/SettingsBluetoothPage.qml').read_text()
        menu = (BAR / 'panels/BluetoothMenu.qml').read_text()
        for source in (bluetooth, menu):
            self.assertIn('BluetoothDiscovery {', source)
        self.assertIn('Bluetooth.defaultAdapter', bluetooth)
        wifi = (BAR / 'settings/SettingsWifiPage.qml').read_text()
        for source in (bluetooth, wifi):
            self.assertIn('headerActions: PanelButton {', source)
        self.assertIn('ConnectionRow {', wifi)
        # Settings and the bar panel share one device row and one connect flow.
        self.assertIn('BluetoothDeviceRow {', bluetooth)
        self.assertIn('ConnectionRow {', (BAR / 'components/BluetoothDeviceRow.qml').read_text())
        self.assertIn('ToggleRow {', wifi)
        self.assertNotIn('"Refresh"', wifi)
        self.assertIn('SettingsWifiCredentials {', wifi)
        qmldir = (BAR / 'qmldir').read_text()
        for entry in ('SettingsBluetoothPage settings/SettingsBluetoothPage.qml', 'ConnectionRow components/ConnectionRow.qml',
                      'BluetoothDiscovery components/BluetoothDiscovery.qml'):
            self.assertIn(entry, qmldir)

    def test_rows_connect_on_click_offscreen(self):
        for theme, foreground, background in [('dark', '#e4e5ef', '#191b25'), ('light', '#202431', '#f5f3ee')]:
            with self.subTest(theme=theme), tempfile.TemporaryDirectory(prefix='settings-connections-') as directory:
                folder = Path(directory)
                copy_runtime(folder)
                output = capture_path('SETTINGS', directory, 'placeholder').parent
                fixture = (BAR / 'tests/fixtures/settings/connections.qml.in').read_text()
                for original, replacement in {'FOREGROUND': foreground, 'BACKGROUND': background, 'PALETTE': theme, 'OUTPUT': str(output)}.items():
                    fixture = fixture.replace(original, replacement)
                (folder / 'fixture.qml').write_text(fixture)
                code, result = render(folder / 'fixture.qml', render_environment(folder, (1760, 1000)), 60)
                self.assertEqual(code, 0, result)
                self.assertIn('CONNECTIONS_OK', result)
                for diagnostic in ('FAIL!', 'TypeError:', 'ReferenceError:', 'Binding loop', 'Unable to assign'):
                    self.assertNotIn(diagnostic, result)
                self.assertTrue((output / f'connections-{theme}.png').is_file())


if __name__ == '__main__':
    unittest.main()
