import ".."
import Eitr as Eitr
import Quickshell.Io
import "../PanelStyle.js" as PanelStyle
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../DockModel.js" as DockModel
import "../JsonState.js" as JsonState

PanelWindow {
    id: dock
    function run(command) { if (command.length) Quickshell.execDetached(command); }
    required property string barEdge
    required property var clients
    required property color foreground
    required property color background
    property color accent: foreground
    property bool dockEnabled: true
    property bool dockPreviews: true
    property var pinnedEntries: []
    property var menuEntry: null
    property point menuPosition: Qt.point(0, 0)
    readonly property bool interacting: available && (menuOpen || previewOpen || surface.dragging || surface.hovered)
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
    // Recomputed when its inputs change rather than bound: looking up desktop entries can
    // update them while the groups are built, which as a binding is a loop (monitor hotplug).
    property var apps: []
    function updateApps() { apps = DockModel.groups(clients, workspaceId, pinnedEntries, surface.application); }
    onClientsChanged: updateApps()
    onWorkspaceIdChanged: updateApps()
    onPinnedEntriesChanged: updateApps()
    onAppsChanged: if (previewAppId !== "") syncPreviews()
    Connections { target: surface; function onDesktopEntriesChanged() { Qt.callLater(dock.updateApps); } }
    Connections { target: Hyprland.toplevels; function onValuesChanged() { if (dock.previewAppId !== "") dock.syncPreviews(); } }
    Component.onCompleted: updateApps()
    property string previewAppId: ""
    property rect previewAnchorRect: Qt.rect(0, 0, 0, 0)
    property string previewAppName: ""
    property string previewIconSource: ""
    property bool previewEitrTerminal: false
    property var previewAddresses: []
    property var previewWindowMap: ({})
    readonly property var previewEntry: previewAppId ? (apps.find(entry => entry.id === previewAppId) || null) : null
    readonly property bool previewOpen: available && !menuOpen && !surface.dragging && previewAppId !== "" && previewAddresses.length > 0
    readonly property Item hoveredSlot: available && !menuOpen && !surface.dragging && reveal.progress >= 1 ? surface.hoveredSlotItem : null
    readonly property var hoveredApp: hoveredSlot && hoveredSlot.modelData && hoveredSlot.modelData.windows && hoveredSlot.modelData.windows.length > 0 ? hoveredSlot.modelData : null
    function syncPreviews() {
        var entry = previewAppId ? (apps.find(candidate => candidate.id === previewAppId) || null) : null;
        if (!entry || !entry.windows || entry.windows.length === 0) {
            previewAppId = "";
            return;
        }
        var items = DockModel.previewWindows(entry, Hyprland.toplevels.values);
        var nextMap = ({});
        var nextAddresses = [];
        for (var item of items) {
            nextMap[item.address] = item;
            nextAddresses.push(item.address);
        }
        previewWindowMap = nextMap;
        if (JsonState.changed(previewAddresses, nextAddresses)) previewAddresses = nextAddresses;
    }
    function openPreviewForSlot(slotItem) {
        if (!slotItem || !slotItem.modelData || !slotItem.modelData.windows || slotItem.modelData.windows.length === 0) return;
        var rect = surface.slotAnchorRect(slotItem);
        var origin = surface.mapToItem(dock.contentItem, rect.x, rect.y);
        previewAnchorRect = Qt.rect(origin.x, origin.y, rect.width, rect.height);
        previewAppName = slotItem.appName || "";
        previewIconSource = slotItem.iconSource || "";
        previewEitrTerminal = !!slotItem.eitrTerminal;
        previewAppId = slotItem.modelData.id;
        syncPreviews();
        Hyprland.refreshToplevels();
    }
    function closePreviews() {
        previewOpenDelay.stop();
        previewCloseDelay.stop();
        previewAppId = "";
    }
    onMenuOpenChanged: if (menuOpen) closePreviews()
    onHoveredSlotChanged: {
        if (hoveredSlot && (!hoveredSlot.modelData || hoveredSlot.modelData.windows.length === 0))
            closePreviews();
    }
    onHoveredAppChanged: {
        if (hoveredApp) {
            previewCloseDelay.stop();
            if (previewOpen) {
                if (hoveredApp.id !== previewAppId) openPreviewForSlot(hoveredSlot);
            } else {
                previewOpenDelay.restart();
            }
        } else {
            previewOpenDelay.stop();
            if (previewOpen && !previewCard.hovered) previewCloseDelay.restart();
        }
    }
    Timer {
        id: previewOpenDelay
        interval: 160
        onTriggered: if (dock.hoveredApp && dock.hoveredSlot) dock.openPreviewForSlot(dock.hoveredSlot)
    }
    Timer {
        id: previewCloseDelay
        interval: 220
        onTriggered: if (!dock.hoveredApp && !previewCard.hovered) dock.closePreviews()
    }
    Timer {
        interval: 1000
        repeat: true
        running: dock.previewOpen
        onTriggered: Hyprland.refreshToplevels()
    }
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
    onAvailableChanged: if (!available) { menuEntry = null; surface.dragEntry = null; reveal.revealed = false; closePreviews(); }
    mask: Region {
        width: dock.menuOpen ? dock.width : 0; height: dock.menuOpen ? dock.height : 0
        Region { item: dock.available ? sensor : null }
        Region { item: dock.available && reveal.progress > 0 ? surfaceArea : null }
        Region { item: dock.available && previewCard.visible ? previewArea : null }
    }
    HyprlandFocusGrab { active: dock.menuOpen; windows: [dock]; onCleared: dock.menuEntry = null }
    BarAutoHide {
        id: reveal
        held: dock.menuOpen || surface.dragging || dock.previewOpen
        autoHide: true
        revealed: false
        pointerInside: dock.available && (edgeHover.hovered || surface.hovered || previewCard.hovered)
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
    Item {
        id: previewArea
        x: previewCard.x; y: previewCard.y; width: previewCard.width; height: previewCard.height
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
        onDraggingChanged: if (dragging) dock.closePreviews()
        onPinsRequested: function(pins) { dock.savePins(pins); }
        onContextRequested: function(entry, position) {
            dock.closePreviews();
            dock.menuEntry = entry;
            dock.menuPosition = surface.mapToItem(dock.contentItem, position.x, position.y);
            Qt.callLater(function() { if (dock.menuOpen) menu.forceActiveFocus(); });
        }
        onActivated: function(entry) {
            dock.closePreviews();
            var target = DockModel.activationTarget(entry);
            if (!target) dock.launch(entry);
            if (target) dock.run(DockModel.windowCommand("focus", target.address));
        }
        onCloseRequested: function(entry) { if (entry.recent) dock.run(DockModel.windowCommand("close", entry.recent.address)); }
    }

    DockPreviewCard {
        id: previewCard
        dockEdge: dock.edge
        anchorRect: dock.previewAnchorRect
        screenWidth: dock.width
        screenHeight: dock.height
        foreground: dock.foreground
        background: dock.background
        accent: dock.accent
        opened: dock.previewOpen
        previewsEnabled: dock.dockPreviews
        appName: dock.previewAppName
        iconSource: dock.previewIconSource
        eitrTerminal: dock.previewEitrTerminal
        windowAddresses: dock.previewAddresses
        windowMap: dock.previewWindowMap
        onHoveredChanged: {
            if (hovered) previewCloseDelay.stop();
            else if (dock.previewOpen && !dock.hoveredApp) previewCloseDelay.restart();
        }
        onVisibleChanged: {
            if (!visible && !dock.previewOpen) Qt.callLater(function() {
                if (!previewCard.visible && !dock.previewOpen) {
                    dock.previewAddresses = [];
                    dock.previewWindowMap = ({});
                }
            });
        }
        onFocusRequested: function(address) {
            dock.closePreviews();
            dock.run(DockModel.windowCommand("focus", address));
        }
        onCloseRequested: function(address) {
            dock.run(DockModel.windowCommand("close", address));
        }
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
