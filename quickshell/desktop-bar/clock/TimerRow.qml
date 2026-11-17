import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// One timer under the Clock's dial: a dot in its ring's colour, its name and time left.
// Clicking it puts it in the dial's centre.
Rectangle {
    id: row
    required property var timerEntry
    required property color foreground
    property color mark: foreground
    property bool chosen: false
    readonly property bool isEnded: timerEntry && timerEntry.ended === true
    readonly property bool isRunning: timerEntry && timerEntry.running === true && !isEnded
    signal clicked()

    implicitHeight: PanelStyle.selectionRowHeight
    radius: DesktopStyle.radius(8)
    color: Qt.alpha(foreground, PanelStyle.selectionAlpha(chosen, pointer.containsMouse))
    border.width: PanelStyle.selectionBorderWidth(chosen)
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)

    Rectangle {
        x: 14
        anchors.verticalCenter: parent.verticalCenter
        width: 10; height: 10; radius: 5
        color: row.mark
    }
    Text {
        anchors { left: parent.left; leftMargin: 36; right: time.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
        elide: Text.ElideRight
        text: ClockTimers.timerLabel(row.timerEntry)
            + (row.isEnded ? " · " + Eitr.I18n.tr("Ended") : row.isRunning ? "" : " · " + Eitr.I18n.tr("Paused"))
        textFormat: Text.PlainText
        color: row.foreground
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    Text {
        id: time
        anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
        text: row.isEnded ? "0:00" : ClockTimers.formatClock(ClockTimers.timerRemaining(row.timerEntry))
        color: row.foreground
        opacity: row.isRunning ? 1 : PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.bold: true
        font.features: PanelStyle.tabularFigures
    }
    MouseArea {
        id: pointer
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: row.clicked()
    }
}
