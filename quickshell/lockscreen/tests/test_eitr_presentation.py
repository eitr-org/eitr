"""Exercise instant submission, preview dismissal and rune deletion without a lock."""
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
        self.assertIn('shell.unlocked = true', callback)
        self.assertIn('Quickshell.execDetached(["loginctl", "unlock-session"])', callback)
        self.assertIn('quitTimer.start()', callback)
        self.assertNotIn('releaseTimer', source)
        self.assertIn('interval: 200; onTriggered: Qt.quit()', source)

    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell is needed for offscreen mock verification')
    def test_submission_preview_and_rune_deletion(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'fixture.qml'
            fixture.write_text('''import QtQuick
import QtQuick.Window
import Quickshell
import "''' + (ROOT / 'themes/eitr').as_uri() + '''" as Design
ShellRoot {
    id: host
    property var config: ({reduceMotion: false, themeMode: "dark"})
    property bool isLockPreview: false
    property var sddm: bridge
    property var userModel: users
    ListModel { id: users; property int lastIndex: 0; ListElement { name: "astrid" } ListElement { name: "bjorn" } }
    property var sessionModel: null
    property int previews: 0
    QtObject {
        id: bridge
        property bool quickshellLock: true
        property int calls: 0
        property string supplied: ""
        signal loginFailed()
        signal loginSucceeded()
        function login(user, password, session) { calls++; supplied = password; }
    }
    TextInput { id: runeInput }
    Design.CarvedRunes { id: runes; input: runeInput; width: 500; height: 40 }
    function rubbleCount() {
        let count = 0;
        for (const child of runes.children) if (child.objectName === "eitrRuneRubble") count++;
        return count;
    }
    function require(value, message) { if (!value) throw new Error(message); }
    Window {
        width: 800; height: 600; visible: true
        Loader { id: design; anchors.fill: parent; source: "''' + (ROOT / 'themes/eitr/Main.qml').as_uri() + '''" }
        Timer {
            interval: 500; running: true
            onTriggered: {
                try {
                    runeInput.text = "abc";
                    runes.sync();
                    runeInput.text = "";
                    runes.sync();
                    host.require(host.rubbleCount() === 0, "Programmatic clearing must not crumble");
                    runeInput.text = "abc";
                    runes.sync();
                    runeInput.cursorPosition = 2;
                    runes.deleteRune(true);
                    host.require(runeInput.text === "ac" && host.rubbleCount() === 1, "Backspace must crumble one rune");
                    runes.deleteRune(false);
                    host.require(runeInput.text === "a" && host.rubbleCount() === 2, "Delete must crumble one rune");
                    const item = design.item;
                    host.require(!!item, "Design failed to load");
                    item.previewFinished.connect(function() { host.previews++; });
                    // Text input is found by its public fixture name, rather than layout position.
                    function find(parentItem, name) {
                        if (parentItem.objectName === name) return parentItem;
                        for (const child of parentItem.children) { const result = find(child, name); if (result) return result; }
                        return null;
                    }
                    const password = find(item, "eitrPassword");
                    const echo = find(item, "eitrCarvedRunes");
                    function requireClear(message) {
                        echo.sync();
                        let rubble = 0;
                        for (const child of echo.children) if (child.objectName === "eitrRuneRubble") rubble++;
                        host.require(password.text === "" && rubble === 0, message);
                    }
                    password.text = "mock-password";
                    echo.sync();
                    item.submit();
                    host.require(bridge.calls === 1 && bridge.supplied === "mock-password", "Real submit must reach controller immediately");
                    host.require(password.text === "", "Submission clears password");
                    requireClear("Submission must not crumble");
                    password.text = "failed-password";
                    echo.sync();
                    bridge.loginFailed();
                    requireClear("Failed login must clear without crumbling");
                    password.text = "switch-password";
                    echo.sync();
                    bridge.quickshellLock = false;
                    find(item, "userPicker").controller.cycleUser();
                    bridge.quickshellLock = true;
                    requireClear("Account switching must clear without crumbling");
                    host.require(find(item, "eitrFeedback").text.length > 0, "Wrong-password feedback missing");
                    host.config = {reduceMotion: true, themeMode: "dark"};
                    host.isLockPreview = true;
                    password.text = "never-authenticate";
                    item.submit();
                    host.require(bridge.calls === 1 && host.previews === 1, "Reduced preview must close without authentication");
                    host.config = {reduceMotion: false, themeMode: "dark"};
                    item.dismissPreview();
                    host.require(host.previews === 2, "Preview must close immediately with motion enabled");
                    finish.start();
                } catch (error) { console.error(error); Qt.exit(1); }
            }
        }
        Timer {
            id: finish; interval: 1100
            onTriggered: {
                if (host.previews !== 2 || Math.round(design.item.ringAngle / 6) % 60 !== design.item.now.getSeconds()) Qt.exit(1);
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
