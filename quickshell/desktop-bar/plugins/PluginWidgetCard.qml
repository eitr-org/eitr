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
                id: glyph
                width: 20; anchors.verticalCenter: parent.verticalCenter
                text: "󰍹"; color: card.foreground; horizontalAlignment: Text.AlignHCenter
                font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
            }
            Text {
                x: 26; width: parent.width - x
                anchors.verticalCenter: parent.verticalCenter
                text: card.monitorLabel; textFormat: Text.PlainText; elide: Text.ElideRight
                color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
            }
        }
        PluginWidgetControls {
            id: controls
            width: parent.width
            entry: card.entry; placement: card.placement
            foreground: card.foreground; background: card.background; accent: card.accent
            monitors: card.monitors
        }
    }
}
