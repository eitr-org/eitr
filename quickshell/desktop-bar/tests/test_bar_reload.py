"""Exercise the real reload coordinator in a disposable offscreen shell."""
import os
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
    property bool revisionReady: false
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
        property string revision: "[]"
        property bool reloaded: false
        onReloaded: {
            const elapsed = Date.now() - closedAt;
            const timestamps = JSON.parse(timestampsJson);
            const repeats = JSON.parse(repeatsJson);
            const requiredQuiet = WAIT_FOR_LOCK && !MANAGED ? 5000 : 700;
            if (!root.expect(closedAt > 0 && elapsed >= requiredQuiet, "Reloaded before the update settled")) return;
            if (!root.expect(timestamps["42"] === 12345 && repeats["42"] === 3, "Lost persistent notification metadata")) return;
            if (!root.expect(!WAIT_FOR_LOCK || revision === '[["sample","bundled"]]', "Skipped the bundled plugin refresh")) return;
            console.log("BAR_RELOAD_OK", elapsed);
            reloaded = true;
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
        pluginRevision: root.revisionReady ? session.revision : ""
        onRefreshPlugins: session.revision = '[["sample","bundled"]]';
        busy: root.panelOpen || root.storeOpen
    }
    Timer {
        interval: 100
        running: true
        onTriggered: root.revisionReady = true
    }
    Timer {
        interval: 300
        running: !session.reloaded
        onTriggered: {
            if (!root.expect(coordinator.loadedVersion === "1" && !coordinator.pending, "Initial load queued a reload")) return;
            coordinator.request();
            if (!root.expect(!coordinator.pending, "IPC without a change queued a reload")) return;
            session.timestampsJson = JSON.stringify({"42": 12345});
            session.repeatsJson = JSON.stringify({"42": 3});
            TRIGGER
        }
    }
    Timer {
        interval: 1300
        running: !session.reloaded
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
        running: !session.reloaded
        onTriggered: {
            if (!root.expect(coordinator.pending, "Pending state lost while Store open")) return;
            if (!WAIT_FOR_LOCK && !MANAGED) session.closedAt = Date.now();
            root.storeOpen = false;
        }
    }
    Timer {
        interval: 3300
        running: !session.reloaded
        onTriggered: {
            if (!WAIT_FOR_LOCK) return;
            if (!root.expect(coordinator.pending, "Reloaded while package transaction active")) return;
            if (!MANAGED) session.closedAt = Date.now();
            unlock.running = true;
        }
    }
    Process {
        id: finishUpdate
        command: ["rm", "--", coordinator.updateMarkerPath]
        onExited: coordinator.request()
    }
    Timer {
        interval: 4500
        running: MANAGED && !session.reloaded
        onTriggered: session.revision = '[["sample","new"]]';
    }
    Timer {
        interval: 10500
        running: MANAGED && !session.reloaded
        onTriggered: {
            if (!root.expect(coordinator.pending, "Reloaded while System Update was active")) return;
            session.closedAt = Date.now();
            finishUpdate.running = true;
        }
    }
    Timer {
        interval: 500
        running: session.reloaded
        onTriggered: {
            coordinator.request();
            root.expect(!coordinator.pending, "Duplicate IPC queued a reload");
        }
    }
    Timer {
        interval: 1500
        running: session.reloaded
        onTriggered: Qt.quit()
    }
}
'''


class BarReloadTests(unittest.TestCase):
    def test_update_waits_for_panel_and_store_then_reloads_once(self):
        triggers = {
            'package': 'writer.setText("2\\n");',
            'plugin': 'session.revision = \'[["sample","new"]]\';',
            'system': 'writer.setText("2\\n"); coordinator.request();',
            'stale-marker': 'session.revision = \'[["sample","new"]]\';',
        }
        for source, trigger in triggers.items():
            with self.subTest(source=source), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                services = path / 'services'
                services.mkdir()
                shutil.copy(BAR / 'services/BarReload.qml', services)
                (path / 'qmldir').write_text('BarReload services/BarReload.qml\n')
                (path / 'version').write_text('1\n')
                wait_for_lock = source in ('package', 'system')
                if wait_for_lock:
                    (path / 'db.lck').touch(mode=0)
                if source in ('system', 'stale-marker'):
                    (path / 'eitr').mkdir()
                    owner = os.getpid() if source == 'system' else 2147483647
                    (path / 'eitr/system-update.pid').write_text(f'{owner}\n')
                shell = path / 'shell.qml'
                lock = 'Quickshell.shellDir + "/db.lck"' if wait_for_lock else '""'
                shell.write_text(FIXTURE.replace('TRIGGER', trigger).replace('PACKAGE_LOCK', lock)
                                 .replace('WAIT_FOR_LOCK', str(wait_for_lock).lower())
                                 .replace('MANAGED', str(source == 'system').lower()))
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
