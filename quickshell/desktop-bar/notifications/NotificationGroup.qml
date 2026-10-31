import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

Column {
    id: group
    required property var notifications
    property var timestamps: ({})
    required property color foreground
    required property color accent
    property color background: "transparent"
    function stackColor(tint) {
        return Qt.rgba(background.r * (1 - tint) + foreground.r * tint,
                       background.g * (1 - tint) + foreground.g * tint,
                       background.b * (1 - tint) + foreground.b * tint, 1);
    }
    function frontColor() {
        if (!multiple) return Qt.alpha(foreground, 0.055);
        var stacked = stackColor(0.055);
        var progress = revealProgress;
        // Hide overlapping stack layers only while collapsed. Expanded cards
        // share the same translucent fill without fading their text or controls.
        return Qt.rgba(stacked.r * (1 - progress) + foreground.r * progress,
                       stacked.g * (1 - progress) + foreground.g * progress,
                       stacked.b * (1 - progress) + foreground.b * progress,
                       1 - 0.945 * progress);
    }
    property bool expanded: false
    property real revealProgress: expanded ? 1 : 0
    Behavior on revealProgress {
        NumberAnimation {
            duration: DesktopStyle.motionDuration(320)
            easing.type: group.expanded ? Easing.OutCubic : Easing.InCubic
        }
    }
    readonly property bool multiple: notifications.length > 1
    readonly property int stackDepth: Math.min(3, notifications.length)
    readonly property var displayedNotifications: expanded ? notifications : notifications.slice(0, 1)
    signal toggleRequested()
    signal clearRequested()
    signal activated(int notificationId)
    spacing: 8
    Row {
        width: parent.width; spacing: 8
        Text {
            width: parent.width - 42 - (group.multiple ? 42 : 0)
            height: 28
            text: group.multiple ? Eitr.I18n.tr("{count} notifications", {count: group.notifications.length}) : Eitr.I18n.tr("{count} notification", {count: group.notifications.length})
            color: group.foreground; opacity: 0.65
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        PanelButton {
            objectName: "toggleNotificationGroup"
            visible: group.multiple
            width: 34; height: 28; icon: true
            text: group.expanded ? "󰅃" : "󰅀"
            foreground: group.foreground
            onClicked: group.toggleRequested()
        }
        PanelButton {
            objectName: "clearNotificationGroup"
            width: 34; height: 28; icon: true
            text: "󰅖"; compactIconBackground: true
            foreground: group.foreground
            onClicked: group.clearRequested()
        }
    }
    Item {
        width: group.width
        height: frontCard.implicitHeight + Math.max(0, group.stackDepth - 1) * 7 * (1 - group.revealProgress)
            + (expandedList.implicitHeight > 0 ? expandedList.implicitHeight + 8 : 0) * group.revealProgress
        clip: true
        Item {
            id: collapsedStack
            objectName: "collapsedNotificationStack"
            width: group.width
            visible: group.revealProgress < 1 && group.notifications.length > 0
            opacity: 1 - group.revealProgress
            implicitHeight: frontCard.implicitHeight + Math.max(0, group.stackDepth - 1) * 7
            height: implicitHeight
            Repeater {
                model: Math.max(0, group.stackDepth - 1)
                Rectangle {
                    required property int index
                    readonly property int depth: index + 1
                    objectName: "notificationStackLayer" + depth
                    x: depth * 8; y: depth * 7
                    width: group.width - depth * 16
                    height: frontCard.implicitHeight
                    z: 3 - depth
                    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                    color: group.stackColor(0.055 + depth * 0.025)
                    border.width: 1
                    border.color: Qt.alpha(group.foreground, 0.12)
                }
            }
        }
        NotificationCard {
            id: frontCard
            objectName: "frontNotificationCard"
            z: 3
            width: parent.width
            notification: group.notifications.length ? group.notifications[0] : null
            receivedAt: notification ? group.timestamps[notification.id] || 0 : 0
            compact: false
            expandOnClick: group.multiple && !group.expanded
            onExpansionRequested: group.toggleRequested()
            color: group.frontColor()
            foreground: group.foreground; accent: group.accent
            onActivated: notificationId => group.activated(notificationId)
        }
        Column {
            id: expandedList
            y: frontCard.implicitHeight + 8
            width: group.width
            visible: group.revealProgress > 0
            opacity: group.revealProgress
            spacing: 8
            Repeater {
                model: group.expanded || group.revealProgress > 0 ? group.notifications.slice(1) : []
                NotificationCard {
                    required property var modelData
                    width: group.width
                    notification: modelData
                    receivedAt: group.timestamps[modelData.id] || 0
                    foreground: group.foreground; accent: group.accent
                    onActivated: notificationId => group.activated(notificationId)
                }
            }
        }
    }
}
