import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// One placed copy of a desktop widget in Control Center > Plugins: which display it is on,
// then its settings (PluginWidgetControls, which the desktop right-click menu shows too).
Rectangle {
    id: card
    required property var entry
    required property var placement
    required property string monitorLabel
    required property color foreground
    required property color background
    required property color accent
    // Connected displays as {name, description, width, height}.
    required property var monitors
    // 01, 02, … in the plugin's list, so each row is easy to tell apart.
    property int number: 1
    // With several copies the cards start folded; the header asks to open or fold one.
    property bool expanded: true
    signal toggled(bool open)

    width: parent ? parent.width : 0
    implicitHeight: content.implicitHeight + 2 * PanelStyle.selectionInset
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: Qt.alpha(foreground, PanelStyle.selectionAlpha(false, false))
    border.width: PanelStyle.selectionBorderWidth(false)
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)

    Column {
        id: content
        x: PanelStyle.selectionInset; y: PanelStyle.selectionInset
        width: card.width - 2 * x
        spacing: PanelStyle.selectionRowGap
        Item {
            width: parent.width; height: 24
            Text {
                id: numberLabel
                width: 24; anchors.verticalCenter: parent.verticalCenter
                text: (card.number < 10 ? "0" : "") + card.number
                color: card.accent; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                font.weight: Font.DemiBold; font.features: PanelStyle.tabularFigures
            }
            Text {
                id: glyph
                x: 28; width: 20; anchors.verticalCenter: parent.verticalCenter
                text: "󰍹"; color: card.foreground; horizontalAlignment: Text.AlignHCenter
                font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
            }
            Text {
                x: 54; width: summary.x - x - 8
                anchors.verticalCenter: parent.verticalCenter
                text: card.monitorLabel; textFormat: Text.PlainText; elide: Text.ElideRight
                color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
            }
            // Folded, the row still says how the copy is turned.
            Text {
                id: summary
                anchors.right: chevron.left; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter
                text: !card.expanded && card.placement && card.placement.rotation ? card.placement.rotation + "°" : ""
                color: card.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
            Text {
                id: chevron
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                text: card.expanded ? "󰅀" : "󰅂"; color: card.foreground
                font.family: PanelStyle.fontFamily; font.pixelSize: 16
            }
            MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                Accessible.role: Accessible.Button
                Accessible.name: card.monitorLabel
                onClicked: card.toggled(!card.expanded)
            }
        }
        PluginWidgetControls {
            id: controls
            visible: card.expanded
            width: parent.width
            entry: card.entry; placement: card.placement
            foreground: card.foreground; background: card.background; accent: card.accent
            monitors: card.monitors
        }
    }
}
