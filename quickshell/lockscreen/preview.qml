import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: shell
    readonly property bool isLockPreview: true
    readonly property var config: JSON.parse(Quickshell.env("DESKTOP_LOCK_CONFIG") || "{}")
    readonly property var sddm: mockAuth
    readonly property var userModel: users
    readonly property var sessionModel: sessions
    readonly property var keyboard: keyboardState

    QtObject {
        id: keyboardState
        property bool numLock: false
        property var layouts: []
        property int currentLayout: 0
        function nextLayout() {
            if (layouts.length > 1) currentLayout = (currentLayout + 1) % layouts.length;
        }
    }
    Process {
        running: true
        command: ["python3", Quickshell.shellDir + "/../desktop-bar/scripts/keyboard-layout.py", "summary"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const state = JSON.parse(text);
                    if (Array.isArray(state.layouts)) {
                        keyboardState.layouts = state.layouts.map(entry => ({
                            index: entry.index, code: entry.code, shortName: entry.code, label: entry.label, longName: entry.label
                        }));
                        const activeIndex = state.layouts.findIndex(entry => entry.index === state.active);
                        keyboardState.currentLayout = activeIndex >= 0 ? activeIndex : 0;
                    }
                } catch (error) {}
            }
        }
    }
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
