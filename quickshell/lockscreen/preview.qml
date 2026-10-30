import QtQuick
import Quickshell
import Quickshell.Wayland

ShellRoot {
    id: shell
    readonly property bool isLockPreview: true
    readonly property var config: JSON.parse(Quickshell.env("DESKTOP_LOCK_CONFIG") || "{}")
    readonly property var sddm: mockAuth
    readonly property var userModel: users
    readonly property var sessionModel: sessions
    readonly property var keyboard: keyboardState

    QtObject { id: keyboardState; property bool numLock: false }
    QtObject {
        id: mockAuth
        readonly property bool quickshellLock: false
        signal loginFailed()
        signal loginSucceeded()
        function login(user, password, session) {}
        function reboot() {}
        function powerOff() {}
        function suspend() {}
    }
    ListModel { id: users; property int lastIndex: 0; property string lastUser: "astrid"; function rowCount() { return count; } ListElement { name: "astrid"; realName: "Astrid Solberg" } ListElement { name: "bjorn"; realName: "Bjørn Lund" } ListElement { name: "freya"; realName: "Freya Lind" } }
    ListModel { id: sessions; property int lastIndex: 0; function rowCount() { return count; } ListElement { name: "Current session" } }
    PanelWindow {
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        color: "transparent"
        Loader {
            anchors.fill: parent
            source: "file://" + Quickshell.env("DESKTOP_LOCK_THEME") + "/Main.qml"
            onLoaded: {
                item.forceActiveFocus();
                if (item.previewFinished) item.previewFinished.connect(function() { Qt.quit(); });
            }
        }
        Shortcut { sequence: "Escape"; onActivated: Qt.quit() }
    }
}
