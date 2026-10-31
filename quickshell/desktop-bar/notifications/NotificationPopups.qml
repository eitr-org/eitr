import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland
import "../PanelStyle.js" as PanelStyle

PanelWindow {
    id: window
    required property var service
    required property color foreground
    required property color background
    required property color accent
    property string barEdge: "top"
    // With a bar on every display, only the main display's bar shows popups.
    property bool shown: true
    visible: shown && service.popups.length > 0 && !service.centerOpen
    color: "transparent"
    implicitWidth: 428
    implicitHeight: cards.implicitHeight
    anchors { top: barEdge !== "bottom"; bottom: barEdge === "bottom"; right: barEdge !== "left"; left: barEdge === "left" }
    margins { top: barEdge === "top" ? 42 : 12; bottom: 42; left: barEdge === "left" ? 80 : 12; right: barEdge === "right" ? 80 : 12 }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "desktop-notifications"
    WlrLayershell.layer: WlrLayer.Overlay
    Column {
        id: cards
        width: parent.width; spacing: 10
        Repeater {
            model: window.service.popupGroups
            Item {
                id: stack
                required property var modelData
                width: cards.width
                height: popupCard.height + Math.max(0, Math.min(3, modelData.notifications.length) - 1) * 7
                Repeater {
                    model: Math.max(0, Math.min(3, stack.modelData.notifications.length) - 1)
                    Rectangle {
                        required property int index
                        readonly property int depth: index + 1
                        x: depth * 8; y: depth * 7
                        width: stack.width - depth * 16; height: popupCard.height
                        radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                        color: Qt.rgba(window.background.r * 0.92 + window.foreground.r * 0.08,
                            window.background.g * 0.92 + window.foreground.g * 0.08,
                            window.background.b * 0.92 + window.foreground.b * 0.08, 1)
                        border.width: 1; border.color: Qt.alpha(window.foreground, 0.12)
                        z: 2 - depth
                    }
                }
                Rectangle {
                    id: popupCard
                    readonly property var modelData: stack.modelData.notifications[0]
                    z: 3
                    width: stack.width
                    height: notificationCard.implicitHeight + 20
                    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                    color: window.background
                    NotificationPriorityGlow {
                        anchors.fill: parent
                        shown: !!popupCard.modelData
                        urgency: popupCard.modelData && popupCard.modelData.urgency !== undefined ? popupCard.modelData.urgency : 1
                        accent: window.accent
                        cornerRadius: popupCard.radius
                    }
                    HoverHandler {
                        onHoveredChanged: stack.modelData.notifications.forEach(notification => window.service.pausePopup(notification.id, hovered))
                    }
                    NotificationCard {
                        id: notificationCard
                        x: 10; y: 10; width: parent.width - 20
                        notification: parent.modelData
                        receivedAt: notification ? window.service.timestamps[notification.id] || 0 : 0
                        compact: true
                        filled: false
                        foreground: window.foreground
                        accent: window.accent
                        onActivated: function(notificationId) { window.service.hidePopupGroup(stack.modelData.name); }
                        onDismissed: window.service.hidePopupGroup(stack.modelData.name)
                    }
                }
            }
        }
    }
}
