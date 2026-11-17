pragma ComponentBehavior: Bound
import ".."
import QtQuick
import Eitr as Eitr
import "../BarIconOrder.js" as OrderLogic
import "../PanelStyle.js" as PanelStyle

// Interactive Bar > Icons organizer: preview strip, 4 draggable/keyboard-reorderable zone rows, and reset.
Column {
    id: iconsPage
    required property var context
    readonly property var view: context || ({page: "", tab: "", live: false, foreground: SettingsPalette.foreground, accent: SettingsPalette.accent, styleState: null})
    readonly property var styleModel: (view && view.styleState) || ({bar: ({})})
    readonly property bool batteryAvailable: visible ? PowerService.battery.available : false
    readonly property var hiddenIds: batteryAvailable ? ({}) : ({battery: true})
    readonly property string savedOrderJson: styleModel && styleModel.bar && styleModel.bar.iconOrder
        ? OrderLogic.serializeOrder(styleModel.bar.iconOrder) : ""

    property string draftJson: ""
    property bool hasDraft: false
    property string expectedSavedJson: ""
    onSavedOrderJsonChanged: {
        if (hasDraft && savedOrderJson === expectedSavedJson) hasDraft = false;
    }

    readonly property string effectiveOrderJson: hasDraft ? draftJson : savedOrderJson
    readonly property var resolved: OrderLogic.resolve(
        effectiveOrderJson,
        BarIconOrder.pluginBarItems,
        function(text) { return Eitr.I18n.tr(text); }
    )
    readonly property bool isCustomized: !OrderLogic.ordersEqual(resolved.idsByZone, resolved.defaultIdsByZone) || effectiveOrderJson !== ""

    property string grabbedId: ""
    property string grabOriginJson: ""
    property string focusChipId: ""
    property string hoveredId: ""

    property string draggingId: ""
    property bool dragActive: false
    property string dragTitle: ""
    property string dragGlyph: ""
    property string dropZone: ""
    property int dropIndex: -1
    property point dragPoint: Qt.point(0, 0)
    property var zoneContainers: ({})

    onVisibleChanged: if (!visible) cancelInteraction()
    function dismiss() { return cancelInteraction(); }

    readonly property var previewZones: {
        if (dragActive && draggingId && dropZone && dropIndex >= 0) {
            const moved = OrderLogic.moveItem(resolved.idsByZone, draggingId, dropZone, dropIndex, hiddenIds);
            return OrderLogic.resolve(OrderLogic.serializeOrder(moved), BarIconOrder.pluginBarItems,
                function(text) { return Eitr.I18n.tr(text); }).zones;
        }
        return resolved.zones;
    }

    function registerZone(zoneId, zoneBox) {
        const next = Object.assign({}, zoneContainers);
        next[zoneId] = zoneBox;
        zoneContainers = next;
    }

    function unregisterZone(zoneId, zoneBox) {
        if (zoneContainers[zoneId] !== zoneBox) return;
        const next = Object.assign({}, zoneContainers);
        delete next[zoneId];
        zoneContainers = next;
    }

    function applyOrderJson(nextJson, resetDefault) {
        const normalized = resetDefault ? "" : nextJson;
        draftJson = normalized;
        expectedSavedJson = normalized;
        hasDraft = true;
        BarIconOrder.savedOrderJson = normalized;
        if (view && view.live && styleModel && styleModel.settingRequested)
            styleModel.settingRequested("iconOrder", resetDefault ? "reset" : normalized);
    }

    function resetToDefault() {
        grabbedId = "";
        grabOriginJson = "";
        clearDrag();
        applyOrderJson("", true);
    }

    function toggleGrab(chipId) {
        if (grabbedId === chipId) {
            grabbedId = "";
            grabOriginJson = "";
        } else {
            grabOriginJson = effectiveOrderJson;
            grabbedId = chipId;
        }
    }

    function cancelInteraction() {
        if (dragActive || draggingId) {
            clearDrag();
            return true;
        }
        if (grabbedId) {
            const restoreId = grabbedId;
            grabbedId = "";
            if (grabOriginJson !== effectiveOrderJson) {
                applyOrderJson(grabOriginJson, grabOriginJson === "");
            }
            grabOriginJson = "";
            queueFocusRestore(restoreId);
            return true;
        }
        return false;
    }

    function clearDrag() {
        draggingId = "";
        dragActive = false;
        dragTitle = "";
        dragGlyph = "";
        dropZone = "";
        dropIndex = -1;
    }

    function queueFocusRestore(chipId) {
        focusChipId = chipId;
        restoreFocusTimer.restart();
    }

    function restoreChipFocus() {
        if (!focusChipId) return;
        const targetId = focusChipId;
        for (const zoneName of OrderLogic.ZONES) {
            const container = zoneContainers[zoneName];
            if (!container) continue;
            for (const chip of container.flowChips()) {
                if (chip.chipId === targetId) {
                    chip.forceActiveFocus();
                    return;
                }
            }
        }
    }

    Timer {
        id: restoreFocusTimer
        interval: 0
        onTriggered: iconsPage.restoreChipFocus()
    }

    function moveFocusAdjacent(fromId, direction) {
        const flat = [];
        for (const zoneName of OrderLogic.ZONES) {
            for (const entry of resolved.zones[zoneName] || []) {
                if (!hiddenIds[entry.id]) flat.push(entry.id);
            }
        }
        const idx = flat.indexOf(fromId);
        if (idx < 0) return;
        const delta = (direction === "left" || direction === "up") ? -1 : 1;
        const nextIdx = Math.max(0, Math.min(flat.length - 1, idx + delta));
        if (flat[nextIdx] !== fromId) queueFocusRestore(flat[nextIdx]);
    }

    function moveGrabbed(id, direction) {
        const nextIds = OrderLogic.moveStep(resolved.idsByZone, id, direction, hiddenIds);
        if (OrderLogic.ordersEqual(nextIds, resolved.idsByZone)) return;
        applyOrderJson(OrderLogic.serializeOrder(nextIds), OrderLogic.ordersEqual(nextIds, resolved.defaultIdsByZone));
        queueFocusRestore(id);
    }

    function beginDrag(item, sourceItem, localPos) {
        grabbedId = "";
        draggingId = item.id;
        dragTitle = item.title;
        dragGlyph = item.glyph;
        dragActive = false;
        dragPoint = sourceItem.mapToItem(dragLayer, localPos.x, localPos.y);
    }

    function updateDrag(sourceItem, localPos) {
        if (!draggingId) return;
        dragPoint = sourceItem.mapToItem(dragLayer, localPos.x, localPos.y);
        if (!dragActive) dragActive = true;
        let chosenZone = "";
        let bestDist = Infinity;
        for (const zoneName of OrderLogic.ZONES) {
            const zoneBox = zoneContainers[zoneName];
            if (!zoneBox) continue;
            const topLeft = zoneBox.mapToItem(dragLayer, 0, 0);
            if (dragPoint.y >= topLeft.y && dragPoint.y <= topLeft.y + zoneBox.height) {
                chosenZone = zoneName;
                bestDist = 0;
                break;
            }
            const dist = dragPoint.y < topLeft.y ? topLeft.y - dragPoint.y : dragPoint.y - (topLeft.y + zoneBox.height);
            if (dist < bestDist) {
                bestDist = dist;
                chosenZone = zoneName;
            }
        }
        if (!chosenZone || !zoneContainers[chosenZone]) return;
        dropZone = chosenZone;
        dropIndex = zoneContainers[chosenZone].computeDropIndex(dragPoint);
    }

    function finishDrag() {
        if (dragActive && draggingId && dropZone && dropIndex >= 0) {
            const nextIds = OrderLogic.moveItem(resolved.idsByZone, draggingId, dropZone, dropIndex, hiddenIds);
            if (!OrderLogic.ordersEqual(nextIds, resolved.idsByZone)) {
                applyOrderJson(OrderLogic.serializeOrder(nextIds), OrderLogic.ordersEqual(nextIds, resolved.defaultIdsByZone));
            }
        }
        clearDrag();
    }

    width: parent ? parent.width : 0
    spacing: 18

    ControlCard {
        surface: SettingsPalette.surface
        line: SettingsPalette.line
        gold: SettingsInk.gold
        carved: true
        title: Eitr.I18n.tr("Icons")
        foreground: view.foreground

        Item {
            id: cardBody
            width: parent.width
            implicitHeight: layoutColumn.implicitHeight

            Column {
                id: layoutColumn
                width: parent.width
                spacing: 12

                BarIconPreviewStrip {
                    width: parent.width
                    zones: iconsPage.previewZones
                    foreground: view.foreground
                    surface: SettingsPalette.surface
                    line: SettingsPalette.line
                    accent: view.accent
                    gold: SettingsInk.gold
                    hoveredId: iconsPage.hoveredId
                    grabbedId: iconsPage.grabbedId || (iconsPage.dragActive ? iconsPage.draggingId : "")
                    hiddenIds: iconsPage.hiddenIds
                }

                Text {
                    id: statusHint
                    width: parent.width
                    wrapMode: Text.WordWrap
                    color: iconsPage.grabbedId ? SettingsInk.gold : Qt.alpha(view.foreground, 0.72)
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    text: iconsPage.grabbedId
                        ? Eitr.I18n.tr("Moving {name} · arrow keys reorder, Enter or Space drops, Esc cancels", {
                            name: (iconsPage.resolved.byId[iconsPage.grabbedId] || {}).title || ""
                        })
                        : Eitr.I18n.tr("Drag icons or press Space to move them between bar zones.")
                }

                Item {
                    width: parent.width
                    height: zonesColumn.implicitHeight
                    SettingsTarget { objectName: "setting-bar-icons-order" }

                    Column {
                        id: zonesColumn
                        width: parent.width
                        spacing: 10

                        Repeater {
                            model: [
                                {id: "left", label: Eitr.I18n.tr("Left side"), caption: Eitr.I18n.tr("Beside the workspaces.")},
                                {id: "clockStart", label: Eitr.I18n.tr("Before the clock"), caption: Eitr.I18n.tr("Centred just before the time.")},
                                {id: "clockEnd", label: Eitr.I18n.tr("After the clock"), caption: Eitr.I18n.tr("Centred right after the time.")},
                                {id: "right", label: Eitr.I18n.tr("Right side"), caption: Eitr.I18n.tr("System status tray and notifications.")}
                            ]
                            delegate: BarIconZoneRow {
                                required property var modelData
                                page: iconsPage
                                width: zonesColumn.width
                                zoneId: modelData.id
                                title: modelData.label
                                caption: modelData.caption
                                items: (iconsPage.resolved.zones[modelData.id] || []).filter(entry => !iconsPage.hiddenIds[entry.id])
                                foreground: view.foreground
                                accent: view.accent
                                gold: SettingsInk.gold
                                overlayLayer: dragLayer
                            }
                        }
                    }
                }
            }

            Item {
                id: dragLayer
                anchors.fill: parent
                z: 20

                Rectangle {
                    visible: iconsPage.dragActive
                    x: Math.max(0, Math.min(dragLayer.width - width, iconsPage.dragPoint.x - width / 2))
                    y: Math.max(0, Math.min(dragLayer.height - height, iconsPage.dragPoint.y - height / 2))
                    width: proxyRow.implicitWidth + 20
                    height: 32
                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                    color: SettingsPalette.raised
                    border.width: 1.5
                    border.color: SettingsInk.gold

                    Row {
                        id: proxyRow
                        anchors.centerIn: parent
                        spacing: 6
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: iconsPage.dragGlyph || "󰐱"
                            color: SettingsInk.gold
                            font.family: DesktopFonts.family
                            font.pixelSize: 15
                            font.bold: true
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: iconsPage.dragTitle
                            color: view.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                        }
                    }
                }
            }
        }

        ControlRow {
            SettingsTarget { objectName: "setting-bar-icons-reset" }
            text: Eitr.I18n.tr("Reset order")
            description: Eitr.I18n.tr("Restore all built-in and plugin bar icons to their default zones.")
            foreground: view.foreground
            PanelButton {
                id: resetButton
                objectName: "bar-icons-reset-button"
                text: Eitr.I18n.tr("Reset to default")
                width: Math.max(156, Math.ceil(resetMetrics.advanceWidth) + 28)
                available: iconsPage.isCustomized
                foreground: view.foreground
                onClicked: iconsPage.resetToDefault()
                TextMetrics {
                    id: resetMetrics
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.controlSize
                    text: resetButton.text
                }
            }
        }
    }
}
