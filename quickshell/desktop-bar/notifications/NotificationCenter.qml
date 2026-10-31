import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

ThemedPopup {
    id: center
    required property var service
    property int maximumHeight: 900
    implicitWidth: 468
    implicitHeight: Math.min(maximumHeight, 740)
    onOpenedChanged: service.centerOpen = opened
    NotificationList {
        anchors.fill: parent
        anchors.margins: 0
        service: center.service
        foreground: center.foreground
        background: center.background
        accent: center.accent
        onActivated: center.opened = false
    }
}
