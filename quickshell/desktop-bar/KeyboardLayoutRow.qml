import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle

Rectangle {
    id: row
    required property string label
    required property color foreground
    property color tooltipBackground
    property bool selected: false
    property bool available: true
    property bool removable: true
    property bool showRemove: true
    signal activated()
    signal removeRequested()
    height: PanelStyle.selectionRowHeight
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: Qt.alpha(foreground, PanelStyle.selectionAlpha(selected, mouse.containsMouse))
    border.width: PanelStyle.selectionBorderWidth(selected)
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)
    activeFocusOnTab: true
    Keys.onReturnPressed: if (available) activated()
    Keys.onSpacePressed: if (available) activated()
    Text {
        x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter
        text: row.selected ? "" : ""
        color: row.foreground; font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
    }
    Text {
        x: PanelStyle.selectionTextInset; width: parent.width - x - (row.showRemove ? PanelStyle.selectionActionWidth + 2 * PanelStyle.selectionActionInset : 10)
        anchors.verticalCenter: parent.verticalCenter
        text: row.label; textFormat: Text.PlainText; elide: Text.ElideRight
        color: row.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    MouseArea {
        id: mouse
        anchors.fill: parent; hoverEnabled: true; enabled: row.available
        cursorShape: Qt.PointingHandCursor
        onClicked: row.activated()
    }
    PanelButton {
        id: removeButton
        anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter
        visible: row.showRemove; width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight
        icon: true; text: "󰆴"; foreground: row.foreground
        available: row.available && row.removable
        Accessible.name: Eitr.I18n.tr("Remove layout")
        onClicked: row.removeRequested()
        HoverHandler { id: removeHover }
        BarTooltip { target: removeButton; hovered: removeHover.hovered; text: Eitr.I18n.tr("Remove layout"); foreground: row.foreground; background: row.tooltipBackground }
    }
}
