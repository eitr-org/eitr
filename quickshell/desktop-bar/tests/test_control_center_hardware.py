import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

battery = load('battery')
airplane = load('airplane')
power = load('power-profile')

class BatteryTests(unittest.TestCase):
    def supply(self, root, name, **values):
        path = root / name
        path.mkdir()
        for key, value in values.items():
            (path / key).write_text(str(value))
        return path

    def test_desktop_and_peripheral_battery_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(battery.status(root)['available'])
            self.supply(root, 'mouse', type='Battery', scope='Device', capacity=75, status='Discharging')
            self.assertFalse(battery.status(root)['available'])
            with patch.object(power, 'POWER_SUPPLY', root):
                self.assertFalse(power.has_battery())

    def test_laptop_percentage_health_and_estimate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.supply(root, 'battery', type='Battery', scope='System', present=1,
                        capacity=50, status='Discharging', energy_now=30, energy_full=60,
                        energy_full_design=75, power_now=10)
            result = battery.status(root)
            self.assertTrue(result['available'])
            self.assertEqual((result['percent'], result['health'], result['hours']), (50, 80, 3))
            with patch.object(power, 'POWER_SUPPLY', root):
                self.assertTrue(power.has_battery())

    def test_absent_battery_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.supply(root, 'BAT0', type='Battery', present=0)
            self.assertFalse(battery.status(root)['available'])

class AirplaneTests(unittest.TestCase):
    devices = [{'id': 0, 'type': 'wlan', 'soft': 'unblocked', 'hard': 'unblocked'},
               {'id': 1, 'type': 'bluetooth', 'soft': 'blocked', 'hard': 'unblocked'}]

    def test_status_is_read_only(self):
        with patch.object(airplane, 'radios', return_value=self.devices), patch.object(airplane.subprocess, 'run') as run:
            self.assertFalse(airplane.status()['enabled'])
            run.assert_not_called()

    def test_restore_does_not_enable_previously_disabled_bluetooth(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(airplane, 'radios', return_value=self.devices), patch.object(airplane.subprocess, 'run') as run:
            state = Path(directory) / 'state.json'
            with patch.object(airplane, 'STATE', state):
                airplane.set_enabled(True)
                self.assertEqual(state.read_text(), '["0"]')
                run.reset_mock()
                airplane.set_enabled(False)
                self.assertEqual(run.call_args.args[0], ['rfkill', 'unblock', '0'])
                self.assertEqual(run.call_count, 1)
                self.assertFalse(state.exists())

    def test_external_blocks_require_individual_enable(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(airplane, 'radios', return_value=self.devices), patch.object(airplane.subprocess, 'run') as run:
            with patch.object(airplane, 'STATE', Path(directory) / 'missing.json'):
                with self.assertRaises(ValueError):
                    airplane.set_enabled(False)
            run.assert_not_called()

class ControlCenterContracts(unittest.TestCase):
    def test_notifications_have_only_the_dedicated_panel(self):
        center = (Path(__file__).parents[1] / 'ControlCenter.qml').read_text()
        self.assertNotIn('key: "notifications"', center)
        self.assertNotIn('NotificationList {', center)
        self.assertNotIn('service.centerOpen =', center)

    def test_shared_sliders_use_pointer_when_enabled(self):
        slider = (Path(__file__).parents[1] / 'PanelSlider.qml').read_text()
        self.assertIn('HoverHandler {', slider)
        self.assertIn('slider.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor', slider)

    def test_general_controls_have_ordered_groups(self):
        center = (Path(__file__).parents[1] / 'ControlCenter.qml').read_text()
        names = ['Connectivity', 'Quick Actions', 'Sound', 'Display', 'Media', 'Power']
        positions = [center.index('text: Eitr.I18n.tr("' + name + '"); width: parent.width') for name in names]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('text: "Sound & Display"', center)
        # Night Light is a quick toggle; its schedule lives under System.
        self.assertIn('title: Eitr.I18n.tr("Night Light")', center)
        self.assertIn('title: Eitr.I18n.tr("Night Light & Main Display")', center)

    def test_single_background_media_popup(self):
        root = Path(__file__).parents[1]
        self.assertIn('property bool cardBackground: true', (root / 'MediaCard.qml').read_text())
        self.assertIn('cardBackground: false', (root / 'MediaMenu.qml').read_text())

    def test_control_center_groups_and_reset(self):
        root = Path(__file__).parents[1]
        center = (root / 'ControlCenter.qml').read_text()
        self.assertIn('onVisibleChanged: if (!visible)', center)
        self.assertNotIn('key: "toggles"', center)
        self.assertNotIn('details: true', center)
        self.assertIn('glyph: center.wifiGlyph', center)
        self.assertIn('WorkspaceMarker {', center)
        for title in ('Lock', 'Logout', 'Suspend', 'Reboot', 'Shutdown'):
            self.assertIn('title: Eitr.I18n.tr("' + title + '")', center)
        self.assertNotIn('BIOS', center)
        # Keyboard layouts stay inline; the Display panel adds what the inline controls lack
        # (resolution, refresh rate and scale).
        self.assertNotIn('center.panelRequested("keyboard")', center)
        self.assertIn('center.panelRequested("display")', center)
        self.assertEqual((root / 'assets/eitr-logo-white.svg').read_bytes(),
                         (root.parents[1] / 'branding/svg/eitr-logo-white.svg').read_bytes())

    def test_workspace_style_updates_immediately_from_both_menus(self):
        shell = (Path(__file__).parents[1] / 'shell.qml').read_text()
        self.assertIn('onWorkspaceStyleRequested: function(value) { shell.setWorkspaceStyle(value); }', shell)
        self.assertIn('shell.setWorkspaceStyle(style);', shell)
        preferences = (Path(__file__).parents[1] / 'BarPreferences.qml').read_text()
        setter = preferences.split('function setWorkspaceStyle(style) {', 1)[1].split('\n    }', 1)[0]
        self.assertLess(setter.index('host.workspaceStyle = style;'),
                        setter.index('saveWorkspaceStyle.running = true;'))

    def test_shared_surface_and_edge_animation(self):
        root = Path(__file__).parents[1]
        center = (root / 'ControlCenter.qml').read_text()
        self.assertIn('ThemedPopup {', center)
        self.assertIn('barEdge: barPosition', center)
        self.assertNotIn('\n    x:', center)
        self.assertNotIn('\n    y:', center)
        self.assertIn('MediaCard {', center)
        shell = (root / 'shell.qml').read_text()
        self.assertIn('Region { item: controlCenter.opened ? controlCenter : null }', shell)
        self.assertIn('onDetailsRequested: bar.togglePanel(mediaMenu)', shell)

if __name__ == '__main__':
    unittest.main()


class HardwareSubscriberTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell unavailable")
    def test_panel_demand_lifetime_retained_errors_and_control_center_entry(self):
        bar = Path(__file__).parents[1]
        self.assertIn('center.panelRequested("hardware")', (bar / 'ControlCenter.qml').read_text())
        self.assertNotIn('hardwareIdentity', (bar / 'shell.qml').read_text())
        panel = (bar / 'SystemMonitorMenu.qml').read_text()
        self.assertNotIn('Process {', panel)
        self.assertNotIn('Timer {', panel)
        with tempfile.TemporaryDirectory(prefix="eitr-hardware-test-") as directory:
            root = Path(directory)
            (root / 'SystemMonitorMenu.qml').write_text(panel[:panel.index('    Flickable {')] + '}\n')
            shutil.copy(bar / 'PanelStyle.js', root / 'PanelStyle.js')
            (root / 'ThemedPopup.qml').write_text("""
import QtQuick
Item {
    property bool opened: false
    property bool waitForFreshData: false
    property bool leftAligned: false
    property real verticalContentInset: 0
    property var content: ({implicitHeight: 20})
    function updateContent(action) { action(); }
    function applySnapshot(name, value) { this[name] = value; }
}
""")
            (root / 'DesktopData.qml').write_text("""
pragma Singleton
import QtQuick
QtObject {
    property var topics: ({})
    property var tokens: []
    property int serial: 0
    function observe(topic, owner) {
        const token = {id: ++serial, owner: owner};
        tokens = tokens.concat([token]);
        return String(token.id);
    }
    function release(token) { tokens = tokens.filter(entry => String(entry.id) !== token); }
    function releaseOwner(owner) { tokens = tokens.filter(entry => entry.owner !== owner); }
    function refresh(topic) {}
}
""")
            (root / 'qmldir').write_text('singleton DesktopData DesktopData.qml\nSystemMonitorMenu SystemMonitorMenu.qml\nThemedPopup ThemedPopup.qml\n')
            (root / 'shell.qml').write_text("""
import QtQuick
import Quickshell
ShellRoot {
    id: harness
    property var first: null
    property var second: null
    property int phase: 0
    function check(condition, message) {
        if (!condition) { console.error("HARDWARE FAIL", message); Qt.exit(1); }
    }
    Component { id: panel; SystemMonitorMenu {} }
    Timer {
        interval: 50; repeat: true; running: true
        onTriggered: {
            if (harness.phase === 0) {
                harness.first = panel.createObject(harness);
                harness.second = panel.createObject(harness);
                harness.check(DesktopData.tokens.length === 0, "closed panels have no demand");
                harness.first.opened = true; harness.second.opened = true;
                harness.check(DesktopData.tokens.length === 2, "two subscribers");
                DesktopData.topics = {"hardware.details": {status: "ready", data: {
                    identity: {cpu: "fixture"}, sections: [{title: "CPU", usage: 75}]}}};
            } else if (harness.phase === 1) {
                harness.check(harness.first.sections[0].usage === 75 && harness.second.sections[0].usage === 75, "same snapshot");
                DesktopData.topics = {"hardware.details": {status: "stale", data: DesktopData.topics["hardware.details"].data}};
            } else if (harness.phase === 2) {
                harness.check(harness.first.error === "Hardware information unavailable", "translated error boundary");
                harness.check(harness.first.sections[0].usage === 75, "retain last sections");
                harness.first.opened = false;
                harness.check(DesktopData.tokens.length === 1, "close releases demand");
                harness.second.destroy();
            } else {
                harness.check(DesktopData.tokens.length === 0, "destruction releases demand");
                console.log("HARDWARE PASS"); Qt.quit();
            }
            harness.phase++;
        }
    }
}
""")
            runtime = root / 'runtime'
            runtime.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QML_IMPORT_PATH=str(bar.parent),
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', XDG_RUNTIME_DIR=str(runtime),
                               HYPRLAND_INSTANCE_SIGNATURE='')
            for kind in ('CONFIG', 'CACHE', 'STATE', 'DATA'):
                environment[f'XDG_{kind}_HOME'] = str(root / kind.lower())
            for name in ('WAYLAND_DISPLAY', 'DISPLAY', 'QS_CONFIG_PATH', 'QS_CONFIG_NAME'):
                environment.pop(name, None)
            result = subprocess.run(['quickshell', '--no-color', '-p', str(root / 'shell.qml')],
                                    env=environment, capture_output=True, text=True, timeout=10)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('HARDWARE PASS', output)
            self.assertNotIn('ReferenceError', output)
            self.assertNotIn('TypeError', output)
