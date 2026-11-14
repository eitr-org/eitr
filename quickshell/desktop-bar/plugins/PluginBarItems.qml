import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr

Grid {
    id: items
    required property color foreground
    required property color background
    required property color accent
    property bool clockSlot: false
    property string placementSlot: clockSlot ? "clock" : "status"
    readonly property bool naturalSize: placementSlot === "clock" || placementSlot === "clockEnd"
    property real reveal: 1
    width: implicitWidth * (naturalSize && !vertical ? reveal : 1)
    height: implicitHeight * (naturalSize && vertical ? reveal : 1)
    clip: naturalSize
    property string clockFormat: "12h"
    property bool vertical: false
    property bool open: true
    property bool observing: true
    property int slotSize: 24
    property int slotSpacing: 4
    property var entries: PluginRegistry.slotItems(placementSlot)
    signal panelRequested(string plugin, string panel, Item target)
    columns: vertical ? 1 : Math.max(1, entries.length)
    spacing: slotSpacing
    visible: open && entries.length > 0
    Repeater {
        model: items.open ? items.entries : []
        PluginComponent {
            id: slot
            required property var modelData
            property real reservedWidth: 0
            onImplicitWidthChanged: if (reservedWidth <= 0 && implicitWidth > 0) reservedWidth = Math.min(192, implicitWidth)
            Component.onCompleted: if (implicitWidth > 0) reservedWidth = Math.min(192, implicitWidth)
            entry: modelData
            clockFormat: items.clockFormat
            observing: items.observing
            verticalBar: items.vertical
            iconSlot: !items.naturalSize
            width: items.naturalSize ? (items.vertical ? items.slotSize : reservedWidth) : items.slotSize
            height: items.naturalSize ? (items.vertical ? ((entry.capabilities || []).includes("weather") ? items.slotSize : reservedWidth) : barContentHeight) : items.slotSize
            verticalContent: items.naturalSize && items.vertical
            foreground: items.foreground; background: items.background; accent: items.accent
            onPanelRequested: function(plugin, panel) { items.panelRequested(plugin, panel, slot); }
            HoverHandler { id: hover }
            BarTooltip {
                target: slot; hovered: hover.hovered
                text: (slot.entry.capabilities || []).includes("weather")
                    ? Eitr.I18n.tr("Weather") + (items.vertical && slot.detail ? " · " + slot.detail : "") : slot.entry.title; foreground: items.foreground; background: items.background
            }
        }
    }
}
