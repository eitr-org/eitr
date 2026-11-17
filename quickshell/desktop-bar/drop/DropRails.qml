import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Item {
    id: rails
    required property var owner
    anchors.fill: parent
    readonly property bool horizontal: owner.verticalAttachment
    // Space between a rail and the page beside it, inside the card.
    readonly property real gap: 14
    // Keeps the pills clear of the card's edge and rounded corners.
    readonly property real inset: 12
    readonly property real reserve: inset + pages.pillSize + gap
    readonly property var inputSurfaces: pages.inputSurfaces
    // Placed plugin bar items follow the pages on the same rail (Weather already fills the
    // first page). The rail scrolls, without a scroll bar, when it is longer than the card.
    readonly property var pluginEntries: (BarIconOrder.customized ? BarIconOrder.orderedPlugins : PluginRegistry.placedBarItems).filter(entry => !(entry.capabilities || []).includes("weather"))
    // Inside the card the pills need their own tint to stand out from it.
    readonly property color pillColor: Qt.alpha(owner.foreground, PanelStyle.selectionAlpha(false, false) + 0.06)
    readonly property var pageEntries: [
        {id: "home", glyph: "󰃭", title: Eitr.I18n.tr("Calendar and weather")},
        {id: "media", glyph: "󰝚", title: Eitr.I18n.tr("Media")},
        {id: "obs", glyph: "󰑋", title: Eitr.I18n.tr("OBS Studio")},
        {id: "controls", glyph: "󰒓", title: Eitr.I18n.tr("Quick controls")},
        {id: "display", glyph: "󰍹", title: Eitr.I18n.tr("Display")},
        {id: "streaming", glyph: "󰢹", title: Eitr.I18n.tr("Streaming")},
        {id: "performance", glyph: "󰍛", title: Eitr.I18n.tr("Performance")},
        {id: "ai", glyph: "", title: Eitr.I18n.tr("AI Usage")},
        {id: "assistant", glyph: "󰭹", title: Eitr.I18n.tr("Assistant")},
        {id: "plugins", glyph: "󰏖", title: Eitr.I18n.tr("Plugins")},
        {id: "notifications", glyph: "󰂚", title: Eitr.I18n.tr("Notifications")}
    ].filter(entry => owner.pages.includes(entry.id))
    DropRail {
        id: pages
        objectName: "dropPageRail"
        entries: rails.pageEntries.concat(rails.pluginEntries)
        clockFormat: rails.owner.barHost.host.barClock
        current: rails.owner.pluginEntry ? "" : rails.owner.page
        horizontal: rails.horizontal
        gap: PanelStyle.selectionRowGap
        opened: rails.owner.opened; ready: rails.owner.settled
        foreground: rails.owner.foreground; background: rails.pillColor; tooltipBackground: rails.owner.surfaceColor; accent: rails.owner.accent
        x: rails.inset
        y: rails.inset
        width: horizontal ? rails.width - 2 * rails.inset : pillSize
        height: horizontal ? pillSize : rails.height - 2 * rails.inset
        onChosen: function(page) { rails.owner.go(page, rails.owner.pages.indexOf(page) >= rails.owner.index ? 1 : -1); }
        onPanelRequested: function(plugin, panel) { rails.owner.openPlugin(plugin, panel); }
    }
}
