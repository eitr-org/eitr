import ".."
pragma ComponentBehavior: Bound
import QtQuick

Grid {
    id: items
    required property color foreground
    required property color background
    required property color accent
    property bool clockSlot: false
    property real reveal: 1
    width: implicitWidth * (clockSlot && !vertical ? reveal : 1)
    height: implicitHeight * (clockSlot && vertical ? reveal : 1)
    clip: clockSlot
    property string clockFormat: "12h"
    property bool vertical: false
    property bool open: true
    property int slotSize: 24
    property int slotSpacing: 4
    property var entries: clockSlot ? PluginRegistry.clockBarItems : PluginRegistry.barItems
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
            clockFormat: items.clockFormat
            width: (items.clockSlot || entry.slot === "clock") ? (items.vertical ? items.slotSize : implicitWidth) : items.slotSize
            height: (items.clockSlot || entry.slot === "clock") ? (items.vertical ? implicitWidth : barContentHeight) : items.slotSize
            verticalContent: (items.clockSlot || entry.slot === "clock") && items.vertical
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
