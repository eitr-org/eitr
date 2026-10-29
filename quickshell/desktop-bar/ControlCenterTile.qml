import QtQuick
import QtQuick.Layouts
import "PanelStyle.js" as PanelStyle

Rectangle {
    id: tile
    required property color foreground
    // A toggle tile shows its state by colour: filled with the accent when on.
    property bool toggle: false
    property color accent: foreground
    property color accentInk: PanelStyle.readableInk(accent, "#111111", "#ffffff")
    readonly property bool filled: toggle && selected && available
    readonly property color ink: filled ? accentInk : foreground
    required property string title
    required property string glyph
    property string tooltip: ""
    property color tooltipBackground
    property string subtitle: ""
    // Short current state shown after the title on the same line.
    property string detail: ""
    property bool selected: false
    property bool available: true
    property bool details: false
    signal clicked()
    signal detailsRequested()
    Layout.fillWidth: true; Layout.preferredHeight: PanelStyle.selectionRowHeight
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: filled ? Qt.alpha(tile.accent, tileMouse.containsMouse || tile.activeFocus ? 0.85 : 1)
        : Qt.alpha(tile.foreground, PanelStyle.selectionAlpha(selected && !toggle, tileMouse.containsMouse || tile.activeFocus))
    border.width: filled ? 0 : PanelStyle.selectionBorderWidth(selected && !toggle)
    Behavior on color { ColorAnimation { duration: DesktopStyle.motionDuration(140) } }
    border.color: Qt.alpha(tile.foreground, PanelStyle.selectionBorderAlpha)
    opacity: available ? 1 : 0.45
    activeFocusOnTab: true
    Keys.onReturnPressed: if (available) clicked()
    Keys.onSpacePressed: if (available) clicked()
    Text { x: PanelStyle.selectionInset; width: 18; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter; text: tile.glyph; color: tile.ink; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.selectionIconSize }
    Column { x: PanelStyle.selectionTextInset; width: parent.width - x - (tile.details ? PanelStyle.selectionActionWidth + 2 * PanelStyle.selectionActionInset : PanelStyle.selectionInset); anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionDetailGap
        // One line: the title, then the current detail dimmed ("WiFi · Home").
        Row {
            width: parent.width
            Text { id: titleText; width: Math.min(implicitWidth, parent.width); text: tile.title; elide: Text.ElideRight; color: tile.ink; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.bold: true }
            Text { width: parent.width - titleText.width; visible: tile.detail !== ""; text: " · " + tile.detail; textFormat: Text.PlainText; elide: Text.ElideRight; color: tile.ink; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
        }
        Text { width: parent.width; text: tile.subtitle; visible: tile.subtitle !== ""; elide: Text.ElideRight; color: tile.ink; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    }
    MouseArea { id: tileMouse; anchors.fill: parent; enabled: tile.available; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { tile.forceActiveFocus(); tile.clicked(); } }
    HoverHandler { id: tooltipHover; enabled: tile.tooltip !== "" }
    BarTooltip { target: tile; hovered: tooltipHover.hovered; text: tile.tooltip; foreground: tile.foreground; background: tile.tooltipBackground }
    PanelButton {
        textSize: 12; iconSize: 16
        visible: tile.details; anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter
        width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight; icon: true; text: "›"; compactIconBackground: true
        foreground: tile.ink; onClicked: tile.detailsRequested()
    }
}
