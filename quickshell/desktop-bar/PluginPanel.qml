pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

ThemedPopup {
    id: panel
    property var entry: null
    surfaceColor: entry && entry.surface === "panel" ? background : "transparent"
    property var history: []
    function back() {
        if (!history.length) return false;
        entry = history[history.length - 1];
        history = history.slice(0, -1);
        return true;
    }
    escapeHandler: back
    onOpenedChanged: if (!opened) history = []
    implicitWidth: 400
    implicitHeight: Math.min(360, content.implicitHeight) + header.height + verticalContentInset
    Connections {
        target: PluginRegistry
        function onEntriesChanged() {
            if (!panel.entry) return;
            panel.entry = PluginRegistry.entries.find(entry => entry.plugin === panel.entry.plugin && entry.id === panel.entry.id && entry.kind === "panels") || null;
            if (!panel.entry) panel.opened = false;
        }
    }
    Row {
        id: header
        width: parent.width; height: visible ? 36 : 0
        spacing: PanelStyle.selectionActionGap
        visible: !panel.entry || panel.entry.header !== false
        PanelButton {
            id: backButton
            icon: true; text: "󰅁"; foreground: panel.foreground
            Accessible.name: Eitr.I18n.tr("Back")
            onClicked: if (!panel.back()) panel.opened = false
        }
        Text { text: panel.entry ? panel.entry.title : ""; color: panel.foreground; textFormat: Text.PlainText; elide: Text.ElideRight; width: parent.width - backButton.width - header.spacing; height: 36; verticalAlignment: Text.AlignVCenter; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize; font.bold: true }
    }
    ScrollView {
        y: header.height
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
                panel.history = panel.history.concat([panel.entry]);
                panel.entry = PluginRegistry.entries.find(entry => entry.plugin === plugin && entry.id === requested && entry.kind === "panels") || null;
            }
        }
    }
}
