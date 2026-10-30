import QtQuick
import Eitr as Eitr

Rectangle {
    id: notifications
    property var host
    property var notificationService
    // A click opens the center on the bar that was clicked, not on the focused display.
    signal openRequested()

    readonly property bool hasNotifications: notificationService.count > 0
    readonly property string text: notificationService.doNotDisturb ? (hasNotifications ? "󰂠" : "󰪓") : (hasNotifications ? "󱅫" : "󰂜")
    readonly property string tooltip: notificationService.doNotDisturb ? Eitr.I18n.tr("Do Not Disturb") : (hasNotifications ? (notificationService.count === 1 ? Eitr.I18n.tr("{count} notification", {count: notificationService.count}) : Eitr.I18n.tr("{count} notifications", {count: notificationService.count})) : Eitr.I18n.tr("No notifications"))

    width: host.workspaceItemSize
    height: 24
    radius: DesktopStyle.radius(7)
    color: "transparent"

    Text {
        anchors.fill: parent
        text: notifications.text
        color: host.fg
        font.family: DesktopFonts.family
        font.pixelSize: 18
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    MouseArea {
        id: mouse

        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: function(event) {
            if (event.button === Qt.RightButton)
                notificationService.toggleDnd();
            else
                notifications.openRequested();
        }
    }

    BarTooltip {
        background: host.workspaceMenuBg
        foreground: host.fg
        target: notifications
        hovered: mouse.containsMouse
        text: notifications.tooltip
    }

    Behavior on color {
        ColorAnimation {
            duration: DesktopStyle.motionDuration(120)
        }

    }

}
