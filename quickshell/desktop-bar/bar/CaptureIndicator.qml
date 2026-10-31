import ".."
import QtQuick
import Eitr as Eitr

Item {
    id: capture
    property var host
    signal recordingClicked()
    property bool recording: false
    property bool recordingPaused: false
    property bool streaming: false
    property bool dictating: false
    property bool transcribing: false
    property var dictationLevels: [0, 0, 0, 0]
    readonly property bool listening: dictating || transcribing
    readonly property bool shown: recording || listening
    property real transcribePhase: 0
    NumberAnimation on transcribePhase {
        running: !DesktopStyle.reduceMotion && (capture.transcribing)
        from: 0; to: 1; duration: 900; loops: Animation.Infinite
    }
    width: shown ? recordingDot.width : 0
    height: 24
    Item {
        id: recordingDot
        visible: capture.shown
        width: 22
        height: 24
        Rectangle {
            visible: !capture.listening
            anchors.right: parent.right
            anchors.rightMargin: 2
            anchors.verticalCenter: parent.verticalCenter
            width: 6
            height: 6
            radius: 3
            color: capture.recordingPaused ? host.fg : "#e05c68"
        }
        // Dictation: seven bars mirrored around the centre line, fed by the
        // microphone while listening and pulsing while transcribing.
        Row {
            visible: capture.listening
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 1
            Repeater {
                model: 7
                Rectangle {
                    required property int index
                    anchors.verticalCenter: parent.verticalCenter
                    width: 2
                    radius: 1
                    color: "#e05c68"
                    height: capture.transcribing
                        ? 3 + 9 * (0.5 + 0.5 * Math.sin((capture.transcribePhase - index / 7) * 2 * Math.PI))
                        : 3 + 11 * ((capture.dictationLevels || [])[Math.abs(index - 3)] || 0)
                    // Smooths the 70 ms microphone samples only: the pulse changes every
                    // frame, and a Behavior restarted each frame never leaves its start.
                    Behavior on height { enabled: !capture.transcribing; NumberAnimation { duration: DesktopStyle.motionDuration(70) } }
                }
            }
        }
        MouseArea {
            id: recordingMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: capture.recording ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: if (capture.recording) capture.recordingClicked()
        }
        BarTooltip {
            target: recordingDot
            hovered: recordingMouse.containsMouse
            text: capture.dictating ? Eitr.I18n.tr("Dictating") : capture.transcribing ? Eitr.I18n.tr("Transcribing")
                : capture.recordingPaused ? "Recording paused" : capture.streaming ? "Live" : "Recording"
            foreground: host.fg
            background: host.workspaceMenuBg
        }
    }
}
