import QtQuick
import Quickshell
import Quickshell.Wayland
import "." as Eitr

// Example values only. No DBus writes, recording, device changes or real media.
ShellRoot {
    QtObject {
        id: player
        property string trackTitle: "Eitr Media Preview"
        property string trackArtist: "Example player"
        property string trackArtUrl: ""
        property bool canControl: true
        property bool canGoPrevious: true
        property bool canGoNext: true
        property bool canTogglePlaying: true
        property bool canSeek: true
        property bool positionSupported: true
        property bool lengthSupported: true
        property bool isPlaying: false
        property real position: 47
        property real length: 209
        function previous() {}
        function next() {}
        function togglePlaying() {}
    }
    PanelWindow {
        implicitWidth: 520
        implicitHeight: 500
        color: "#20202b"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "eitr-handbook-controls-preview"
        WlrLayershell.layer: WlrLayer.Overlay
        Column {
            anchors.fill: parent; anchors.margins: 24; spacing: 16
            Text { text: "Workspace styles"; color: "#ddd9bd"; font.pixelSize: 18; font.family: Eitr.DesktopFonts.family }
            Repeater {
                model: ["Dots", "Glyph", "Numbers", "Runes"]
                Row {
                    required property string modelData
                    spacing: 12
                    Text { width: 140; text: parent.modelData; color: "#ddd9bd"; font.pixelSize: 14; font.family: Eitr.DesktopFonts.family }
                    Repeater {
                        model: 5
                        Eitr.WorkspaceMarker {
                            required property int index
                            width: 24; height: 24
                            style: parent.modelData; label: String(index + 1)
                            active: index === 1
                            foreground: "#ddd9bd"; accent: "#85a1dc"; selectedForeground: "#20202b"
                        }
                    }
                }
            }
            Text { text: "Media controls"; color: "#ddd9bd"; font.pixelSize: 18; font.family: Eitr.DesktopFonts.family }
            Eitr.MediaCard { width: parent.width; player: player; active: false; foreground: "#ddd9bd"; accent: "#85a1dc" }
        }
    }
    Timer { interval: 120000; running: true; onTriggered: Qt.quit() }
}
