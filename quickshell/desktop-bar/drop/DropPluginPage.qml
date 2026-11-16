import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Item {
    id: page
    required property var owner
    readonly property var entry: owner.pluginEntry
    readonly property real contentLimit: Math.max(0, Math.min(entry && entry.maxHeight ? entry.maxHeight : 360,
        owner.height - owner.verticalContentInset - header.height))
    implicitHeight: header.height + Math.min(entry && entry.maxHeight ? entry.maxHeight : 360, plugin.implicitHeight)
    Row {
        id: header
        width: parent.width; height: 36; spacing: 6
        PanelButton {
            objectName: "dropPluginBack"
            icon: true; text: "󰅁"; foreground: page.owner.foreground
            Accessible.name: Eitr.I18n.tr("Back")
            onClicked: page.owner.backPlugin()
        }
        Text {
            text: page.entry ? page.entry.title : ""; textFormat: Text.PlainText
            width: parent.width - 34; height: 36; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter
            color: page.owner.accent; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize; font.bold: true
        }
    }
    ScrollView {
        id: scroll
        y: header.height
        width: parent.width; height: Math.min(page.contentLimit, plugin.implicitHeight)
        contentWidth: availableWidth; clip: true
        PluginComponent {
            id: plugin
            objectName: "dropPluginContent"
            width: scroll.availableWidth; height: implicitHeight
            entry: page.entry || ({kind: "panels", plugin: "", id: "", title: "", source: "", qml: "", disabled: true})
            active: !!page.entry && page.owner.opened && page.visible
            observing: page.owner.settled
            surface: false
            clockFormat: page.owner.barHost.host.barClock
            foreground: page.owner.foreground; background: page.owner.background; accent: page.owner.accent
            onPanelRequested: function(plugin, panel) { page.owner.openPlugin(plugin, panel, true); }
        }
    }
}
