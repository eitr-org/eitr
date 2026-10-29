import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "DockModel.js" as DockModel

PanelWindow {
    id: dock
    function run(command) { if (command.length) Quickshell.execDetached(command); }
    required property string barEdge
    required property var clients
    required property color foreground
    required property color background
    property bool dockEnabled: true
    property var pinnedEntries: []
    readonly property string edge: DockModel.opposite(barEdge)
    readonly property bool vertical: edge === "left" || edge === "right"
    readonly property var monitor: Hyprland.monitorFor(screen)
    readonly property bool fullscreen: !!(monitor && monitor.activeWorkspace && monitor.activeWorkspace.hasFullscreen)
    readonly property int workspaceId: monitor && monitor.activeWorkspace ? monitor.activeWorkspace.id : 0
    readonly property var apps: DockModel.groups(clients, workspaceId, pinnedEntries)
    readonly property bool available: dockEnabled && !fullscreen && apps.length > 0
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    exclusiveZone: 0
    // Share the bar namespace's theme blur rule.
    WlrLayershell.namespace: "desktop-bar"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    visible: available
    onAvailableChanged: if (!available) reveal.revealed = false
    mask: Region {
        width: 0; height: 0
        Region { item: dock.available ? sensor : null }
        Region { item: dock.available && reveal.progress > 0 ? surfaceArea : null }
    }
    BarAutoHide {
        id: reveal
        autoHide: true
        revealed: false
        pointerInside: dock.available && (edgeHover.hovered || surface.hovered)
    }
    Item {
        id: sensor
        width: dock.vertical ? 1 : dock.width
        height: dock.vertical ? dock.height : 1
        x: dock.edge === "right" ? dock.width - width : 0
        y: dock.edge === "bottom" ? dock.height - height : 0
        HoverHandler { id: edgeHover }
    }
    // The input mask covers the whole resting surface; it unfolds inside it.
    Item {
        id: surfaceArea
        x: surface.x; y: surface.y; width: surface.width; height: surface.height
    }
    EdgeDockContent {
        id: surface
        barEdge: dock.edge
        apps: dock.apps
        foreground: dock.foreground; background: dock.background
        revealProgress: reveal.progress
        availableLength: Math.max(0, (dock.vertical ? dock.height : dock.width) - 16)
        x: dock.vertical ? (dock.edge === "right" ? dock.width - width : 0) : (dock.width - width) / 2
        y: dock.vertical ? (dock.height - height) / 2 : (dock.edge === "bottom" ? dock.height - height : 0)
        onActivated: function(entry) {
            var target = DockModel.activationTarget(entry);
            if (target) dock.run(DockModel.windowCommand("focus", target.address));
        }
        onCloseRequested: function(entry) { if (entry.recent) dock.run(DockModel.windowCommand("close", entry.recent.address)); }
    }
}
