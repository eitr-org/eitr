import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Stopwatch: the hand sweeps once a minute and each lap leaves a notch on the bezel; the
// time with tenths in the centre, laps newest first below (each against the one before:
// faster in the accent, slower dimmed).
Item {
    id: page
    required property color foreground
    required property color accent
    readonly property bool isRunning: ClockTimers.stopwatchRunning
    readonly property bool isPaused: ClockTimers.stopwatchPaused
    readonly property bool isActive: ClockTimers.stopwatchActive
    readonly property var laps: ClockTimers.stopwatchLaps

    ChronoDial {
        id: dial
        width: parent.width
        height: Math.min(parent.width, parent.height - 190)
        foreground: page.foreground
        accent: page.accent
        showHand: true
        hand: (ClockTimers.stopwatchElapsed % 60000) / 60000
        notches: page.laps.slice(0, 12).map(lap => (lap.totalMs % 60000) / 60000)

        Column {
            anchors.centerIn: parent
            spacing: 2
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: page.isRunning ? Eitr.I18n.tr("Running") : page.isPaused ? Eitr.I18n.tr("Paused") : Eitr.I18n.tr("Ready")
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
            Text {
                objectName: "clock-stopwatch-time"
                anchors.horizontalCenter: parent.horizontalCenter
                text: ClockTimers.formatStopwatch(ClockTimers.stopwatchElapsed)
                color: page.foreground
                font.family: DesktopFonts.family; font.pixelSize: 34; font.bold: true
                font.features: PanelStyle.tabularFigures
            }
        }
    }

    Item {
        id: below
        anchors.bottom: parent.bottom
        width: parent.width
        height: parent.height - dial.height - 12

        ListView {
            anchors { left: parent.left; right: parent.right; top: parent.top; bottom: keys.top; bottomMargin: 8 }
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: page.laps
            delegate: Item {
                id: lap
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 30
                Rectangle {
                    visible: lap.index > 0
                    width: parent.width; height: 1
                    color: Qt.alpha(page.foreground, PanelStyle.dividerAlpha)
                }
                Text {
                    x: 8; anchors.verticalCenter: parent.verticalCenter
                    text: Eitr.I18n.tr("Lap {number}", {number: lap.modelData.number})
                    color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    font.features: PanelStyle.tabularFigures
                }
                Text {
                    x: parent.width * 0.38; anchors.verticalCenter: parent.verticalCenter
                    text: ClockTimers.formatStopwatch(lap.modelData.splitMs)
                    color: page.foreground
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.bold: true
                    font.features: PanelStyle.tabularFigures
                }
                Text {
                    anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    text: lap.modelData.deltaText || ""
                    color: lap.modelData.trend === "faster" ? page.accent : page.foreground
                    opacity: lap.modelData.trend === "faster" ? 1 : PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    font.features: PanelStyle.tabularFigures
                }
            }
        }

        Row {
            id: keys
            anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom }
            spacing: 8
            PanelButton {
                width: 120; height: 36
                outlined: true
                available: page.isActive
                foreground: page.foreground
                text: page.isRunning ? Eitr.I18n.tr("Lap") : Eitr.I18n.tr("Reset")
                onClicked: page.isRunning ? ClockTimers.lapStopwatch() : ClockTimers.resetStopwatch()
            }
            PanelButton {
                objectName: "clock-stopwatch-toggle"
                width: 120; height: 36
                selected: true
                foreground: page.foreground
                text: page.isRunning ? Eitr.I18n.tr("Pause") : page.isPaused ? Eitr.I18n.tr("Resume") : Eitr.I18n.tr("Start")
                onClicked: {
                    if (page.isRunning) ClockTimers.pauseStopwatch();
                    else if (page.isPaused) ClockTimers.resumeStopwatch();
                    else ClockTimers.startStopwatch();
                }
            }
        }
    }
}
