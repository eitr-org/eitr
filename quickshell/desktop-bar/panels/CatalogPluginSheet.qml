import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Eitr Store: clicking an installed plugin opens everything Control Center offers
// for it (switch, desktop widgets and bar icons with their settings, details, update and
// remove) in one sheet over the catalog.
Rectangle {
    id: sheet
    required property var plugin
    required property color foreground
    required property color background
    required property color accent
    required property color surface
    required property color line
    property var updateAction: null
    property var removeAction: null
    signal closed()
    readonly property var installed: plugin ? PluginRegistry.installed.find(entry => entry.id === plugin.id) || null : null
    visible: installed !== null
    z: 3
    color: Qt.alpha(background, 0.82)
    MouseArea { anchors.fill: parent; onClicked: sheet.closed() }
    Rectangle {
        anchors.centerIn: parent
        width: Math.min(560, parent.width - 48)
        height: Math.min(parent.height - 48, details.height + header.height + 48 + 16)
        radius: DesktopStyle.radius(12); color: sheet.surface
        border.width: 1; border.color: sheet.line
        // Clicks inside the card never reach the closing backdrop.
        MouseArea { anchors.fill: parent }
        Item {
            id: header
            x: 24; y: 18; width: parent.width - 48; height: 32
            Text {
                width: parent.width - close.width - 8; anchors.verticalCenter: parent.verticalCenter
                text: sheet.installed ? sheet.installed.name : ""; textFormat: Text.PlainText; elide: Text.ElideRight
                color: sheet.foreground; font.family: SiteStyle.carved; font.pixelSize: PanelStyle.headingSize; font.weight: Font.Medium
            }
            PanelButton {
                id: close
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                width: 32; height: 32; icon: true; text: "󰅖"; foreground: sheet.foreground
                Accessible.name: Eitr.I18n.tr("Close")
                onClicked: sheet.closed()
            }
        }
        Flickable {
            x: 24; y: header.y + header.height + 16
            width: parent.width - 48; height: parent.height - y - 24
            contentHeight: details.height; clip: true
            boundsBehavior: Flickable.StopAtBounds
            // Built only while a plugin is open, so it never sees an empty plugin.
            Loader {
                id: details
                width: parent.width
                active: sheet.installed !== null
                sourceComponent: PluginDetails {
                    width: details.width
                    modelData: sheet.installed
                    entries: PluginRegistry.entries.filter(entry => entry.plugin === sheet.installed.id)
                    foreground: sheet.foreground; background: sheet.background; accent: sheet.accent
                    framed: false
                    updateAction: sheet.updateAction; removeAction: sheet.removeAction
                }
            }
        }
    }
}
