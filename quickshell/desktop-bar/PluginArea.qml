pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
import QtQuick.Controls.Basic
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle
import "JsonState.js" as JsonState

Column {
    id: area
    required property color foreground
    required property color background
    required property color accent
    property bool active: true
    property bool queryEnabled: true
    property var entries: []
    property var selectedPanel: null
    readonly property var tiles: entries.filter(entry => entry.kind === "tiles")
    spacing: PanelStyle.selectionRowGap
    visible: tiles.length > 0
    property bool refreshPending: false
    function refresh() {
        if (!queryEnabled) return;
        if (query.running) refreshPending = true;
        else query.running = true;
    }
    onActiveChanged: {
        selectedPanel = null;
        if (active) refresh();
    }
    Component.onCompleted: refresh()
    function openPanel(plugin, panel) {
        selectedPanel = entries.find(entry => entry.plugin === plugin && entry.id === panel && entry.kind === "panels") || null;
    }
    function back() {
        if (!selectedPanel) return false;
        selectedPanel = null;
        return true;
    }
    Text {
        visible: !area.selectedPanel
        text: Eitr.I18n.tr("Plugins"); color: area.foreground
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize
        font.bold: true
    }
    Repeater {
        model: !area.selectedPanel ? area.tiles : []
        PluginComponent {
            required property var modelData
            width: area.width; entry: modelData
            active: area.active
            height: implicitHeight
            foreground: area.foreground; background: area.background; accent: area.accent
            onPanelRequested: function(plugin, panel) { area.openPanel(plugin, panel); }
        }
    }
    Loader {
        width: area.width
        active: area.active && area.selectedPanel !== null
        sourceComponent: Column {
            width: area.width
            spacing: PanelStyle.selectionRowGap
            Row {
                width: parent.width; spacing: PanelStyle.selectionActionGap
                PanelButton {
                    icon: true; text: "󰅁"; foreground: area.foreground
                    Accessible.name: Eitr.I18n.tr("Back")
                    onClicked: area.back()
                    HoverHandler { id: backHover }
                    BarTooltip { target: parent; hovered: backHover.hovered; text: Eitr.I18n.tr("Back"); foreground: area.foreground; background: area.background }
                }
                Text {
                    width: parent.width - 34; height: 32
                    text: area.selectedPanel ? area.selectedPanel.title : ""
                    textFormat: Text.PlainText; elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                    color: area.foreground; font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.headingSize; font.bold: true
                }
            }
            ScrollView {
                id: panelScroll
                width: parent.width
                height: Math.min(360, panel.implicitHeight)
                clip: true
                contentWidth: availableWidth
                PluginComponent {
                    id: panel
                    width: panelScroll.availableWidth; height: implicitHeight
                    entry: area.selectedPanel
                    foreground: area.foreground; background: area.background; accent: area.accent
                    onPanelRequested: function(plugin, panel) { area.openPanel(plugin, panel); }
                }
            }
        }
    }
    FileView {
        path: area.queryEnabled ? (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/eitr/plugins.json" : ""
        watchChanges: true; printErrors: false
        onFileChanged: { reload(); area.refresh(); }
    }
    FileView {
        path: area.queryEnabled ? (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/eitr/plugin-ui.json" : ""
        watchChanges: true; printErrors: false
        onFileChanged: { reload(); area.refresh(); }
    }

    Process {
        id: query
        command: ["python3", Eitr.Paths.code("walker/scripts/actions/install/plugins.py"), "ui"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            if (area.refreshPending) { area.refreshPending = false; Qt.callLater(area.refresh); }
            if (code !== 0) { area.entries = []; return; }
            try {
                const next = JSON.parse(output.text);
                if (JsonState.changed(area.entries, next)) {
                    area.entries = next;
                    if (area.selectedPanel) area.selectedPanel = next.find(entry => entry.plugin === area.selectedPanel.plugin && entry.id === area.selectedPanel.id) || null;
                }
            } catch (error) { console.warn("Plugin list:", error); area.entries = []; }
        }
    }

}
