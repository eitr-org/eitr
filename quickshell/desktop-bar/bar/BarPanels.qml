import ".."
import QtQuick
import Eitr as Eitr
import Quickshell.Io

Item {
    id: panels
    required property var host
    required property var barHost
    readonly property var batteryMenuItem: batteryMenuLoader.item
    readonly property var controlCenterItem: controlCenterLoader.item
    readonly property var mediaMenuItem: mediaMenuLoader.item
    readonly property var dropDashboardItem: dropDashboardLoader.item
    readonly property var notificationCenterItem: notificationCenterLoader.item
    readonly property alias notificationPopupsItem: notificationPopups
    readonly property alias panelIpcItem: panelIpc
    readonly property var pluginPanelItem: pluginPanelLoader.item
    function ensure(kind) {
        const loaders = {notifications: notificationCenterLoader, plugin: pluginPanelLoader,
            center: controlCenterLoader, media: mediaMenuLoader, dashboard: dropDashboardLoader, battery: batteryMenuLoader};
        const loader = loaders[kind];
        if (!loader) return null;
        loader.active = true;
        loader.asynchronous = false;
        return loader.item;
    }
    function toggleKind(kind) { panels.barHost.togglePanel(ensure(kind)); }
    // Incubate one closed panel at a time, after the bar has had time to present.
    Timer {
        interval: 3500
        running: true
        repeat: true
        property int next: 0
        property var loaders: [notificationCenterLoader, controlCenterLoader, mediaMenuLoader,
            batteryMenuLoader, pluginPanelLoader, dropDashboardLoader]
        onTriggered: {
            if (next >= loaders.length) { stop(); return; }
            loaders[next++].active = true;
            interval = 500;
        }
    }
    NotificationPopups {
        id: notificationPopups
        screen: panels.barHost.screen
        shown: panels.barHost.isMainBar || panels.barHost.notificationsRef.popupsOnAllDisplays
        service: panels.barHost.notificationsRef
        foreground: panels.host.fg
        background: panels.host.barBackground()
        accent: panels.host.activeBg
        barEdge: panels.host.barEdge
    }

    Loader {
        id: notificationCenterLoader
        active: false
        asynchronous: true
        sourceComponent: NotificationCenter {
            id: notificationCenter
            readonly property string notifyZone: panels.barHost.iconZone("notifications") || "right"
            service: panels.barHost.notificationsRef
            maximumHeight: panels.barHost.screen.height - 70
            target: panels.barHost.iconTarget("notifications", panels.host.verticalBar ? panels.barHost.verticalNotificationIcon : panels.barHost.notificationIcon)
            leftAligned: notifyZone === "left"
            centered: notifyZone === "clockStart" || notifyZone === "clockEnd"
            barEdge: panels.host.barEdge
            surfaceColor: panels.host.barBackground()
            foreground: panels.host.fg
            background: panels.host.workspaceMenuBg
            accent: panels.host.activeBg
        }
    }


    Loader {
        id: pluginPanelLoader
        active: false
        asynchronous: true
        sourceComponent: PluginPanel {
            id: pluginPanel
            clockFormat: panels.host.barClock
            target: panels.barHost.notificationIcon
            barEdge: panels.host.barEdge; surfaceColor: panels.host.barBackground()
            foreground: panels.host.fg; background: panels.host.workspaceMenuBg; accent: panels.host.activeBg
        }
    }

    // Opens a placed plugin bar item's panel as its click does (IPC `panels plugin`).
    function clickPlugin(plugin) {
        function find(item, visibleOnly) {
            if (item.barItem === true && item.entry && item.entry.plugin === plugin && (!visibleOnly || item.visible)) return item;
            for (const child of item.children || []) { const found = find(child, visibleOnly); if (found) return found; }
            return null;
        }
        const item = find(panels.barHost.contentItem, true) || find(panels.barHost.contentItem, false);
        if (item && item.entry.panel) panels.barHost.openPluginPanel(plugin, item.entry.panel, item);
        return item !== null;
    }
    function openPluginPanel(plugin, panel, target) {
        ensure("plugin");
        var entry = PluginRegistry.entries.find(entry => entry.plugin === plugin && entry.id === panel && entry.kind === "panels");
        if (!entry) return;
        const placed = PluginRegistry.placedBarItems.find(item => item.plugin === plugin && item.panel === panel);
        const targetId = target && target.entry ? BarIconOrder.pluginId(target.entry) : (placed ? BarIconOrder.pluginId(placed) : "");
        const fallbackSlot = target && target.entry ? target.entry.slot || "status" : placed ? placed.slot || "status" : "status";
        const effectiveSlot = placed ? BarIconOrder.pluginSlot(placed.plugin, placed.id, fallbackSlot)
            : (target && target.entry ? BarIconOrder.pluginSlot(target.entry.plugin, target.entry.id, fallbackSlot) : fallbackSlot);
        panels.pluginPanelItem.placementSlot = effectiveSlot;
        panels.pluginPanelItem.leftAligned = effectiveSlot === "start";
        panels.pluginPanelItem.clockSlot = effectiveSlot === "clock" || effectiveSlot === "clockEnd";
        panels.pluginPanelItem.centered = panels.pluginPanelItem.clockSlot;
        panels.pluginPanelItem.target = targetId ? panels.barHost.iconTarget(targetId, target || panels.barHost.stripItem) : (target || panels.barHost.stripItem);
        // Clearing first restarts the shared panel's content and data for the new plugin.
        if (panels.pluginPanelItem.entry && (panels.pluginPanelItem.entry.plugin !== entry.plugin || panels.pluginPanelItem.entry.id !== entry.id)) panels.pluginPanelItem.entry = null;
        panels.pluginPanelItem.entry = entry;
        panels.barHost.showPanel(panels.pluginPanelItem);
    }
    Loader {
        id: controlCenterLoader
        active: false
        asynchronous: true
        sourceComponent: ControlCenter {
            id: controlCenter
            screenMargins: panels.host.screenGaps
            target: panels.barHost.stripItem
            surfaceColor: panels.host.barBackground()
            foreground: panels.host.fg; background: panels.host.workspaceMenuBg; accent: panels.host.activeBg
            service: panels.barHost.notificationsRef
            wifiControl: panels.barHost.networkServiceRef; bluetoothControl: panels.barHost.bluetoothMenu; displayControl: panels.barHost.brightnessMenu
            // Zone icons are created with their zone, so the WiFi icon can be missing for a moment.
            wifiGlyph: (panels.host.verticalBar ? panels.barHost.verticalWifiIcon : panels.barHost.wifiIcon)?.text ?? ""
            battery: panels.host.battery; mediaPlayer: panels.barHost.mediaStrip.player
            idleEnabled: panels.host.idleLockEnabled; idleBusy: panels.barHost.idleLockProcessRef.running
            barPosition: panels.host.barEdge
            barRef: panels.barHost
            onIdleToggleRequested: if (!panels.barHost.idleLockProcessRef.running) panels.barHost.idleLockProcessRef.running = true
            onLockRequested: runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")])
            onPanelRequested: function(kind) { panelIpc.show(kind); }
            onSettingsRequested: function(page) { panels.host.showSettings(page); }
            onClockRequested: function(page) { panels.host.showClock(page); }
        }
    }

    Loader {
        id: mediaMenuLoader
        active: false
        asynchronous: true
        sourceComponent: MediaMenu {
            id: mediaMenu
            target: panels.host.verticalBar ? panels.barHost.verticalCalendarIcon : panels.barHost.mediaStrip
            barEdge: panels.host.barEdge; surfaceColor: panels.host.barBackground()
            foreground: panels.host.fg; background: panels.host.workspaceMenuBg; accent: panels.host.activeBg
            player: panels.barHost.mediaStrip.player; host: panels.barHost.host
        }
    }

    Loader {
        id: dropDashboardLoader
        active: false
        asynchronous: true
        sourceComponent: DropDashboard {
            id: dropDashboard
            barHost: panels.barHost
            target: panels.host.verticalBar ? panels.barHost.verticalCalendarIcon : panels.barHost.centerInfo
            barEdge: panels.host.barEdge; surfaceColor: panels.host.barBackground()
            foreground: panels.host.fg; background: panels.host.workspaceMenuBg; accent: panels.host.activeBg
            player: panels.barHost.mediaStrip.player
        }
    }

    Loader {
        id: batteryMenuLoader
        active: false
        asynchronous: true
        sourceComponent: BatteryMenu {
            id: batteryMenu
            readonly property string batteryZone: panels.barHost.iconZone("battery") || "right"
            target: panels.barHost.iconTarget("battery", panels.host.verticalBar ? panels.barHost.verticalBatteryIcon : panels.barHost.batteryBarIcon)
            leftAligned: batteryZone === "left"
            centered: batteryZone === "clockStart" || batteryZone === "clockEnd"
            barEdge: panels.host.barEdge; surfaceColor: panels.host.barBackground()
            foreground: panels.host.fg; background: panels.host.workspaceMenuBg; accent: panels.host.activeBg
            battery: panels.host.battery; displayControl: panels.barHost.brightnessMenu
        }
    }

    function showControlCenter(page) {
        // Style, Settings and the profile picture moved to the Settings window; their old names open it there.
        var moved = {style: "appearance", settings: "system", system: "system", picture: "user"};
        if (moved[page]) { panels.host.showSettings(moved[page]); return; }
        ensure("center");
        // "timer" is the Tools page with its Timer & Focus fold open.
        if (page === "timer") panels.controlCenterItem.setFold(panels.controlCenterItem.timerFold, true);
        page = ({capture: "tools", timer: "tools"})[page] || page;
        if (["general", "plugins", "tools"].indexOf(page) === -1) return;
        panels.controlCenterItem.page = page;
        panels.barHost.showPanel(panels.controlCenterItem);
    }
    function toggleControlCenter() { panels.barHost.togglePanel(ensure("center")); }
    function showKind(kind) {
        if (kind === "weather" && !PluginRegistry.weatherEnabled) return;
        if (kind === "picture") { showControlCenter(kind); return; }
        if (kind === "window-info" || kind === "speed-test") {
            ensure("center");
            panels.controlCenterItem.page = "tools";
            panels.controlCenterItem.detail = kind;
            panels.barHost.showPanel(panels.controlCenterItem);
            return;
        }
        ensure(kind);
        var choices = {wifi: panels.barHost.wifiMenu, bluetooth: panels.barHost.bluetoothMenu, brightness: panels.barHost.brightnessMenu, display: panels.barHost.brightnessMenu, volume: panels.barHost.volumeMenu,
            mic: panels.barHost.volumeMenu, streaming: panels.barHost.streamingMenu, keyboard: panels.barHost.keyboardMenu, calendar: panels.barHost.calendarMenu,
            weather: panels.barHost.weatherMenu, hardware: panels.barHost.hardwareMenu, ai: panels.barHost.aiMenu, obs: panels.barHost.obsMenu,
            workspace: panels.barHost.workspaceMenu, recording: panels.barHost.recordingMenu, notifications: panels.notificationCenterItem,
            center: panels.controlCenterItem, media: panels.mediaMenuItem, battery: panels.batteryMenuItem, dashboard: panels.barHost.dropDashboard};
        if (kind === "store" || kind === "catalog") { panels.host.showCatalog(); return; }
        if (kind === "overview") { panels.barHost.toggleOverview(); return; }
        if (!choices[kind]) return;
        if (kind === "mic" || kind === "volume") panels.barHost.volumeMenu.microphone = kind === "mic";
        panels.barHost.showPanel(choices[kind]);
    }
    function inspectPanels() {
        return JSON.stringify(panels.barHost.dockPanels.map(panel => ({name: panel.toString(), visible: panel.visible,
            x: panel.x, y: panel.y, width: panel.width, height: panel.height,
            progress: panel.revealProgress, opened: panel.opened, screen: panels.barHost.modelData.name,
            parent: String(panel.parent), host: String(panel.hostWindow)})));
    }



    // The main barHost receives shortcuts and forwards them to the barHost of the display in use.
    IpcHandler {
        enabled: panels.barHost.isMainBar
        target: "controlCenter"
        function toggle(): void { panels.host.activeBar(barHost).toggleControlCenter(); }
        function show(page: string): void { panels.host.activeBar(barHost).showControlCenter(page); }
    }

    IpcHandler {
        id: panelIpc
        enabled: panels.barHost.isMainBar
        target: "panels"
        function inspect(): string { return panels.host.activeBar(barHost).inspectPanels(); }
        function close(): void { panels.host.activeBar(barHost).closePanels(); }
        function show(kind: string): void { panels.host.activeBar(barHost).showKind(kind); }
        function plugin(plugin: string): bool { return panels.host.activeBar(barHost).clickPlugin(plugin); }
    }

}
