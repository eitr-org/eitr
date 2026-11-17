import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Single countdown row/card showing progress ring, remaining time, name, and controls.
Rectangle {
    id: card
    required property var timerEntry
    required property color foreground
    required property color accent
    readonly property bool isEnded: timerEntry && timerEntry.ended === true
    readonly property bool isRunning: timerEntry && timerEntry.running === true && !isEnded
    readonly property real remainingMs: timerEntry ? ClockTimers.timerRemaining(timerEntry) : 0
    readonly property real progress: timerEntry ? ClockTimers.timerProgress(timerEntry) : 0

    width: parent ? parent.width : 0
    implicitHeight: rowContent.implicitHeight + 24
    height: implicitHeight
    radius: DesktopStyle.radius(10)
    color: isEnded ? Qt.alpha(SettingsInk.gold, 0.08) : SettingsPalette.surface
    border.width: 1
    border.color: isEnded ? Qt.alpha(SettingsInk.gold, 0.55) : SettingsPalette.line

    component RowActionButton: PanelButton {
        id: actionBtn
        property real minWidth: 82
        width: Math.max(minWidth, Math.ceil(metrics.advanceWidth) + 24)
        height: 32
        foreground: card.foreground
        TextMetrics {
            id: metrics
            font.family: DesktopFonts.family
            font.pixelSize: actionBtn.textSize
            text: actionBtn.text
        }
    }

    Item {
        id: rowContent
        anchors.fill: parent
        anchors.margins: 12
        implicitHeight: Math.max(ring.height, infoCol.implicitHeight, actionsRow.implicitHeight)

        ProgressRing {
            id: ring
            width: 56; height: 56
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            progress: card.isEnded ? 1 : card.progress
            trackColor: Qt.alpha(card.foreground, 0.12)
            accentColor: card.isEnded ? SettingsInk.gold : card.accent
            lineWidth: 5
            ringPadding: 5
            minimumArc: card.isEnded ? 1 : 0.02
            animateProgress: false
        }

        Column {
            id: infoCol
            anchors.left: ring.right
            anchors.leftMargin: 16
            anchors.right: actionsRow.left
            anchors.rightMargin: 14
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2

            Row {
                width: parent.width
                spacing: 8

                Text {
                    text: ClockTimers.timerLabel(card.timerEntry)
                    color: card.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                    font.weight: Font.Medium
                    elide: Text.ElideRight
                    width: Math.min(implicitWidth, parent.width - (badge.visible ? badge.width + 8 : 0))
                }

                Rectangle {
                    id: badge
                    visible: card.isEnded || !card.isRunning
                    anchors.verticalCenter: parent.verticalCenter
                    radius: DesktopStyle.radius(4)
                    color: card.isEnded ? Qt.alpha(SettingsInk.gold, 0.2) : Qt.alpha(card.foreground, 0.08)
                    width: badgeLabel.implicitWidth + 12
                    height: 20

                    Text {
                        id: badgeLabel
                        anchors.centerIn: parent
                        text: card.isEnded ? Eitr.I18n.tr("Ended") : Eitr.I18n.tr("Paused")
                        color: card.isEnded ? SettingsInk.gold : card.foreground
                        opacity: card.isEnded ? 1 : PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                        font.weight: Font.Medium
                    }
                }
            }

            Text {
                width: parent.width
                text: card.isEnded
                    ? Eitr.I18n.tr("0:00 · Timer finished")
                    : ClockTimers.formatClock(card.remainingMs)
                color: card.isEnded ? SettingsInk.gold : card.foreground
                font.family: DesktopFonts.family
                font.pixelSize: card.isEnded ? 20 : 28
                font.weight: Font.Bold
                font.features: PanelStyle.tabularFigures
            }
        }

        Row {
            id: actionsRow
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8

            RowActionButton {
                visible: !card.isEnded
                selected: !card.isRunning
                outlined: card.isRunning
                text: card.isRunning ? Eitr.I18n.tr("Pause") : Eitr.I18n.tr("Resume")
                onClicked: {
                    if (card.isRunning) ClockTimers.pauseTimer(card.timerEntry.id);
                    else ClockTimers.resumeTimer(card.timerEntry.id);
                }
            }

            RowActionButton {
                outlined: !card.isEnded
                selected: card.isEnded
                text: Eitr.I18n.tr("Restart")
                onClicked: ClockTimers.restartTimer(card.timerEntry.id)
            }

            PanelButton {
                width: 32; height: 32
                icon: true; iconSize: 16
                outlined: true
                text: "\u{F00D}"
                foreground: card.foreground
                Accessible.name: Eitr.I18n.tr("Remove timer")
                onClicked: ClockTimers.removeTimer(card.timerEntry.id)
            }
        }
    }
}
