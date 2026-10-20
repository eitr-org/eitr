import QtQuick
import QtQuick.Window
import Quickshell

ShellRoot {
    id: preview
    readonly property var config: JSON.parse(Quickshell.env("EITR_RENDER_CONFIG"))
    readonly property var sddm: mockAuth
    readonly property var userModel: users
    readonly property var sessionModel: sessions
    readonly property var keyboard: keyboardState
    QtObject { id: keyboardState; property bool numLock: false }
    QtObject {
        id: mockAuth
        readonly property bool quickshellLock: true
        signal loginFailed()
        signal loginSucceeded()
        function login(user, password, session) {}
        function reboot() {}
        function powerOff() {}
        function suspend() {}
    }
    ListModel { id: users; property int lastIndex: 0; property string lastUser: "EITR"; function rowCount() { return count; } ListElement { name: "EITR"; realName: "EITR" } }
    ListModel { id: sessions; property int lastIndex: 0; function rowCount() { return count; } ListElement { name: "Current session" } }
    Window {
        width: 3840; height: 2160; visible: true
        Loader {
            id: design
            anchors.fill: parent
            source: Quickshell.env("EITR_RENDER_DESIGN")
        }
        Timer {
            interval: 3200; running: true
            onTriggered: {
                if (design.status !== Loader.Ready) { console.error("Design did not load"); Qt.exit(1); return; }
                design.grabToImage(function(result) {
                    if (!result.saveToFile(Quickshell.env("EITR_RENDER_OUTPUT"))) Qt.exit(1);
                    else Qt.quit();
                }, Qt.size(3840, 2160));
            }
        }
    }
}
