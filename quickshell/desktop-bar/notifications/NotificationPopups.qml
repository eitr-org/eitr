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
    property bool shown: true
    // On a display without a bar the cards keep only the small screen margin.
    property bool besideBar: true
    readonly property int barMargin: besideBar ? 42 : 12
    visible: shown && service.popups.length > 0 && !service.centerOpen
    color: "transparent"
    implicitWidth: 428
    implicitHeight: cards.implicitHeight
    anchors { top: barEdge !== "bottom"; bottom: barEdge === "bottom"; right: barEdge !== "left"; left: barEdge === "left" }
    margins { top: barEdge === "top" ? barMargin : 12; bottom: barEdge === "bottom" ? barMargin : 12
        left: barEdge === "left" ? (besideBar ? 80 : 12) : 12; right: barEdge === "right" ? (besideBar ? 80 : 12) : 12 }
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
                    // The front card is translucent, so each layer behind it draws only
                    // the strip that peeks out below it; otherwise its outline shows
                    // through the front card.
                    Item {
                        required property int index
                        readonly property int depth: index + 1
                        objectName: "popupStackLayer" + depth
                        y: popupCard.height
                        width: stack.width; height: depth * 7
                        clip: true
                        z: 2 - depth
                        Rectangle {
                            x: parent.depth * 8; y: parent.depth * 7 - popupCard.height
                            width: stack.width - parent.depth * 16; height: popupCard.height
                            radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                            color: Qt.rgba(window.background.r * 0.92 + window.foreground.r * 0.08,
                                window.background.g * 0.92 + window.foreground.g * 0.08,
                                window.background.b * 0.92 + window.foreground.b * 0.08, 1)
                            border.width: 1; border.color: Qt.alpha(window.foreground, 0.12)
                        }
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
                        repeats: notification ? window.service.repeats[notification.id] || 1 : 1
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
