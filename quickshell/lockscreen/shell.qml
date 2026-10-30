import Eitr as Eitr
import QtQuick
import Quickshell
import Quickshell.Wayland
import "themes/eitr/Spectrum.js" as Spectrum

ShellRoot {
    Component.onCompleted: Quickshell.watchFiles = Quickshell.env("EITR_LIVE_RELOAD") === "1"
    id: shell
    readonly property string themePath: Quickshell.env("DESKTOP_LOCK_THEME")
    readonly property var config: JSON.parse(Quickshell.env("DESKTOP_LOCK_CONFIG") || "{}")
    readonly property var sddm: auth.sddm
    readonly property var userModel: auth.userModel
    readonly property var sessionModel: auth.sessionModel
    readonly property var keyboard: keyboardState
    property bool authenticated: false
    property bool unlocked: false
    readonly property bool sweepEnabled: themePath.endsWith("/eitr") && config.reduceMotion !== true
    signal snapshotAll()
    Loader {
        id: exitEffect
        active: shell.sweepEnabled
        asynchronous: true
        source: "UnlockOverlay.qml"
        onLoaded: {
            item.authenticated = Qt.binding(function() { return shell.authenticated; });
            // WlSessionLock.locked still reads true after release; secure reports the compositor's state.
            item.locked = Qt.binding(function() { return !shell.unlocked; });
            item.secure = Qt.binding(function() { return sessionLock.secure; });
            item.reduced = !shell.sweepEnabled;
            item.spectrum = Spectrum.colors(config.themeMode === "light");
            item.style = config.unlockEffect || "bifrost";
        }
    }
    function capture(item, screenName) {
        if (exitEffect.item) exitEffect.item.capture(item, screenName);
    }

    QtObject { id: keyboardState; property bool numLock: false }
    AuthAdapter {
        id: auth
        // Previews run preview.qml instead; this shell always holds a real lock.
        preview: false
        onAuthenticated: {
            shell.authenticated = true;
            releaseTimer.start();
        }
    }

    // With the unlock effect, the lock is held 150 ms longer so the effect's
    // surface is already drawn beneath it when the desktop is revealed.
    Timer {
        id: releaseTimer
        interval: shell.sweepEnabled ? 150 : 0
        onTriggered: {
            shell.unlocked = true;
            Quickshell.execDetached(["loginctl", "unlock-session"]);
            quitTimer.start();
        }
    }
    Timer { id: quitTimer; interval: shell.sweepEnabled ? 1200 : 200; onTriggered: Qt.quit() }

    Component {
        id: themeSurface
        Item {
            // Session-lock surfaces report no Window.screen; the surface passes its own.
            property string screenName: ""
            Connections {
                target: shell
                function onSnapshotAll() { shell.capture(theme.item, screenName); }
            }
            Loader {
                id: theme
                anchors.fill: parent
                asynchronous: true
                // Create the lock surface before loading the presentation.
                Component.onCompleted: Qt.callLater(function() {
                    theme.source = "file://" + shell.themePath + "/Main.qml";
                })
                onLoaded: {
                    item.forceActiveFocus();
                    if (shell.sweepEnabled && item.captureRequested)
                        item.captureRequested.connect(function() {
                            if (exitEffect.item) exitEffect.item.resetCapture();
                            shell.snapshotAll();
                        });
                }
            }
            Rectangle {
                anchors.fill: parent
                visible: theme.status === Loader.Error
                color: "#181824"
                Column {
                    anchors.centerIn: parent
                    spacing: 16
                    Text { text: Eitr.I18n.tr("Unlock"); color: "white"; font.pixelSize: 24 }
                    TextInput {
                        id: fallbackPassword
                        width: 280
                        height: 36
                        color: "white"
                        echoMode: TextInput.Password
                        focus: parent.parent.visible
                        onAccepted: {
                            auth.sddm.login(Quickshell.env("USER"), text, 0);
                            text = "";
                        }
                    }
                }
            }
        }
    }

    WlSessionLock {
        id: sessionLock
        locked: !shell.unlocked
        surface: WlSessionLockSurface {
            id: lockSurface
            color: "black"
            Loader {
                anchors.fill: parent
                sourceComponent: themeSurface
                onLoaded: item.screenName = Qt.binding(function() { return lockSurface.screen ? lockSurface.screen.name : ""; })
            }
        }
    }
}
