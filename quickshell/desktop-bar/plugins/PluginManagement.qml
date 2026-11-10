import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// One plugin's visuals in Control Center > Plugins: its desktop widgets as cards, each
// with its settings, and its bar icons as Show on the bar switches.
Column {
    id: management
    required property var entries
    required property color foreground
    required property color background
    required property color accent
    property var monitors: Quickshell.screens.map(screen => ({name: screen.name, description: screen.model || screen.description || screen.name,
        width: screen.width, height: screen.height}))
    // The focused display comes first when choosing where to add a widget.
    readonly property string focusedMonitor: Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : ""
    readonly property var addChoices: monitors.slice().sort((first, second) => (second.name === focusedMonitor) - (first.name === focusedMonitor))
    spacing: PanelStyle.selectionRowGap
    function monitorName(name) {
        const monitor = monitors.find(monitor => monitor.name === name);
        return monitor ? monitor.description : name;
    }
    readonly property bool visualsDisabled: entries.some(entry => entry.disabled)
    readonly property var widgets: entries.filter(entry => !entry.disabled && entry.kind === "widgets")
    readonly property var barItems: entries.filter(entry => !entry.disabled && entry.kind === "barItems")
    function placed(entry) {
        return (PluginRegistry.placements[entry.kind] || []).filter(placement => placement.plugin === entry.plugin && placement.id === entry.id);
    }
    // Several copies on one display are numbered in the order they were added.
    function copyLabel(placements, placement) {
        const same = placements.filter(other => other.monitor === placement.monitor);
        return monitorName(placement.monitor) + (same.length > 1 ? " · " + (same.indexOf(placement) + 1) : "");
    }

    component SectionLabel: Text {
        width: management.width; topPadding: 6
        textFormat: Text.PlainText; color: management.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.capitalization: Font.AllUppercase
    }

    Row {
        visible: management.visualsDisabled
        width: parent.width; spacing: PanelStyle.selectionActionGap
        Text {
            width: parent.width - reenable.width - parent.spacing; anchors.verticalCenter: parent.verticalCenter
            text: Eitr.I18n.tr("Visuals disabled after failures"); wrapMode: Text.Wrap; textFormat: Text.PlainText
            color: management.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        PanelButton {
            id: reenable
            width: Math.max(68, reenableMetrics.advanceWidth + 24)
            text: Eitr.I18n.tr("Re-enable"); foreground: management.foreground
            onClicked: PluginRegistry.change("enable-ui", management.entries.find(entry => entry.disabled))
            TextMetrics { id: reenableMetrics; text: reenable.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
        }
    }

    Repeater {
        model: management.widgets
        Column {
            id: widget
            required property var modelData
            readonly property var placements: management.placed(modelData)
            property bool choosing: false
            width: management.width; spacing: PanelStyle.selectionRowGap
            SectionLabel {
                text: management.widgets.length > 1 ? widget.modelData.title : Eitr.I18n.tr("On your desktop")
            }
            Text {
                visible: widget.placements.length === 0
                width: parent.width; wrapMode: Text.Wrap; textFormat: Text.PlainText
                text: Eitr.I18n.tr("Not on any display yet.")
                color: management.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            }
            Repeater {
                model: widget.placements
                PluginWidgetCard {
                    required property var modelData
                    width: widget.width
                    entry: widget.modelData; placement: modelData
                    monitorLabel: management.copyLabel(widget.placements, modelData)
                    monitors: management.monitors
                    foreground: management.foreground; background: management.background; accent: management.accent
                }
            }
            PanelButton {
                id: addButton
                visible: management.monitors.length > 0
                width: Math.max(68, addMetrics.advanceWidth + 52)
                leadingIcon: "+"; textAlignment: Text.AlignLeft; outlined: true
                text: widget.placements.length ? Eitr.I18n.tr("Add another copy") : Eitr.I18n.tr("Add to a display")
                foreground: management.foreground
                onClicked: {
                    if (management.monitors.length > 1) widget.choosing = !widget.choosing;
                    else PluginRegistry.change("place", widget.modelData, {monitor: management.monitors[0].name, isNew: true});
                }
                TextMetrics { id: addMetrics; text: addButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
            }
            Repeater {
                model: widget.choosing ? management.addChoices : []
                PanelButton {
                    required property var modelData
                    width: widget.width; height: PanelStyle.selectionRowHeight; foreground: management.foreground
                    leadingIcon: "󰍹"; text: modelData.description; textAlignment: Text.AlignLeft
                    onClicked: { PluginRegistry.change("place", widget.modelData, {monitor: modelData.name, isNew: true}); widget.choosing = false; }
                }
            }
        }
    }

    SectionLabel {
        visible: management.barItems.length > 0
        text: Eitr.I18n.tr("On the bar")
    }
    Repeater {
        model: management.barItems
        ToggleRow {
            required property var modelData
            width: management.width
            text: modelData.title
            description: Eitr.I18n.tr("Show on the bar")
            foreground: management.foreground; accent: management.accent
            checked: management.placed(modelData).length > 0
            onToggled: checked => PluginRegistry.change(checked ? "place" : "unplace", modelData)
        }
    }
}
