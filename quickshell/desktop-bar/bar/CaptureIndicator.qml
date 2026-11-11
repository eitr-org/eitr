import ".."
import QtQuick
import Eitr as Eitr

// What is happening beside the clock: the recording dot or dictation bars, and from
// ClockActivityState an event about to start, a running timer and, where the layout hides its
// own bell, a bell that slides out and rings for a new notification. Every layout makes room
// for its width as it does for the recording dot.
Item {
    id: capture
    property var host
    // ClockActivityState; without it only capture shows.
    property var activity: null
    // Stacked along a side bar.
    property bool vertical: false
    signal recordingClicked()
    signal meetingClicked()
    signal timerClicked()
    signal bellClicked()
    property bool recording: false
    property bool recordingPaused: false
    property bool streaming: false
    property bool dictating: false
    property bool transcribing: false
    property var dictationLevels: [0, 0, 0, 0]
    readonly property bool listening: dictating || transcribing
    // In a pill of its own (Islands, Dynamic) the dot sits in the middle; beside the clock it hugs it.
    property bool centered: false
    readonly property bool capturing: recording || listening
    readonly property bool meeting: !!activity && activity.meetingSoon
    readonly property bool timing: !!activity && activity.timing
    readonly property bool bell: !!activity && activity.bellOut
    readonly property bool shown: capturing || meeting || timing || bell
    property real transcribePhase: 0
    NumberAnimation on transcribePhase {
        running: !DesktopStyle.reduceMotion && (capture.transcribing)
        from: 0; to: 1; duration: 900; loops: Animation.Infinite
    }
    width: shown ? marks.width : 0
    height: vertical ? (shown ? marks.height : 0) : 24
    component Mark: Text {
        id: mark
        signal activated()
        property string tip: ""
        width: 22; height: 24
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        color: capture.host.fg
        font.family: DesktopFonts.family; font.pixelSize: 14
        MouseArea { id: markMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: mark.activated() }
        BarTooltip { target: mark; hovered: markMouse.containsMouse && mark.tip !== ""; text: mark.tip; foreground: capture.host.fg; background: capture.host.workspaceMenuBg }
    }
    Grid {
        id: marks
        columns: capture.vertical ? 1 : 4
        Item {
            id: recordingDot
            visible: capture.capturing
            width: 22
            height: 24
            Rectangle {
                visible: !capture.listening
                anchors.right: capture.centered ? undefined : parent.right
                anchors.rightMargin: 2
                anchors.horizontalCenter: capture.centered ? parent.horizontalCenter : undefined
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
                anchors.right: capture.centered ? undefined : parent.right
                anchors.horizontalCenter: capture.centered ? parent.horizontalCenter : undefined
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
        Mark {
            visible: capture.meeting
            text: "󰃭"
            tip: capture.activity ? capture.activity.meetingTitle : ""
            onActivated: capture.meetingClicked()
        }
        Item {
            visible: capture.timing
            width: 22; height: 24
            TimerRing { anchors.centerIn: parent; foreground: capture.host.fg }
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: capture.timerClicked() }
        }
        Mark {
            visible: capture.bell
            text: "󰂚"
            transformOrigin: Item.Top
            rotation: capture.activity ? capture.activity.bellAngle : 0
            onActivated: capture.bellClicked()
        }
    }
}
