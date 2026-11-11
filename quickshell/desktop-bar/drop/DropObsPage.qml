import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Drop's OBS page, shown while OBS is open or capturing: what it is doing and for how long,
// big buttons to pause, resume or stop the recording and to start or stop streaming, and
// small shortcuts for a chapter mark, the recordings folder and OBS itself. Every action
// goes through the OBS panel's own run(), which owns the capture flow.
Item {
    id: page
    required property var obs
    required property color foreground
    required property color accent
    required property color background
    required property bool active
    readonly property var state: obs.obsState
    readonly property bool recording: !!state.recording
    readonly property bool streaming: !!state.streaming
    // Time on the clock since this capture began, counted here (OBS does not report it).
    property real startedAt: 0
    property real now: Date.now()
    readonly property bool capturing: recording || streaming
    onCapturingChanged: startedAt = capturing ? Date.now() : 0
    Component.onCompleted: if (capturing) startedAt = Date.now()
    Timer { interval: 1000; repeat: true; running: page.active && page.capturing; triggeredOnStart: true; onTriggered: page.now = Date.now() }
    function elapsed() {
        const seconds = Math.max(0, Math.floor((now - startedAt) / 1000));
        return Math.floor(seconds / 3600) + ":" + String(Math.floor(seconds / 60) % 60).padStart(2, "0") + ":" + String(seconds % 60).padStart(2, "0");
    }
    implicitHeight: 236

    // One round action: a glyph in a circle, filled when it is the main one, and its name.
    component Action: Item {
        id: action
        required property string glyph
        required property string label
        property bool main: false
        property color tint: page.accent
        property bool available: true
        signal activated()
        width: 72; height: 86
        opacity: available ? 1 : 0.4
        Rectangle {
            id: disc
            anchors.horizontalCenter: parent.horizontalCenter
            width: 56; height: 56; radius: 28
            color: action.main ? action.tint : Qt.alpha(page.foreground, mouse.containsMouse && action.available ? 0.14 : 0.08)
            border.width: action.main ? 0 : 1
            border.color: Qt.alpha(page.foreground, PanelStyle.selectionBorderAlpha)
            scale: mouse.pressed && action.available ? 0.92 : 1
            Behavior on scale { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
            Text {
                anchors.centerIn: parent
                text: action.glyph
                color: action.main ? PanelStyle.readableInk(action.tint, page.foreground, page.background) : page.foreground
                font.family: DesktopFonts.family; font.pixelSize: 22
            }
            MouseArea {
                id: mouse
                anchors.fill: parent; hoverEnabled: true
                enabled: action.available; cursorShape: Qt.PointingHandCursor
                onClicked: action.activated()
            }
        }
        Text {
            y: disc.height + 8; width: parent.width
            horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
            text: action.label
            color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.weight: Font.DemiBold
        }
    }

    // Now: a pulsing dot while live, what is happening and for how long.
    Row {
        x: 6; y: 6
        spacing: 12
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 12; height: 12; radius: 6
            color: page.capturing && !page.state.paused ? "#e05c68" : Qt.alpha(page.foreground, 0.35)
            SequentialAnimation on opacity {
                running: page.active && page.capturing && !page.state.paused && !DesktopStyle.reduceMotion; loops: Animation.Infinite
                NumberAnimation { to: 0.35; duration: 700; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1; duration: 700; easing.type: Easing.InOutSine }
            }
        }
        Column {
            Text {
                text: page.state.paused ? Eitr.I18n.tr("Paused") : page.recording && page.streaming ? Eitr.I18n.tr("Recording and streaming")
                    : page.recording ? Eitr.I18n.tr("Recording") : page.streaming ? Eitr.I18n.tr("Streaming")
                    : page.state.ready ? Eitr.I18n.tr("Ready") : Eitr.I18n.tr("OBS is starting…")
                color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 18; font.weight: Font.Bold
            }
            Text {
                text: page.capturing ? page.elapsed() : page.obs.status || Eitr.I18n.tr("Nothing is being captured")
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.features: PanelStyle.tabularFigures
            }
        }
    }
    Row {
        anchors.right: parent.right; anchors.rightMargin: 4; y: 8
        spacing: 4
        Repeater {
            model: [{glyph: "󰃀", name: "Add a chapter mark", action: "chapter", live: true},
                    {glyph: "󰉋", name: "Open recordings", action: "folder"},
                    {glyph: "󰻂", name: "Open OBS", action: "open"}]
            PanelButton {
                required property var modelData
                width: 30; height: 30; icon: true
                text: modelData.glyph; foreground: page.foreground
                available: page.obs.controlsReady && (!modelData.live || page.recording)
                Accessible.name: Eitr.I18n.tr(modelData.name)
                onClicked: page.obs.run(modelData.action)
            }
        }
    }

    Rectangle { x: 6; y: 62; width: parent.width - 12; height: 1; color: Qt.alpha(page.foreground, 0.14) }

    // The recording on the left, the stream on the right.
    Row {
        y: 86
        width: parent.width
        Item {
            width: parent.width / 2; height: 120
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Eitr.I18n.tr("RECORDING")
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.2
            }
            Row {
                y: 24; anchors.horizontalCenter: parent.horizontalCenter
                spacing: 14
                Action {
                    visible: page.recording
                    glyph: page.state.paused ? "󰐊" : "󰏤"
                    label: page.state.paused ? Eitr.I18n.tr("Resume") : Eitr.I18n.tr("Pause")
                    available: page.obs.controlsReady
                    onActivated: page.obs.run(page.state.paused ? "resume" : "pause")
                }
                Action {
                    main: true; tint: page.recording ? "#e05c68" : page.accent
                    glyph: page.recording ? "󰓛" : "󰑊"
                    label: page.recording ? Eitr.I18n.tr("Stop") : Eitr.I18n.tr("Record")
                    available: !page.obs.busy
                    onActivated: page.obs.run(page.recording ? "stop" : "record")
                }
            }
        }
        Item {
            width: parent.width / 2; height: 120
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Eitr.I18n.tr("STREAMING")
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.2
            }
            Action {
                y: 24; anchors.horizontalCenter: parent.horizontalCenter
                main: page.streaming; tint: "#e05c68"
                glyph: page.streaming ? "󰓛" : "󰐊"
                label: page.streaming ? Eitr.I18n.tr("Stop") : Eitr.I18n.tr("Go live")
                available: !page.obs.busy
                onActivated: page.obs.run(page.streaming ? "stop-stream" : "stream")
            }
        }
    }
}
