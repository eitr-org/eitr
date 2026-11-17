import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Stopwatch page: start, pause, resume, lap, reset, large tenths display,
// and newest-first laps comparing each lap to the previous one using theme colours.
Flickable {
    id: stopwatchPage
    required property color foreground
    required property color background
    required property color accent
    contentHeight: contentColumn.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    readonly property bool isRunning: ClockTimers.stopwatchRunning
    readonly property bool isPaused: ClockTimers.stopwatchPaused
    readonly property bool isActive: ClockTimers.stopwatchActive
    readonly property real elapsedMs: ClockTimers.stopwatchElapsed
    readonly property var laps: ClockTimers.stopwatchLaps

    component SwButton: PanelButton {
        id: swBtn
        property real minWidth: 96
        width: Math.max(minWidth, Math.ceil(metrics.advanceWidth) + 28)
        height: 36
        foreground: stopwatchPage.foreground
        TextMetrics {
            id: metrics
            font.family: DesktopFonts.family
            font.pixelSize: swBtn.textSize
            text: swBtn.text
        }
    }

    Column {
        id: contentColumn
        width: stopwatchPage.width
        spacing: 18

        FamilyPageHeader {
            foreground: stopwatchPage.foreground
            rune: "ᛏ"
            group: Eitr.I18n.tr("Clock")
            title: Eitr.I18n.tr("Stopwatch")
            description: Eitr.I18n.tr("Measure elapsed time and compare laps against the previous split.")
        }

        ControlCard {
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            carved: true
            foreground: stopwatchPage.foreground
            title: Eitr.I18n.tr("Elapsed time")

            Column {
                width: parent.width
                spacing: 18

                Item {
                    width: parent.width
                    height: 188

                    ProgressRing {
                        anchors.centerIn: parent
                        width: 180; height: 180
                        progress: stopwatchPage.isActive ? (stopwatchPage.elapsedMs % 60000) / 60000 : 0
                        trackColor: Qt.alpha(stopwatchPage.foreground, 0.12)
                        accentColor: stopwatchPage.accent
                        lineWidth: 8
                        ringPadding: 10
                        minimumArc: stopwatchPage.isActive ? 0.015 : 0
                        animateProgress: false
                    }

                    Column {
                        anchors.centerIn: parent
                        spacing: 2

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: ClockTimers.formatStopwatch(stopwatchPage.elapsedMs)
                            color: stopwatchPage.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: 34
                            font.weight: Font.Bold
                            font.features: PanelStyle.tabularFigures
                        }

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: stopwatchPage.isRunning ? Eitr.I18n.tr("Running")
                                : stopwatchPage.isPaused ? Eitr.I18n.tr("Paused")
                                : Eitr.I18n.tr("Ready")
                            color: stopwatchPage.foreground
                            opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.captionSize
                        }
                    }
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10

                    SwButton {
                        selected: true
                        text: stopwatchPage.isRunning ? Eitr.I18n.tr("Pause")
                            : stopwatchPage.isPaused ? Eitr.I18n.tr("Resume")
                            : Eitr.I18n.tr("Start")
                        onClicked: {
                            if (stopwatchPage.isRunning) ClockTimers.pauseStopwatch();
                            else if (stopwatchPage.isPaused) ClockTimers.resumeStopwatch();
                            else ClockTimers.startStopwatch();
                        }
                    }

                    SwButton {
                        outlined: true
                        available: stopwatchPage.isRunning || (stopwatchPage.isActive && stopwatchPage.elapsedMs > 0)
                        text: Eitr.I18n.tr("Lap")
                        onClicked: ClockTimers.lapStopwatch()
                    }

                    SwButton {
                        outlined: true
                        available: stopwatchPage.isActive
                        text: Eitr.I18n.tr("Reset")
                        onClicked: ClockTimers.resetStopwatch()
                    }
                }
            }
        }

        ControlCard {
            visible: stopwatchPage.laps.length > 0
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            carved: true
            foreground: stopwatchPage.foreground
            title: Eitr.I18n.tr("Laps")

            Item {
                width: parent.width
                height: 22

                Text {
                    width: 64
                    text: Eitr.I18n.tr("Lap")
                    color: stopwatchPage.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
                Text {
                    x: 72
                    width: 140
                    text: Eitr.I18n.tr("Lap time")
                    color: stopwatchPage.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
                Text {
                    x: 220
                    width: 120
                    text: Eitr.I18n.tr("Difference")
                    color: stopwatchPage.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
                Text {
                    anchors.right: parent.right
                    text: Eitr.I18n.tr("Total")
                    color: stopwatchPage.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
            }

            Repeater {
                model: stopwatchPage.laps
                Column {
                    required property var modelData
                    width: parent.width
                    spacing: 0

                    Rectangle {
                        width: parent.width
                        height: 1
                        color: Qt.alpha(stopwatchPage.foreground, PanelStyle.dividerAlpha)
                    }

                    Item {
                        width: parent.width
                        height: 36

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 64
                            text: "#" + modelData.number
                            color: stopwatchPage.foreground
                            opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                            font.features: PanelStyle.tabularFigures
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            x: 72
                            width: 140
                            text: ClockTimers.formatStopwatch(modelData.splitMs)
                            color: stopwatchPage.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                            font.weight: Font.Medium
                            font.features: PanelStyle.tabularFigures
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            x: 220
                            width: 120
                            text: modelData.deltaText || "—"
                            color: modelData.trend === "faster" ? stopwatchPage.accent : stopwatchPage.foreground
                            opacity: modelData.trend === "faster" ? 1.0 : PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                            font.weight: modelData.trend === "faster" ? Font.Medium : Font.Normal
                            font.features: PanelStyle.tabularFigures
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            text: ClockTimers.formatStopwatch(modelData.totalMs)
                            color: stopwatchPage.foreground
                            opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                            font.features: PanelStyle.tabularFigures
                        }
                    }
                }
            }
        }
    }
}
