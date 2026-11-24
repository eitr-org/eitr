import ".."
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

ThemedPopup {
    id: panel
    waitForFreshData: true
    property var entry: null
    property bool clockSlot: false
    property string placementSlot: "status"
    leftAligned: placementSlot === "start"
    property string clockFormat: PluginRegistry.clockFormat
    surfaceColor: entry && entry.surface === "panel" ? background : "transparent"
    property var history: []
    function back() {
        while (history.length) {
            const previous = history[history.length - 1];
            history = history.slice(0, -1);
            const current = PluginRegistry.entries.find(entry => entry.plugin === previous.plugin
                && entry.id === previous.id && entry.kind === "panels");
            if (current && (!PluginRegistry.barItemShown || PluginRegistry.barItemShown(current.plugin))) {
                entry = current;
                return true;
            }
        }
        return false;
    }
    escapeHandler: back
    onOpenedChanged: if (!opened) history = []
    // A panel may ask for more room in its manifest (width, maxHeight); its content scrolls beyond that.
    readonly property int contentLimit: entry && entry.maxHeight ? entry.maxHeight : 360
    implicitWidth: entry && entry.width ? entry.width : 400
    implicitHeight: Math.min(contentLimit, content.implicitHeight) + header.height + verticalContentInset
    Connections {
        target: PluginRegistry
        function onEntriesChanged() {
            if (!panel.entry) return;
            panel.entry = PluginRegistry.entries.find(entry => entry.plugin === panel.entry.plugin && entry.id === panel.entry.id && entry.kind === "panels") || null;
            if (!panel.entry || (PluginRegistry.barItemShown && !PluginRegistry.barItemShown(panel.entry.plugin))) panel.opened = false;
        }
        function onPlacementsChanged() {
            if (panel.entry && PluginRegistry.barItemShown && !PluginRegistry.barItemShown(panel.entry.plugin)) panel.opened = false;
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
        width: parent.width; height: Math.min(panel.contentLimit, content.implicitHeight)
        contentWidth: availableWidth; clip: true
        PluginComponent {
            id: content
            clockFormat: panel.clockFormat
            width: scroll.availableWidth; height: implicitHeight
            active: panel.entry !== null
            // The panel itself is the plugin's surface; a second fill would show twice through Blur.
            surface: false
            onImplicitHeightChanged: panel.dataReady()
            entry: panel.entry || ({kind: "panels", plugin: "", id: "", commit: "", qml: "", source: "", title: "", disabled: true})
            foreground: panel.foreground; background: panel.background; accent: panel.accent
            onPanelRequested: function(plugin, requested) {
                panel.history = panel.history.concat([{plugin: panel.entry.plugin, id: panel.entry.id}]);
                panel.entry = PluginRegistry.entries.find(entry => entry.plugin === plugin && entry.id === requested && entry.kind === "panels") || null;
            }
        }
    }
}
