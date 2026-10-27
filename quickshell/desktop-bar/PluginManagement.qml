pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

Column {
    id: management
    required property var entries
    required property color foreground
    required property color background
    property var monitors: Quickshell.screens.map(screen => ({name: screen.name, description: screen.model || screen.description || screen.name}))
    spacing: PanelStyle.selectionRowGap
    function monitorName(name) {
        const monitor = monitors.find(monitor => monitor.name === name);
        return monitor ? monitor.description : name;
    }
    readonly property var rows: {
        const result = [];
        const disabled = [];
        for (const entry of entries) {
            if (entry.disabled) {
                if (disabled.indexOf(entry.plugin) === -1) {
                    disabled.push(entry.plugin);
                    result.push({entry: entry, monitor: "", placed: false});
                }
                continue;
            }
            if (entry.kind !== "widgets" && entry.kind !== "barItems") continue;
            const placements = (PluginRegistry.placements[entry.kind] || []).filter(placement => placement.plugin === entry.plugin && placement.id === entry.id);
            if (placements.length) {
                for (const placement of placements) result.push({entry: entry, monitor: placement.monitor || "", aboveWindows: !!placement.aboveWindows, placed: true});
            } else result.push({entry: entry, monitor: "", placed: false});
        }
        return result.sort((first, second) => (first.entry.pluginName || "").localeCompare(second.entry.pluginName || "") || first.entry.title.localeCompare(second.entry.title) || first.monitor.localeCompare(second.monitor));
    }
    Repeater {
        model: management.rows
        Column {
            id: visual
            required property var modelData
            readonly property var entry: modelData.entry
            readonly property bool editing: PluginRegistry.editing && PluginRegistry.editTarget !== null && PluginRegistry.editTarget.plugin === entry.plugin && PluginRegistry.editTarget.id === entry.id && PluginRegistry.editTarget.monitor === modelData.monitor
            property bool choosing: false
            property bool optionsOpen: false
            readonly property var availableMonitors: management.monitors.filter(monitor => !(PluginRegistry.placements.widgets || []).some(placement => placement.plugin === entry.plugin && placement.id === entry.id && placement.monitor === monitor.name))
            width: management.width; spacing: PanelStyle.selectionRowGap
            Rectangle {
                width: visual.width; height: PanelStyle.selectionRowHeight
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: Qt.rgba(management.foreground.r, management.foreground.g, management.foreground.b, PanelStyle.selectionAlpha(visual.modelData.placed, false))
                border.width: PanelStyle.selectionBorderWidth(visual.modelData.placed)
                border.color: Qt.rgba(management.foreground.r, management.foreground.g, management.foreground.b, PanelStyle.selectionBorderAlpha)
                Text {
                    x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter
                    width: 18; horizontalAlignment: Text.AlignHCenter
                    text: visual.entry.icon || (visual.entry.disabled ? "󰒓" : visual.entry.kind === "widgets" ? "󰍹" : "󰕮")
                    color: management.foreground; font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
                }
                Column {
                    x: PanelStyle.selectionTextInset; anchors.verticalCenter: parent.verticalCenter
                    width: actions.x - x - PanelStyle.selectionActionGap
                    spacing: PanelStyle.selectionDetailGap
                    Text {
                        width: parent.width; text: visual.entry.disabled ? visual.entry.pluginName || Eitr.I18n.tr("Plugin") : visual.entry.title
                        textFormat: Text.PlainText; elide: Text.ElideRight
                        color: management.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    }
                    Text {
                        width: parent.width
                        text: visual.entry.disabled ? Eitr.I18n.tr("Visuals disabled") : (visual.entry.pluginName || Eitr.I18n.tr("Plugin")) + (visual.modelData.monitor ? " · " + management.monitorName(visual.modelData.monitor) : "")
                        textFormat: Text.PlainText; elide: Text.ElideRight
                        color: management.foreground; opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                    }
                }
                Row {
                    id: actions
                    anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset
                    anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionActionGap
                    PanelButton {
                        visible: !visual.entry.disabled && visual.entry.kind === "widgets" && visual.modelData.placed
                        width: 24; height: 24; icon: true; text: "⋯"; foreground: management.foreground
                        Accessible.name: Eitr.I18n.tr("Widget options")
                        onClicked: visual.optionsOpen = !visual.optionsOpen
                    }
                    PanelButton {
                        visible: !visual.entry.disabled && visual.entry.kind === "widgets" && visual.modelData.placed
                        width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight
                        icon: true; text: "󰁝"; foreground: management.foreground
                        selected: !!visual.modelData.aboveWindows
                        readonly property string label: Eitr.I18n.tr("Show above windows")
                        Accessible.name: label
                        Accessible.checkable: true; Accessible.checked: selected
                        onClicked: PluginRegistry.change("toggle-layer", visual.entry, visual.modelData.monitor, null)
                        HoverHandler { id: layerHover }
                        BarTooltip { target: parent; hovered: layerHover.hovered; text: parent.label; foreground: management.foreground; background: management.background }
                    }
                    PanelButton {
                        visible: !visual.entry.disabled && visual.entry.kind === "widgets" && visual.modelData.placed
                        width: 24; height: 24; icon: true; text: visual.editing ? "󰄬" : "󰏫"; foreground: management.foreground
                        readonly property string label: visual.editing ? Eitr.I18n.tr("Done editing widgets") : Eitr.I18n.tr("Edit position")
                        Accessible.name: label
                        onClicked: {
                            const wasEditing = visual.editing;
                            PluginRegistry.editTarget = {plugin: visual.entry.plugin, id: visual.entry.id, monitor: visual.modelData.monitor};
                            PluginRegistry.editing = !wasEditing;
                        }
                        HoverHandler { id: editHover }
                        BarTooltip { target: parent; hovered: editHover.hovered; text: parent.label; foreground: management.foreground; background: management.background }
                    }
                    PanelButton {
                        width: 24; height: 24; icon: true; foreground: management.foreground
                        text: visual.entry.disabled ? "󰑐" : visual.modelData.placed ? "󰅖" : "+"
                        readonly property string label: visual.entry.disabled ? Eitr.I18n.tr("Re-enable") : visual.modelData.placed ? Eitr.I18n.tr("Remove") : Eitr.I18n.tr("Add")
                        Accessible.name: label
                        available: visual.entry.disabled || visual.modelData.placed || visual.entry.kind !== "widgets" || visual.availableMonitors.length > 0
                        onClicked: {
                            if (visual.entry.disabled) PluginRegistry.change("enable-ui", visual.entry, "", null);
                            else if (visual.modelData.placed) PluginRegistry.change("unplace", visual.entry, visual.modelData.monitor, null);
                            else if (visual.entry.kind === "widgets" && visual.availableMonitors.length > 1) visual.choosing = !visual.choosing;
                            else PluginRegistry.change("place", visual.entry, visual.entry.kind === "widgets" ? visual.availableMonitors[0].name : "", null);
                        }
                        HoverHandler { id: actionHover }
                        BarTooltip { target: parent; hovered: actionHover.hovered; text: parent.label; foreground: management.foreground; background: management.background }
                    }
                    PanelButton {
                        visible: !visual.entry.disabled && visual.entry.kind === "widgets" && visual.modelData.placed && visual.availableMonitors.length > 0
                        width: 24; height: 24; icon: true; text: "+"; foreground: management.foreground
                        Accessible.name: Eitr.I18n.tr("Add")
                        onClicked: {
                            if (visual.availableMonitors.length > 1) visual.choosing = !visual.choosing;
                            else PluginRegistry.change("place", visual.entry, visual.availableMonitors[0].name, null);
                        }
                        HoverHandler { id: addHover }
                        BarTooltip { target: parent; hovered: addHover.hovered; text: Eitr.I18n.tr("Add"); foreground: management.foreground; background: management.background }
                    }
                }
            }
            PluginWidgetMenu {
                width: parent.width; visible: visual.optionsOpen; height: visible ? implicitHeight : 0
                foreground: management.foreground; background: management.background
                aboveWindows: !!visual.modelData.aboveWindows
                surface: {
                    const placement = (PluginRegistry.placements.widgets || []).find(placement => placement.plugin === visual.entry.plugin && placement.id === visual.entry.id && placement.monitor === visual.modelData.monitor);
                    return PluginRegistry.widgetSurface(Object.assign({}, visual.entry, {geometry: placement}));
                }
                entries: PluginRegistry.widgetMenus[PluginRegistry.menuKey(visual.entry, visual.modelData.monitor)] || []
                onAction: function(action) {
                    if (action === "panel" || action === "none") PluginRegistry.change("surface", visual.entry, visual.modelData.monitor, null, action);
                    else if (action === "layer") PluginRegistry.change("toggle-layer", visual.entry, visual.modelData.monitor, null);
                    else if (action === "remove") PluginRegistry.change("unplace", visual.entry, visual.modelData.monitor, null);
                    else PluginRegistry.widgetAction(visual.entry.plugin, visual.entry.id, visual.modelData.monitor, action, false);
                }
                onSelected: id => PluginRegistry.widgetAction(visual.entry.plugin, visual.entry.id, visual.modelData.monitor, id, true)
            }
            Column {
                width: parent.width; visible: visual.choosing; spacing: PanelStyle.selectionRowGap
                Repeater {
                    model: visual.choosing ? visual.availableMonitors : []
                    PanelButton {
                        required property var modelData
                        width: visual.width; height: 36; foreground: management.foreground
                        text: modelData.description; textAlignment: Text.AlignLeft
                        onClicked: { PluginRegistry.change("place", visual.entry, modelData.name, null); visual.choosing = false; }
                    }
                }
            }
        }
    }
}
