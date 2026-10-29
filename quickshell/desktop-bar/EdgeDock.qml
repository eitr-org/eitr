import Eitr as Eitr
import Quickshell.Io
import "PanelStyle.js" as PanelStyle
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
    property var menuEntry: null
    property point menuPosition: Qt.point(0, 0)
    readonly property bool menuOpen: menuEntry !== null
    property string pendingPins: ""
    function savePins(pins) {
        pinnedEntries = pins;
        pendingPins = JSON.stringify(pins);
        writeDelay.restart();
    }
    function launch(entry) {
        if (!entry.desktopId) return;
        var id = /\.desktop$/i.test(entry.desktopId) ? entry.desktopId : entry.desktopId + ".desktop";
        run([Eitr.Paths.code("walker/bin/app-launch"), "--desktop", id]);
    }
    function togglePin(entry) {
        var id = entry.desktopId || (entry.pinned ? entry.appClass : "");
        if (id) savePins(DockModel.movePin(pinnedEntries, id, pinnedEntries.length, !entry.pinned));
    }
    function closeWindows(entry) {
        for (var client of entry.windows) run(DockModel.windowCommand("close", client.address));
    }
    FileView {
        id: pinsFile
        path: Eitr.Paths.config("quickshell/desktop-bar/dock-pins.json")
        watchChanges: true; printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                var value = Eitr.Paths.settings(text());
                if (Array.isArray(value.pins) && value.pins.every(pin => typeof pin === "string" && pin.length > 0))
                    dock.pinnedEntries = value.pins;
            } catch (error) { console.warn("Dock pins:", error); }
        }
    }
    Timer {
        id: writeDelay
        interval: 40
        onTriggered: {
            if (pinWriter.running) { restart(); return; }
            pinWriter.command = ["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/dock-pins.py"), "set", dock.pendingPins];
            pinWriter.running = true;
        }
    }
    Process {
        id: pinWriter
        onExited: function(code) { if (code !== 0) { console.warn("Could not save dock pins"); pinsFile.reload(); } }
    }
    readonly property string edge: DockModel.opposite(barEdge)
    readonly property bool vertical: edge === "left" || edge === "right"
    readonly property var monitor: Hyprland.monitorFor(screen)
    readonly property bool fullscreen: !!(monitor && monitor.activeWorkspace && monitor.activeWorkspace.hasFullscreen)
    readonly property int workspaceId: monitor && monitor.activeWorkspace ? monitor.activeWorkspace.id : 0
    readonly property var apps: DockModel.groups(clients, workspaceId, pinnedEntries, surface.application)
    readonly property bool available: dockEnabled && !fullscreen && apps.length > 0
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    exclusiveZone: 0
    // Share the bar namespace's theme blur rule.
    WlrLayershell.namespace: "desktop-bar"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: menuOpen ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
    visible: available
    onAvailableChanged: if (!available) { menuEntry = null; surface.dragEntry = null; reveal.revealed = false; }
    mask: Region {
        width: dock.menuOpen ? dock.width : 0; height: dock.menuOpen ? dock.height : 0
        Region { item: dock.available ? sensor : null }
        Region { item: dock.available && reveal.progress > 0 ? surfaceArea : null }
    }
    HyprlandFocusGrab { active: dock.menuOpen; windows: [dock]; onCleared: dock.menuEntry = null }
    BarAutoHide {
        id: reveal
        held: dock.menuOpen || surface.dragging
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
    MouseArea {
        anchors.fill: parent
        visible: dock.menuOpen
        acceptedButtons: Qt.AllButtons
        onPressed: dock.menuEntry = null
    }
    EdgeDockContent {
        id: surface
        barEdge: dock.edge
        menuOpen: dock.menuOpen
        apps: dock.apps
        foreground: dock.foreground; background: dock.background
        revealProgress: reveal.progress
        availableLength: Math.max(0, (dock.vertical ? dock.height : dock.width) - 16)
        x: dock.vertical ? (dock.edge === "right" ? dock.width - width : 0) : (dock.width - width) / 2
        y: dock.vertical ? (dock.height - height) / 2 : (dock.edge === "bottom" ? dock.height - height : 0)
        onPinsRequested: function(pins) { dock.savePins(pins); }
        onContextRequested: function(entry, position) {
            dock.menuEntry = entry;
            dock.menuPosition = surface.mapToItem(dock.contentItem, position.x, position.y);
            Qt.callLater(function() { if (dock.menuOpen) menu.forceActiveFocus(); });
        }
        onActivated: function(entry) {
            var target = DockModel.activationTarget(entry);
            if (!target) dock.launch(entry);
            if (target) dock.run(DockModel.windowCommand("focus", target.address));
        }
        onCloseRequested: function(entry) { if (entry.recent) dock.run(DockModel.windowCommand("close", entry.recent.address)); }
    }

    Rectangle {
        id: menu
        objectName: "dockContextMenu"
        visible: dock.menuOpen
        width: 250; height: menuRows.height + 12
        x: Math.max(6, Math.min(dock.width - width - 6, dock.vertical ? (dock.edge === "left" ? surface.width + 6 : surface.x - width - 6) : dock.menuPosition.x - width / 2))
        y: Math.max(6, Math.min(dock.height - height - 6, dock.vertical ? dock.menuPosition.y - height / 2 : (dock.edge === "top" ? surface.height + 6 : surface.y - height - 6)))
        radius: DesktopStyle.radius(PanelStyle.controlRadius + 4)
        color: dock.background
        border.color: Qt.alpha(dock.foreground, PanelStyle.selectionBorderAlpha)
        Keys.onEscapePressed: dock.menuEntry = null
        Column {
            id: menuRows
            x: 6; y: 6; width: parent.width - 12; spacing: 2
            PanelButton {
                objectName: "dockPinAction"
                width: parent.width; height: PanelStyle.selectionRowHeight
                foreground: dock.foreground; flat: true; textAlignment: Text.AlignLeft
                text: dock.menuEntry && dock.menuEntry.pinned ? Eitr.I18n.tr("Remove from Dock") : Eitr.I18n.tr("Keep in Dock")
                available: !!dock.menuEntry && (dock.menuEntry.pinned || !!dock.menuEntry.desktopId)
                onClicked: { var entry = dock.menuEntry; dock.menuEntry = null; dock.togglePin(entry); }
            }
            PanelButton {
                width: parent.width; height: PanelStyle.selectionRowHeight
                visible: !!dock.menuEntry && !!dock.menuEntry.desktopId
                foreground: dock.foreground; flat: true; textAlignment: Text.AlignLeft
                text: Eitr.I18n.tr("New Window")
                onClicked: { var entry = dock.menuEntry; dock.menuEntry = null; dock.launch(entry); }
            }
            PanelButton {
                width: parent.width; height: PanelStyle.selectionRowHeight
                visible: !!dock.menuEntry && dock.menuEntry.windows.length > 0
                foreground: dock.foreground; flat: true; textAlignment: Text.AlignLeft
                text: dock.menuEntry && dock.menuEntry.windows.length > 1 ? Eitr.I18n.tr("Close All Windows") : Eitr.I18n.tr("Close")
                onClicked: { var entry = dock.menuEntry; dock.menuEntry = null; dock.closeWindows(entry); }
            }
        }
    }
}
