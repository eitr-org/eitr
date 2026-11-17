import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Compact Control Center > Tools summary for ClockTimers and FocusTimer:
// shows the active countdown, focus phase, or stopwatch, starts or stops
// quick presets, and opens the full Clock window.
Column {
    id: panel
    required property color foreground
    required property color accent
    required property color background
    property real ringSize: 44
    signal clockRequested(string page)
    spacing: 10

    readonly property var liveActivity: ClockTimers.activity
    readonly property bool pausedStopwatchOnly: !liveActivity.active && ClockTimers.stopwatchPaused
    readonly property bool hasActivity: liveActivity.active || pausedStopwatchOnly
    readonly property string activeKind: liveActivity.active ? liveActivity.kind : (pausedStopwatchOnly ? "stopwatch" : "")
    readonly property string activePage: liveActivity.active ? liveActivity.page : (pausedStopwatchOnly ? "stopwatch" : "timers")
    readonly property bool activeRunning: liveActivity.active ? liveActivity.running : false
    readonly property bool activeIsBreak: liveActivity.active && liveActivity.isBreak
    readonly property real activeProgress: liveActivity.active ? liveActivity.progress
        : (pausedStopwatchOnly ? (ClockTimers.stopwatchElapsed % 60000) / 60000 : 0)
    readonly property string activeTimeText: liveActivity.active ? liveActivity.timeText
        : (pausedStopwatchOnly ? ClockTimers.formatStopwatch(ClockTimers.stopwatchElapsed) : "")

    readonly property string statusTitle: {
        if (activeKind === "timer") {
            const label = liveActivity.name && liveActivity.name.length > 0 ? liveActivity.name : Eitr.I18n.tr("Timer");
            return liveActivity.paused ? label + " · " + Eitr.I18n.tr("Paused") : label;
        }
        if (activeKind === "focus") {
            const label = FocusTimer.phase === "break"
                ? Eitr.I18n.tr("Break")
                : Eitr.I18n.tr("Focus · round {round}", {round: FocusTimer.rounds + 1});
            return FocusTimer.paused ? label + " · " + Eitr.I18n.tr("Paused") : label;
        }
        if (activeKind === "stopwatch") {
            return ClockTimers.stopwatchPaused
                ? Eitr.I18n.tr("Stopwatch") + " · " + Eitr.I18n.tr("Paused")
                : Eitr.I18n.tr("Stopwatch");
        }
        return Eitr.I18n.tr("Nothing running");
    }

    function stopCurrent() {
        if (activeKind === "timer") ClockTimers.removeTimer(liveActivity.timerId);
        else if (activeKind === "focus") FocusTimer.stop();
        else if (activeKind === "stopwatch") ClockTimers.resetStopwatch();
    }

    function togglePauseCurrent() {
        if (activeKind === "timer") {
            if (liveActivity.running) ClockTimers.pauseTimer(liveActivity.timerId);
            else ClockTimers.resumeTimer(liveActivity.timerId);
        } else if (activeKind === "focus") {
            if (FocusTimer.running) FocusTimer.pause();
            else FocusTimer.resume();
        } else if (activeKind === "stopwatch") {
            if (ClockTimers.stopwatchRunning) ClockTimers.pauseStopwatch();
            else ClockTimers.resumeStopwatch();
        }
    }

    component ActionButton: PanelButton {
        id: actionButton
        property real minWidth: 84
        width: Math.max(minWidth, Math.ceil(metrics.advanceWidth) + 28)
        height: 32
        foreground: panel.foreground
        TextMetrics {
            id: metrics
            font.family: DesktopFonts.family
            font.pixelSize: actionButton.textSize
            text: actionButton.text
        }
    }

    Row {
        width: parent.width
        spacing: 12

        ProgressRing {
            id: ring
            width: panel.ringSize; height: panel.ringSize
            anchors.verticalCenter: parent.verticalCenter
            progress: panel.activeProgress
            trackColor: Qt.alpha(panel.foreground, 0.14)
            accentColor: panel.activeIsBreak ? Qt.lighter(panel.accent, 1.3) : panel.accent
            lineWidth: 4
            ringPadding: 4
            minimumArc: panel.hasActivity ? 0.02 : 0
        }

        Column {
            width: parent.width - ring.width - parent.spacing
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2

            Text {
                width: parent.width
                elide: Text.ElideRight
                text: panel.statusTitle
                color: panel.foreground
                opacity: panel.hasActivity ? 1.0 : PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
                font.weight: panel.hasActivity ? Font.Medium : Font.Normal
            }

            Text {
                width: parent.width
                elide: Text.ElideRight
                text: panel.hasActivity
                    ? panel.activeTimeText
                    : Eitr.I18n.tr("Start a 5-minute timer or {focus}-minute focus", {focus: FocusTimer.focusMinutes})
                color: panel.foreground
                opacity: panel.hasActivity ? 1.0 : PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: panel.hasActivity ? PanelStyle.headingSize : PanelStyle.captionSize
                font.weight: panel.hasActivity ? Font.Bold : Font.Normal
                font.features: panel.hasActivity ? PanelStyle.tabularFigures : ({})
            }
        }
    }

    Flow {
        width: parent.width
        spacing: 8

        ActionButton {
            visible: !panel.hasActivity
            outlined: true
            text: Eitr.I18n.tr("5m Timer")
            onClicked: ClockTimers.addQuickTimer(5, "")
        }

        ActionButton {
            visible: !panel.hasActivity
            outlined: true
            text: Eitr.I18n.tr("Focus")
            onClicked: FocusTimer.startFocus()
        }

        ActionButton {
            visible: panel.hasActivity
            selected: true
            text: panel.activeRunning ? Eitr.I18n.tr("Pause") : Eitr.I18n.tr("Resume")
            onClicked: panel.togglePauseCurrent()
        }

        ActionButton {
            visible: panel.hasActivity
            outlined: true
            text: Eitr.I18n.tr("Stop")
            onClicked: panel.stopCurrent()
        }

        ActionButton {
            minWidth: 104
            outlined: true
            text: Eitr.I18n.tr("Open Clock")
            onClicked: panel.clockRequested(panel.activePage)
        }
    }
}
