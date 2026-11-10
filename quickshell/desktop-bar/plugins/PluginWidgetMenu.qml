import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The desktop right-click menu of one widget copy: its title and plugin, then the same
// settings Control Center shows (PluginWidgetControls), on a themed card.
Rectangle {
    id: menu
    required property var entry
    required property var placement
    required property color foreground
    required property color background
    required property color accent
    // Asks the host to close the menu (after an action that ends it, or Escape).
    signal closeRequested()
    readonly property alias controls: controls
    readonly property real inset: PanelStyle.surfaceInset
    implicitWidth: 372
    implicitHeight: content.implicitHeight + 2 * inset
    radius: DesktopStyle.radius(PanelStyle.cornerRadius + 4)
    color: Qt.rgba(background.r, background.g, background.b, 1)
    border.width: 1
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)
    Keys.onEscapePressed: closeRequested()

    Column {
        id: content
        x: menu.inset; y: menu.inset
        width: menu.width - 2 * menu.inset
        spacing: 10
        Item {
            width: parent.width; height: 34
            Rectangle {
                id: badge
                width: 30; height: 30; anchors.verticalCenter: parent.verticalCenter
                radius: DesktopStyle.radius(PanelStyle.controlRadius + 2)
                color: Qt.alpha(menu.accent, 0.18)
                Text {
                    anchors.centerIn: parent
                    text: "󰏖"; color: menu.accent
                    font.family: PanelStyle.fontFamily; font.pixelSize: 16
                }
            }
            Column {
                x: badge.width + 10; width: parent.width - x
                anchors.verticalCenter: parent.verticalCenter
                spacing: PanelStyle.selectionDetailGap
                Text {
                    width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText
                    text: menu.entry.title || ""; color: menu.foreground
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                }
                Text {
                    width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText
                    text: menu.entry.pluginName || ""; visible: text !== ""
                    color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
            }
        }
        PluginWidgetControls {
            id: controls
            width: parent.width
            entry: menu.entry; placement: menu.placement
            foreground: menu.foreground; background: menu.background; accent: menu.accent
            onActed: menu.closeRequested()
        }
    }
}
