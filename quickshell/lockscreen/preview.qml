import QtQuick
import Quickshell
import Quickshell.Wayland

ShellRoot {
    id: shell
    readonly property var config: JSON.parse(Quickshell.env("DESKTOP_LOCK_CONFIG") || "{}")
    readonly property var sddm: auth.sddm
    readonly property var userModel: auth.userModel
    readonly property var sessionModel: auth.sessionModel
    readonly property var keyboard: keyboardState

    QtObject { id: keyboardState; property bool numLock: false }
    AuthAdapter { id: auth; preview: true }
    PanelWindow {
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        color: "black"
        Loader {
            anchors.fill: parent
            source: "file://" + Quickshell.env("DESKTOP_LOCK_THEME") + "/Main.qml"
            onLoaded: item.forceActiveFocus()
        }
        Shortcut { sequence: "Escape"; onActivated: Qt.quit() }
    }
}
