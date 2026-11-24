"""Exercise the real reload coordinator in a disposable offscreen shell."""
from pathlib import Path
import shutil
import tempfile
import unittest

from layout_render import BAR, render, render_environment

FIXTURE = '''import QtQuick
import Quickshell
import Quickshell.Io
import "." as Bar

ShellRoot {
    id: root
    property bool panelOpen: true
    property bool storeOpen: false
    function expect(condition, message) {
        if (condition) return true;
        console.error(message);
        Qt.exit(1);
        return false;
    }
    PersistentProperties {
        id: session
        reloadableId: "fixture-session"
        property double closedAt: 0
        property string timestampsJson: "{}"
        property string repeatsJson: "{}"
        onReloaded: {
            const elapsed = Date.now() - closedAt;
            const timestamps = JSON.parse(timestampsJson);
            const repeats = JSON.parse(repeatsJson);
            if (!root.expect(closedAt > 0 && elapsed >= 700, "Reloaded while busy")) return;
            if (!root.expect(timestamps["42"] === 12345 && repeats["42"] === 3, "Lost persistent notification metadata")) return;
            console.log("BAR_RELOAD_OK", elapsed);
            Qt.callLater(Qt.quit);
        }
    }
    FileView {
        id: writer
        path: Quickshell.shellDir + "/version"
        atomicWrites: true
    }
    Bar.BarReload {
        id: coordinator
        versionPath: writer.path
        packageLockPath: PACKAGE_LOCK
        pluginRevision: "[]"
        busy: root.panelOpen || root.storeOpen
    }
    Timer {
        interval: 300
        running: true
        onTriggered: {
            if (!root.expect(coordinator.loadedVersion === "1" && !coordinator.pending, "Initial load queued a reload")) return;
            session.timestampsJson = JSON.stringify({"42": 12345});
            session.repeatsJson = JSON.stringify({"42": 3});
            TRIGGER
        }
    }
    Timer {
        interval: 1300
        running: true
        onTriggered: {
            if (!root.expect(coordinator.pending, "No pending reload after update")) return;
            root.storeOpen = true;
            root.panelOpen = false;
        }
    }
    Process {
        id: unlock
        command: ["rm", "--", coordinator.packageLockPath]
    }
    Timer {
        interval: 2300
        running: true
        onTriggered: {
            if (!root.expect(coordinator.pending, "Pending state lost while Store open")) return;
            if (!WAIT_FOR_LOCK) session.closedAt = Date.now();
            root.storeOpen = false;
        }
    }
    Timer {
        interval: 3300
        running: true
        onTriggered: {
            if (!WAIT_FOR_LOCK) return;
            if (!root.expect(coordinator.pending, "Reloaded while package transaction active")) return;
            session.closedAt = Date.now();
            unlock.running = true;
        }
    }
}
'''


class BarReloadTests(unittest.TestCase):
    def test_update_waits_for_panel_and_store_then_reloads_once(self):
        triggers = {
            'package': 'writer.setText("2\\n");',
            'plugin': 'coordinator.pluginRevision = \'[["sample","new"]]\';',
            'ipc': 'coordinator.request();',
        }
        for source, trigger in triggers.items():
            with self.subTest(source=source), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                services = path / 'services'
                services.mkdir()
                shutil.copy(BAR / 'services/BarReload.qml', services)
                (path / 'qmldir').write_text('BarReload services/BarReload.qml\n')
                (path / 'version').write_text('1\n')
                if source == 'package':
                    (path / 'db.lck').touch(mode=0)
                shell = path / 'shell.qml'
                lock = 'Quickshell.shellDir + "/db.lck"' if source != 'plugin' else '""'
                shell.write_text(FIXTURE.replace('TRIGGER', trigger).replace('PACKAGE_LOCK', lock)
                                 .replace('WAIT_FOR_LOCK', 'true' if source == 'package' else 'false'))
                code, output = render(shell, render_environment(directory), 30)
                self.assertEqual(code, 0, output)
                self.assertIn('BAR_RELOAD_OK', output)
                self.assertEqual(output.count('Reloading the desktop bar after an update'), 1, output)

    def test_bar_ipc_requests_the_same_idle_reload(self):
        preferences = (BAR / 'services/BarPreferences.qml').read_text()
        self.assertIn('target: "bar"', preferences)
        self.assertIn('function reload(): void { preferences.host.requestBarReload(); }', preferences)
        shell = (BAR / 'shell.qml').read_text()
        self.assertIn('function requestBarReload() { barReload.request(); }', shell)
        for blocker in (
            'catalogWindow.opened', 'settingsWindow.opened', 'clockWindow.opened', 'welcome.opened',
            'desktopAppearance.opened', 'timePicker.opened', 'beautify.opened', 'pins.entries.length > 0',
            'polkit.showing', 'cleanOverlay.active', 'PluginRegistry.editing', '!!PluginRegistry.menuTarget',
            'pluginDesktop.focusedWidgets.length > 0', 'PluginRegistry.refreshing',
            'notificationsService.popupIds.length > 0', 'shell.barPointerHeld',
            'ObsStatus.reloadBlocked', 'Object.values(shell.barsByScreen).some(bar => bar.reloadBusy)',
        ):
            self.assertIn(blocker, shell)
        bar_window = (BAR / 'bar/BarWindow.qml').read_text()
        self.assertIn('readonly property bool reloadBusy: panelOpen || overviewOpen || pendingPanel !== null', bar_window)
        self.assertIn('pointerInside || edgeDock.interacting || autoHide.held || choicePopups.length > 0', bar_window)
        self.assertIn('reloadableId: "notificationHistory"', (BAR / 'notifications/NotificationService.qml').read_text())
        self.assertIn('reloadableId: "updatesSession"', (BAR / 'services/UpdatesStatus.qml').read_text())


if __name__ == '__main__':
    unittest.main()
