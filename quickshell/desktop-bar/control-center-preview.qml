import QtQuick
import Quickshell
import Quickshell.Wayland
import "." as Eitr

// Read-only media/laptop preview: no DBus writes, capture, or system actions.
ShellRoot {
    QtObject {
        id: mockPlayer
        property string identity: "Preview Player"
        property string trackTitle: "Eitr Media Preview"
        property string trackArtist: "Read-only test fixture"
        property string trackArtUrl: ""
        property bool canControl: true
        property bool canGoPrevious: true
        property bool canGoNext: true
        property bool canTogglePlaying: true
        property bool canSeek: true
        property bool positionSupported: true
        property bool lengthSupported: true
        property bool isPlaying: true
        property real position: 47
        property real length: 209
        function previous() {}
        function next() {}
        function togglePlaying() {}
    }
    QtObject {
        id: mockDisplay
        property var power: ({available: true, active: "balanced", profiles: ["power-saver", "balanced", "performance"]})
        property bool powerBusy: false
        property string powerError: ""
        function setPowerProfile(name) {}
    }
    PanelWindow {
        visible: true
        implicitWidth: 560; implicitHeight: 360
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "eitr-control-center-preview"
        WlrLayershell.layer: WlrLayer.Overlay
        color: "#111c18"
        Column {
            anchors.fill: parent; anchors.margins: 24; spacing: 20
            Eitr.MediaCard { width: parent.width; player: mockPlayer; active: true; foreground: "#c1c497"; accent: "#509475" }
            Eitr.PowerControls {
                width: parent.width; foreground: "#c1c497"; displayControl: mockDisplay
                battery: ({available: true, percent: 74, status: "Discharging", hours: 3.25, health: 92})
            }
        }
    }
    Timer { interval: 12000; running: true; onTriggered: Qt.quit() }
}
