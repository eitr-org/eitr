import "../.."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle

// Drop's Timer & Focus page: a large ring with the time left (or the stopwatch's time),
// the choice of countdown, stopwatch or focus sessions, quick lengths for a countdown, and
// start, pause and stop. FocusTimer keeps time, so it carries on with the dashboard closed.
Item {
    id: page
    required property color foreground
    required property color accent
    required property color background
    property string choice: FocusTimer.active ? FocusTimer.mode : "timer"
    property int minutes: 5
    implicitHeight: 248

    // The ring and the time.
    Canvas {
        id: ring
        x: 6; anchors.verticalCenter: parent.verticalCenter
        width: 200; height: 200
        readonly property real progress: FocusTimer.active ? FocusTimer.progress : 0
        onProgressChanged: requestPaint()
        onPaint: {
            const context = getContext("2d");
            context.reset();
            context.lineWidth = 8; context.lineCap = "round";
            context.strokeStyle = Qt.alpha(page.foreground, 0.1);
            context.beginPath(); context.arc(100, 100, 88, 0, Math.PI * 2); context.stroke();
            if (progress <= 0) return;
            context.strokeStyle = FocusTimer.phase === "break" && FocusTimer.mode === "focus" ? Qt.lighter(page.accent, 1.3) : page.accent;
            context.beginPath(); context.arc(100, 100, 88, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * progress); context.stroke();
        }
        Column {
            anchors.centerIn: parent
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: !FocusTimer.active ? (page.choice === "stopwatch" ? "0:00" : page.choice === "focus" ? FocusTimer.focusMinutes + ":00" : page.minutes + ":00")
                    : FocusTimer.clock(FocusTimer.mode === "stopwatch" ? FocusTimer.elapsed : FocusTimer.remaining)
                color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 38; font.weight: Font.Bold
                font.features: PanelStyle.tabularFigures
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: FocusTimer.paused ? Eitr.I18n.tr("Paused")
                    : FocusTimer.active && FocusTimer.mode === "focus" ? (FocusTimer.phase === "break" ? Eitr.I18n.tr("Break") : Eitr.I18n.tr("Focus · round {round}", {round: FocusTimer.rounds + 1}))
                    : FocusTimer.active ? (FocusTimer.mode === "stopwatch" ? Eitr.I18n.tr("Stopwatch") : Eitr.I18n.tr("Timer")) : ""
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
        }
    }

    Column {
        x: ring.x + ring.width + 28; width: parent.width - x - 6
        anchors.verticalCenter: parent.verticalCenter
        spacing: 16
        TabStrip {
            width: parent.width
            foreground: page.foreground; gold: page.accent
            enabled: !FocusTimer.active
            opacity: enabled ? 1 : 0.5
            choices: [{id: "timer", label: Eitr.I18n.tr("Timer")}, {id: "stopwatch", label: Eitr.I18n.tr("Stopwatch")}, {id: "focus", label: Eitr.I18n.tr("Focus")}]
            current: page.choice
            onChosen: value => page.choice = value
        }
        // Countdown lengths.
        Flow {
            visible: page.choice === "timer" && !FocusTimer.active
            width: parent.width; spacing: 6
            Repeater {
                model: [1, 3, 5, 10, 15, 25, 45, 60]
                PanelButton {
                    required property int modelData
                    width: 56; height: 30; outlined: true
                    selected: page.minutes === modelData
                    text: modelData + "m"; foreground: page.foreground
                    onClicked: page.minutes = modelData
                }
            }
        }
        Text {
            visible: page.choice === "focus" && !FocusTimer.active
            width: parent.width; wrapMode: Text.Wrap
            text: Eitr.I18n.tr("{focus} minutes of focus, then a {rest}-minute break. You'll get a notification at each change.", {focus: FocusTimer.focusMinutes, rest: FocusTimer.breakMinutes})
            color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        Row {
            spacing: 10
            PanelButton {
                width: 110; height: 38; selected: true
                text: !FocusTimer.active ? Eitr.I18n.tr("Start") : FocusTimer.paused ? Eitr.I18n.tr("Resume") : Eitr.I18n.tr("Pause")
                foreground: page.foreground
                onClicked: {
                    if (FocusTimer.paused) FocusTimer.resume();
                    else if (FocusTimer.running) FocusTimer.pause();
                    else if (page.choice === "stopwatch") FocusTimer.startStopwatch();
                    else if (page.choice === "focus") FocusTimer.startFocus();
                    else FocusTimer.startTimer(page.minutes);
                }
            }
            PanelButton {
                visible: FocusTimer.active
                width: 90; height: 38; outlined: true
                text: Eitr.I18n.tr("Stop"); foreground: page.foreground
                onClicked: FocusTimer.stop()
            }
        }
    }
}
