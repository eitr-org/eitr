import ".."
import QtQuick
import Eitr as Eitr

Rectangle {
    id: clock
    property var host

    property date now: new Date()
    property bool compact: false
    // Only hours and minutes, without date or AM/PM (Dynamic's resting clock island).
    property bool timeOnly: false

    signal clicked()
    signal rightClicked()

    width: compact ? host.barHeight - 2 : label.implicitWidth + 17
    height: compact ? compactLabel.implicitHeight + 6 : 24
    radius: DesktopStyle.radius(7)
    color: "transparent"

    Timer {
        interval: 1000
        running: clock.visible
        repeat: true
        triggeredOnStart: true
        onTriggered: clock.now = new Date()
    }

    Text {
        id: label

        anchors.centerIn: parent
        visible: !clock.compact
        // Qt counts hours 0-23 in any format without AP, so the 12-hour time-only clock
        // computes its hour itself.
        text: clock.timeOnly ? (host.barClock === "24h" ? Qt.formatDateTime(clock.now, "HH:mm")
                : ((clock.now.getHours() + 11) % 12 + 1) + Qt.formatDateTime(clock.now, ":mm"))
            : Qt.formatDateTime(clock.now, host.barClock === "24h" ? Eitr.I18n.tr("ddd MMM dd HH:mm") : Eitr.I18n.tr("ddd MMM dd hh:mm AP"))
        horizontalAlignment: Text.AlignHCenter
        color: host.fg
        font.family: DesktopFonts.family
        font.pixelSize: 14
        font.bold: true
    }

    // Vertical bars stack the hour over the minutes (and AM/PM for 12-hour time), with a calendar glyph below.
    Column {
        id: compactLabel

        anchors.centerIn: parent
        visible: clock.compact
        spacing: 2
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: host.barClock === "24h" ? Qt.formatDateTime(clock.now, "HH\nmm")
                : String((clock.now.getHours() + 11) % 12 + 1).padStart(2, "0") + Qt.formatDateTime(clock.now, "\nmm")
            horizontalAlignment: Text.AlignHCenter
            lineHeight: 0.9
            color: host.fg
            font.family: DesktopFonts.family
            font.pixelSize: 13
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: host.barClock !== "24h" && !clock.timeOnly
            text: Qt.formatDateTime(clock.now, "AP")
            color: host.fg
            font.family: DesktopFonts.family
            font.pixelSize: 9
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: !clock.timeOnly
            text: "\u{F00ED}"
            color: host.fg
            font.family: DesktopFonts.family
            font.pixelSize: 14
        }
    }

    MouseArea {
        id: mouse

        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: mouse => mouse.button === Qt.RightButton ? clock.rightClicked() : clock.clicked()
    }

    BarTooltip {
        background: host.workspaceMenuBg
        foreground: host.fg
        target: clock
        hovered: mouse.containsMouse
        text: clock.compact ? Qt.formatDateTime(clock.now, Eitr.I18n.tr("ddd MMM dd")) : Eitr.I18n.tr("Calendar")
    }

}
