import Eitr as Eitr
import QtQuick
import QtQuick.Window
import Quickshell
import Quickshell.Wayland

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
    QtObject { id: keyboardState; property bool numLock: false }
    AuthAdapter {
        id: auth
        // Previews run preview.qml instead; this shell always holds a real lock.
        preview: false
        onAuthenticated: {
            shell.authenticated = true;
            shell.unlocked = true;
            Quickshell.execDetached(["loginctl", "unlock-session"]);
            quitTimer.start();
        }
    }

    Timer { id: quitTimer; interval: 200; onTriggered: Qt.quit() }

    Component {
        id: themeSurface
        Item {
            // Returning from another account's login screen (Switch user) leaves the
            // lock without keyboard focus; give it back to the design when active again.
            readonly property bool windowActive: Window.active
            onWindowActiveChanged: if (windowActive && theme.item) theme.item.forceActiveFocus()
            Loader {
                id: theme
                anchors.fill: parent
                asynchronous: true
                // Create the lock surface before loading the presentation.
                Component.onCompleted: Qt.callLater(function() {
                    theme.source = "file://" + shell.themePath + "/Main.qml";
                })
                onLoaded: item.forceActiveFocus()
            }
            Column {
                id: lockedControls
                readonly property real unit: Math.max(0.65, Math.min(parent.width / 1440, parent.height / 900))
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom; anchors.bottomMargin: 40 * lockedControls.unit
                spacing: 10 * lockedControls.unit
                z: 200
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: Eitr.I18n.tr("Locked session · %1", [auth.lockedName])
                    color: "white"; style: Text.Outline; styleColor: "#202126"
                    font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 13 * lockedControls.unit
                }
                Rectangle {
                    visible: auth.switchAvailable && sessionLock.secure && !shell.authenticated
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: switchLabel.implicitWidth + 32 * lockedControls.unit; height: 38 * lockedControls.unit; radius: 12 * lockedControls.unit
                    color: "#202126"; border.color: "#808080"
                    Text { id: switchLabel; anchors.centerIn: parent; text: Eitr.I18n.tr("Switch user"); color: "white"; font.pixelSize: 13 * lockedControls.unit }
                    MouseArea { anchors.fill: parent; enabled: !auth.authenticating; cursorShape: Qt.PointingHandCursor; onClicked: auth.switchUser() }
                    Shortcut { sequence: "Ctrl+Alt+U"; enabled: auth.switchAvailable && sessionLock.secure && !auth.authenticating && !shell.authenticated; onActivated: auth.switchUser() }
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
            }
        }
    }
}
