pragma ComponentBehavior: Bound
import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle

Item {
    id: center
    required property var service
    required property color foreground
    required property color background
    required property color accent
    signal activated()
    property var expandedApps: ({})
    function toggleGroup(name) {
        var updated = Object.assign({}, expandedApps);
        updated[name] = !updated[name];
        expandedApps = updated;
    }
    Item {
        anchors.fill: parent
        Row {
            id: header
            width: parent.width; spacing: 8
            PanelHeading {
                width: parent.width - 84; height: 34
                text: Eitr.I18n.tr("Notifications")
                foreground: center.foreground; accent: center.accent; rune: "wisdom"
            }
            PanelButton {
                id: dndButton
                width: 34; height: 34; icon: true
                text: center.service.doNotDisturb ? "󰂛" : "󰂚"
                selected: center.service.doNotDisturb
                foreground: center.foreground
                onClicked: center.service.toggleDnd()
                HoverHandler { id: dndHover }
                BarTooltip { target: dndButton; hovered: dndHover.hovered; text: Eitr.I18n.tr("Do Not Disturb"); foreground: center.foreground; background: center.background }
            }
            PanelButton {
                id: clearButton
                width: 34; height: 34; icon: true; text: "󰃢"
                available: center.service.count > 0
                foreground: center.foreground
                onClicked: center.service.clear()
                HoverHandler { id: clearHover }
                BarTooltip { target: clearButton; hovered: clearHover.hovered; text: Eitr.I18n.tr("Clear all"); foreground: center.foreground; background: center.background }
            }
        }
        PanelDivider { y: header.height + 12; width: parent.width; height: 8; foreground: center.foreground }
        Text {
            anchors.centerIn: parent
            visible: center.service.count === 0
            text: center.service.doNotDisturb ? Eitr.I18n.tr("󰂛  Do Not Disturb\n\nNo notifications") : Eitr.I18n.tr("󰂚  No notifications")
            horizontalAlignment: Text.AlignHCenter
            color: center.foreground; opacity: 0.65
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        Flickable {
            anchors { top: header.bottom; topMargin: 26; left: parent.left; right: parent.right; bottom: parent.bottom }
            contentHeight: groups.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: groups
                width: parent.width; spacing: 18
                Repeater {
                    model: center.service.groups
                    NotificationGroup {
                        required property var modelData
                        width: groups.width
                        notifications: modelData.notifications
                        timestamps: center.service.timestamps
                        background: center.background
                        expanded: !!center.expandedApps[modelData.name]
                        foreground: center.foreground
                        accent: center.accent
                        onToggleRequested: center.toggleGroup(modelData.name)
                        onClearRequested: center.service.clearApp(modelData.name)
                        onActivated: center.activated()
                    }
                }
            }
        }
    }
}
