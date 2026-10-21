import QtQuick
import QtQuick.Layouts
import "PanelStyle.js" as PanelStyle

Rectangle {
    id: tile
    required property color foreground
    required property string title
    required property string glyph
    property string subtitle: ""
    property bool selected: false
    property bool available: true
    property bool details: false
    signal clicked()
    signal detailsRequested()
    Layout.fillWidth: true; Layout.preferredHeight: PanelStyle.selectionRowHeight
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: Qt.alpha(tile.foreground, PanelStyle.selectionAlpha(selected, tileMouse.containsMouse))
    border.width: PanelStyle.selectionBorderWidth(selected)
    border.color: Qt.alpha(tile.foreground, PanelStyle.selectionBorderAlpha)
    opacity: available ? 1 : 0.45
    activeFocusOnTab: true
    Keys.onReturnPressed: if (available) clicked()
    Keys.onSpacePressed: if (available) clicked()
    Text { x: PanelStyle.selectionInset; width: 18; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter; text: tile.glyph; color: tile.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.selectionIconSize }
    Column { x: PanelStyle.selectionTextInset; width: parent.width - (tile.details ? 82 : 56); anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionDetailGap
        Text { width: parent.width; text: tile.title; elide: Text.ElideRight; color: tile.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.bold: true }
        Text { width: parent.width; text: tile.subtitle; visible: tile.subtitle !== ""; elide: Text.ElideRight; color: tile.foreground; opacity: 0.65; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    }
    MouseArea { id: tileMouse; anchors.fill: parent; enabled: tile.available; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { tile.forceActiveFocus(); tile.clicked(); } }
    PanelButton {
        textSize: 12; iconSize: 16
        visible: tile.details; anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter
        width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight; icon: true; text: "›"; compactIconBackground: true
        foreground: tile.foreground; onClicked: tile.detailsRequested()
    }
}
