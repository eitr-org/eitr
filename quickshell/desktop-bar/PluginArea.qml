pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import QtQuick.Controls.Basic
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

Column {
    id: area
    required property color foreground
    required property color background
    required property color accent
    property bool active: true
    property bool queryEnabled: true
    property var entries: queryEnabled ? PluginRegistry.entries : []
    property var selectedPanel: null
    readonly property var tiles: entries.filter(entry => entry.kind === "tiles")
    spacing: PanelStyle.selectionRowGap
    visible: entries.length > 0
    function refresh() { if (queryEnabled) PluginRegistry.refresh(); }
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
    Item {
        width: area.width; height: 32
        visible: !area.selectedPanel
        Text {
            anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
            text: Eitr.I18n.tr("Plugins"); color: area.foreground
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize; font.bold: true
        }

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
        active: area.active && (area.selectedPanel !== null)
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
                Column {
                    width: panelScroll.availableWidth
                    PluginComponent {
                        id: panel
                        width: panelScroll.availableWidth; height: implicitHeight
                        entry: area.selectedPanel || ({kind: "panels", plugin: "", id: "", commit: "", source: "", qml: "", disabled: true, title: ""})
                        foreground: area.foreground; background: area.background; accent: area.accent
                        onPanelRequested: function(plugin, panel) { area.openPanel(plugin, panel); }
                    }

                }
            }
        }
    }
    Connections {
        target: PluginRegistry
        enabled: area.queryEnabled
        function onEntriesChanged() {
            area.entries = PluginRegistry.entries;
            if (area.selectedPanel) area.selectedPanel = area.entries.find(entry => entry.plugin === area.selectedPanel.plugin && entry.id === area.selectedPanel.id && entry.kind === "panels") || null;
        }
    }
}
