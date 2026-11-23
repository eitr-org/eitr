pragma Singleton
import ".."
import QtQuick
import Eitr as Eitr
import "../BarIconOrder.js" as OrderLogic

QtObject {
    id: store
    // Bound in shell.qml from persisted bar-settings.json; empty uses default zone placement.
    property string savedOrderJson: ""
    // Keep built-in icon titles visible to tools/i18n-build.py extraction.
    readonly property string batteryLabel: Eitr.I18n.tr("Battery")

    readonly property var pluginBarItems: {
        if (PluginRegistry.placedBarItems !== undefined) return PluginRegistry.placedBarItems;
        const combined = [];
        for (const slotName of ["start", "clock", "clockEnd", "status"]) {
            const entries = PluginRegistry.slotItems ? PluginRegistry.slotItems(slotName) : [];
            for (let idx = 0; idx < entries.length; idx++) combined.push(entries[idx]);
        }
        return combined;
    }

    readonly property var resolved: OrderLogic.resolve(
        savedOrderJson,
        pluginBarItems,
        function(text) { return Eitr.I18n.tr(text); }
    )
    readonly property var orderedPlugins: resolved.plugins
    readonly property bool customized: resolved.customized
    readonly property var defaultIdsByZone: resolved.defaultIdsByZone
    readonly property var idsByZone: resolved.idsByZone

    function zoneItems(zone) {
        return (resolved.zones && resolved.zones[zone]) || [];
    }

    function zoneOf(id) {
        return (resolved.zoneOf && resolved.zoneOf[id]) || "";
    }

    function pluginId(entry) {
        return OrderLogic.pluginItemId(entry);
    }

    function placedPluginId(plugin, id) {
        const entry = pluginBarItems.find(candidate => candidate.plugin === plugin && candidate.id === id);
        return entry ? pluginId(entry) : String(plugin) + ":" + String(id);
    }

    function pluginZone(plugin, id, fallbackSlot) {
        const zone = zoneOf(placedPluginId(plugin, id));
        if (zone) return zone;
        return OrderLogic.SLOT_TO_ZONE[fallbackSlot || "status"] || "right";
    }

    function pluginSlot(plugin, id, fallbackSlot) {
        const zone = pluginZone(plugin, id, fallbackSlot);
        return OrderLogic.ZONE_TO_SLOT[zone] || fallbackSlot || "status";
    }

    function moveItemJson(id, targetZone, targetIndex, hiddenMap) {
        return OrderLogic.serializeOrder(OrderLogic.moveItem(idsByZone, id, targetZone, targetIndex, hiddenMap));
    }

    function moveStepJson(id, direction, hiddenMap) {
        return OrderLogic.serializeOrder(OrderLogic.moveStep(idsByZone, id, direction, hiddenMap));
    }

    function setCustomSlotJson(plugin, id, slot) {
        const fullId = placedPluginId(plugin, id);
        const zone = OrderLogic.SLOT_TO_ZONE[slot || "status"] || "right";
        const dest = (idsByZone[zone] || []).filter(entryId => entryId !== fullId);
        return OrderLogic.serializeOrder(OrderLogic.moveItem(idsByZone, fullId, zone, dest.length, null));
    }

    function updateRegistry(current, id, item, expectingMatch) {
        return OrderLogic.updateRegistry(current, id, item, expectingMatch);
    }

    function resolveTarget(item, zone, iconsOpen, verticalBar, hiddenFallback, fallback) {
        return OrderLogic.resolveTarget(item, zone, iconsOpen, verticalBar, hiddenFallback, fallback);
    }
}
