pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic

ThemedPopup {
    id: panel
    property var entry: null
    implicitWidth: 400
    implicitHeight: Math.min(360, content.implicitHeight) + verticalContentInset
    Connections {
        target: PluginRegistry
        function onEntriesChanged() {
            if (!panel.entry) return;
            panel.entry = PluginRegistry.entries.find(entry => entry.plugin === panel.entry.plugin && entry.id === panel.entry.id && entry.kind === "panels") || null;
            if (!panel.entry) panel.opened = false;
        }
    }
    ScrollView {
        id: scroll
        width: parent.width; height: Math.min(360, content.implicitHeight)
        contentWidth: availableWidth; clip: true
        PluginComponent {
            id: content
            width: scroll.availableWidth; height: implicitHeight
            active: panel.opened && panel.entry !== null
            entry: panel.entry || ({kind: "panels", plugin: "", id: "", commit: "", qml: "", source: "", title: "", disabled: true})
            foreground: panel.foreground; background: panel.background; accent: panel.accent
            onPanelRequested: function(plugin, requested) {
                panel.entry = PluginRegistry.entries.find(entry => entry.plugin === plugin && entry.id === requested && entry.kind === "panels") || null;
            }
        }
    }
}
