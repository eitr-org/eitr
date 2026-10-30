"""Exercise design submission and optional post-unlock capture without PAM or a lock."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EitrPresentationTests(unittest.TestCase):
    def test_authentication_releases_lock_before_any_cosmetic_wait(self):
        source = (ROOT / 'shell.qml').read_text()
        callback = source.split('onAuthenticated: {', 1)[1].split('}', 1)[0]
        self.assertIn('shell.authenticated = true', callback)
        self.assertIn('releaseTimer.start()', callback)
        self.assertNotIn('grabToImage', callback)
        self.assertNotIn('animation', callback.lower())
        # The lock is held at most 150 ms for the effect, then released before the process quits.
        release = source.split('id: releaseTimer', 1)[1].split('Timer { id: quitTimer', 1)[0]
        self.assertIn('interval: shell.sweepEnabled ? 150 : 0', release)
        self.assertLess(release.index('shell.unlocked = true'), release.index('quitTimer.start()'))
        overlay = (ROOT / 'UnlockOverlay.qml').read_text()
        self.assertIn('WlrKeyboardFocus.None', overlay)
        self.assertIn('mask: Region {}', overlay)
        self.assertIn('interval: 1250', overlay)
        self.assertIn('effect.expired = true', overlay)

    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell is needed for offscreen mock verification')
    def test_submission_preview_and_late_snapshot_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'fixture.qml'
            fixture.write_text('''import QtQuick
import QtQuick.Window
import Quickshell
import "''' + ROOT.as_uri() + '''" as Lock
ShellRoot {
    id: host
    property var config: ({reduceMotion: true, themeMode: "dark"})
    property bool isLockPreview: false
    property var sddm: bridge
    property var userModel: null
    property var sessionModel: null
    property int previews: 0
    property int captures: 0
    QtObject {
        id: bridge
        property bool quickshellLock: true
        property int calls: 0
        property string supplied: ""
        signal loginFailed()
        signal loginSucceeded()
        function login(user, password, session) { calls++; supplied = password; }
    }
    Lock.UnlockSnapshots { id: effect; reduced: false }
    QtObject {
        id: source
        property var callback: null
        property int grabs: 0
        property bool shouldThrow: false
        function grabToImage(callback) { grabs++; if (shouldThrow) throw new Error("Mock capture failure"); this.callback = callback; }
    }
    function require(value, message) { if (!value) throw new Error(message); }
    Window {
        width: 800; height: 600; visible: true
        Loader { id: design; anchors.fill: parent; source: "''' + (ROOT / 'themes/eitr/Main.qml').as_uri() + '''" }
        Timer {
            interval: 500; running: true
            onTriggered: {
                try {
                    const item = design.item;
                    host.require(!!item, "Design failed to load");
                    item.captureRequested.connect(function() { host.captures++; });
                    item.previewFinished.connect(function() { host.previews++; });
                    // Text input is found by its public fixture name, rather than layout position.
                    function find(parentItem, name) {
                        if (parentItem.objectName === name) return parentItem;
                        for (const child of parentItem.children) { const result = find(child, name); if (result) return result; }
                        return null;
                    }
                    const password = find(item, "eitrPassword");
                    password.text = "mock-password";
                    item.submit();
                    host.require(bridge.calls === 1 && bridge.supplied === "mock-password", "Real submit must reach controller immediately");
                    host.require(password.text === "" && host.captures === 1, "Capture follows field clearing");
                    bridge.loginFailed();
                    host.require(find(item, "eitrFeedback").text.length > 0, "Wrong-password feedback missing");
                    host.isLockPreview = true;
                    password.text = "never-authenticate";
                    item.submit();
                    host.require(bridge.calls === 1 && host.previews === 1, "Reduced preview must close without authentication");
                    effect.capture(source, "mock");
                    effect.authenticated = true;
                    source.callback({url: "file:///mock"});
                    // PAM usually answers before the grab finishes; that capture is the one the effect shows.
                    host.require(Object.keys(effect.snapshots).length === 1, "A capture started before authentication must be kept");
                    effect.capture(source, "mock");
                    host.require(source.grabs === 1, "No new capture may start after authentication");
                    effect.authenticated = false;
                    effect.capture(source, "mock");
                    source.callback({url: "file:///mock"});
                    host.require(Object.keys(effect.snapshots).length === 1, "Valid capture was not retained");
                    effect.resetCapture();
                    source.callback({url: "file:///stale"});
                    host.require(Object.keys(effect.snapshots).length === 0, "Previous-attempt callbacks must be ignored");
                    source.shouldThrow = true;
                    effect.capture(source, "mock");
                    effect.reduced = true;
                    effect.capture(source, "mock");
                    host.require(source.grabs === 3, "Reduced motion must skip capture");
                    host.config = {reduceMotion: false, themeMode: "dark"};
                    item.dismissPreview();
                    finish.start();
                } catch (error) { console.error(error); Qt.exit(1); }
            }
        }
        Timer {
            id: finish; interval: 1100
            onTriggered: {
                if (host.previews !== 2 || design.item.sweepProgress < 1
                    || Math.round(design.item.ringAngle / 6) % 60 !== design.item.now.getSeconds()) Qt.exit(1);
                else { console.log("EITR_PRESENTATION_OK"); Qt.quit(); }
            }
        }
        Timer { interval: 5000; running: true; onTriggered: Qt.exit(1) }
    }
}''')
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=os.pathsep.join((str(ROOT.parent), str(ROOT / 'imports'))),
                               XDG_RUNTIME_DIR=temporary, XDG_CONFIG_HOME=temporary, XDG_CACHE_HOME=temporary,
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
            result = subprocess.run(['quickshell', '-n', '-p', str(fixture)], env=environment,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('EITR_PRESENTATION_OK', result.stdout + result.stderr)
