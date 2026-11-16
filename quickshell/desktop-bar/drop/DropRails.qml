import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Item {
    id: rails
    required property var owner
    anchors.fill: parent
    readonly property bool horizontal: owner.verticalAttachment
    readonly property real gap: owner.hostWindow ? owner.hostWindow.islandSpacing || 20 : 20
    readonly property real reserve: pages.pillSize + gap
    readonly property real minimumLength: Math.max(pages.naturalLength, plugins.naturalLength)
    readonly property var inputSurfaces: pages.inputSurfaces.concat(plugins.inputSurfaces)
    readonly property var pageEntries: [
        {id: "home", glyph: "󰃭", title: Eitr.I18n.tr("Calendar and weather")},
        {id: "media", glyph: "󰝚", title: Eitr.I18n.tr("Media")},
        {id: "obs", glyph: "󰑋", title: Eitr.I18n.tr("OBS Studio")},
        {id: "controls", glyph: "󰒓", title: Eitr.I18n.tr("Quick controls")},
        {id: "timer", glyph: "󱎫", title: Eitr.I18n.tr("Timer & Focus")},
        {id: "performance", glyph: "󰍛", title: Eitr.I18n.tr("Performance")},
        {id: "ai", glyph: "", title: Eitr.I18n.tr("AI Usage")},
        {id: "notifications", glyph: "󰂚", title: Eitr.I18n.tr("Notifications")}
    ].filter(entry => owner.pages.includes(entry.id))
    DropRail {
        id: pages
        objectName: "dropPageRail"
        entries: rails.pageEntries
        current: rails.owner.pluginEntry ? "" : rails.owner.page
        horizontal: rails.horizontal
        // Pills sit close together; the rail keeps the island gap from the card.
        gap: PanelStyle.selectionRowGap
        opened: rails.owner.opened; ready: rails.owner.settled
        foreground: rails.owner.foreground; background: rails.owner.surfaceColor; accent: rails.owner.accent
        x: horizontal ? 0 : -rails.reserve
        y: horizontal ? -rails.reserve : 0
        width: horizontal ? rails.width : pillSize
        height: horizontal ? pillSize : rails.height
        onChosen: function(page) { rails.owner.go(page, rails.owner.pages.indexOf(page) >= rails.owner.index ? 1 : -1); }
    }
    DropRail {
        id: plugins
        objectName: "dropPluginRail"
        entries: PluginRegistry.placedBarItems
        horizontal: rails.horizontal; trailing: true
        // Pills sit close together; the rail keeps the island gap from the card.
        gap: PanelStyle.selectionRowGap
        clockFormat: rails.owner.barHost.host.barClock
        opened: rails.owner.opened; ready: rails.owner.settled
        foreground: rails.owner.foreground; background: rails.owner.surfaceColor; accent: rails.owner.accent
        x: horizontal ? 0 : rails.width + rails.gap
        y: horizontal ? rails.height + rails.gap : 0
        width: horizontal ? rails.width : pillSize
        height: horizontal ? pillSize : rails.height
        onPanelRequested: function(plugin, panel) { rails.owner.openPlugin(plugin, panel); }
    }
}
