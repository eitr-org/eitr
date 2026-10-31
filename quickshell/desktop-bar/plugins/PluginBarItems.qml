import ".."
pragma ComponentBehavior: Bound
import QtQuick

Grid {
    id: items
    required property color foreground
    required property color background
    required property color accent
    property bool vertical: false
    property bool open: true
    property int slotSize: 24
    property int slotSpacing: 4
    property var entries: PluginRegistry.barItems
    signal panelRequested(string plugin, string panel, Item target)
    columns: vertical ? 1 : Math.max(1, entries.length)
    spacing: slotSpacing
    visible: open && entries.length > 0
    Repeater {
        model: items.open ? items.entries : []
        PluginComponent {
            id: slot
            required property var modelData
            entry: modelData
            width: items.slotSize; height: items.slotSize
            foreground: items.foreground; background: items.background; accent: items.accent
            onPanelRequested: function(plugin, panel) { items.panelRequested(plugin, panel, slot); }
            HoverHandler { id: hover }
            BarTooltip {
                target: slot; hovered: hover.hovered
                text: slot.entry.title; foreground: items.foreground; background: items.background
            }
        }
    }
}
