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
    // Which copies are open, by instance; kept here because the cards are rebuilt on every
    // saved change. A single copy is open unless folded.
    property var openCopies: ({})
    function isOpen(placement, count) {
        return openCopies[placement.instance] !== undefined ? openCopies[placement.instance] : count === 1;
    }
    function setOpen(placement, open) {
        const next = Object.assign({}, openCopies);
        next[placement.instance] = open;
        openCopies = next;
    }
    function placed(entry) {
        return (PluginRegistry.placements[entry.kind] || []).filter(placement => placement.plugin === entry.plugin && placement.id === entry.id);
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
                    required property int index
                    width: widget.width
                    number: index + 1
                    expanded: management.isOpen(modelData, widget.placements.length)
                    onToggled: open => management.setOpen(modelData, open)
                    entry: widget.modelData; placement: modelData
                    monitorLabel: management.monitorName(modelData.monitor)
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
        Column {
            id: barItem
            required property var modelData
            readonly property string chosenSlot: (management.placed(modelData)[0] || {}).slot || modelData.slot || "status"
            width: management.width; spacing: PanelStyle.selectionRowGap
            ToggleRow {
                width: parent.width; text: barItem.modelData.title
                description: Eitr.I18n.tr("Show on the bar")
                foreground: management.foreground; accent: management.accent
                checked: management.placed(barItem.modelData).length > 0
                onToggled: checked => PluginRegistry.change(checked ? "place" : "unplace", barItem.modelData)
            }
            Flow {
                width: parent.width; spacing: 6
                visible: management.placed(barItem.modelData).length > 0
                Repeater {
                    model: [{slot:"start", label:Eitr.I18n.tr("After Idle Lock")},
                        {slot:"clock", label:Eitr.I18n.tr("Before clock")},
                        {slot:"clockEnd", label:Eitr.I18n.tr("After clock")},
                        {slot:"status", label:Eitr.I18n.tr("Status group")}]
                    PanelButton {
                        required property var modelData
                        width: Math.max(100, placementText.advanceWidth + 24)
                        text: modelData.label; foreground: management.foreground
                        selected: barItem.chosenSlot === modelData.slot
                        outlined: !selected
                        onClicked: PluginRegistry.change("place", barItem.modelData, {slot:modelData.slot})
                        TextMetrics { id: placementText; text: parent.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                    }
                }
            }
        }
    }
}
