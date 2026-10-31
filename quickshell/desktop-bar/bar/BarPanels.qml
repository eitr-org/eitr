import ".."
import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io

Item {
    id: panels
    required property var host
    required property var barHost
    readonly property alias batteryMenuItem: batteryMenu
    readonly property alias controlCenterItem: controlCenter
    readonly property alias mediaMenuItem: mediaMenu
    readonly property alias notificationCenterItem: notificationCenter
    readonly property alias notificationPopupsItem: notificationPopups
    readonly property alias panelIpcItem: panelIpc
    readonly property alias pluginPanelItem: pluginPanel
    NotificationPopups {
        id: notificationPopups
        screen: barHost.screen
        shown: barHost.isMainBar
        service: barHost.notificationsRef
        foreground: host.fg
        background: host.barBackground()
        accent: host.activeBg
        barEdge: host.barEdge
    }

    NotificationCenter {
        id: notificationCenter
        service: barHost.notificationsRef
        maximumHeight: barHost.screen.height - 70
        target: host.verticalBar ? barHost.verticalNotificationIcon : barHost.notificationIcon
        barEdge: host.barEdge
        surfaceColor: host.barBackground()
        foreground: host.fg
        background: host.workspaceMenuBg
        accent: host.activeBg
    }

    PluginPanel {
        id: pluginPanel
        target: barHost.notificationIcon
        barEdge: host.barEdge; surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
    }
    function openPluginPanel(plugin, panel, target) {
        var entry = PluginRegistry.entries.find(entry => entry.plugin === plugin && entry.id === panel && entry.kind === "panels");
        if (!entry) return;
        pluginPanel.target = target;
        pluginPanel.entry = entry;
        barHost.showPanel(pluginPanel);
    }
    ControlCenter {
        id: controlCenter
        screenMargins: host.screenGaps
        target: barHost.stripItem
        surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
        service: barHost.notificationsRef
        wifiControl: barHost.networkServiceRef; bluetoothControl: barHost.bluetoothMenu; displayControl: barHost.brightnessMenu
        keyboardControl: barHost.keyboardMenu
        wifiGlyph: host.verticalBar ? barHost.verticalWifiIcon.text : barHost.wifiIcon.text
        battery: host.battery; mediaPlayer: barHost.mediaStrip.player
        idleEnabled: host.idleLockEnabled; idleBusy: barHost.idleLockProcessRef.running
        barPosition: host.barEdge; appearance: host.barAppearance; layout: host.barLayout; barScreens: host.barScreens; barAutoHide: host.barAutoHide; barDock: host.barDock; mediaStyle: host.barMediaStyle; clockFormat: host.barClock; workspaceStyle: host.workspaceStyle
        onIdleToggleRequested: if (!barHost.idleLockProcessRef.running) barHost.idleLockProcessRef.running = true
        onLockRequested: runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")])
        onSettingRequested: function(key, value) { host.updateBarSetting(key, value); }
        onWorkspaceStyleRequested: function(value) { host.setWorkspaceStyle(value); }
        onPanelRequested: function(kind) { panelIpc.show(kind); }
        onPickerRequested: function(kind) { runAfterClose(["bash", Quickshell.shellDir + "/scripts/appearance-picker.sh", kind]); }
    }
    MediaMenu {
        id: mediaMenu
        target: host.verticalBar ? barHost.verticalCalendarIcon : barHost.mediaStrip
        barEdge: host.barEdge; surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
        player: barHost.mediaStrip.player
    }
    BatteryMenu {
        id: batteryMenu
        target: host.verticalBar ? barHost.verticalBatteryIcon : barHost.batteryBarIcon
        barEdge: host.barEdge; surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
        battery: host.battery; displayControl: barHost.brightnessMenu
    }
    function showControlCenter(page) {
        // Accept the System and Capture aliases for Settings and Tools.
        page = ({system: "settings", capture: "tools"})[page] || page;
        if (["general", "plugins", "style", "tools", "settings"].indexOf(page) === -1) return;
        controlCenter.page = page;
        barHost.showPanel(controlCenter);
    }
    function toggleControlCenter() { barHost.togglePanel(controlCenter); }
    function showKind(kind) {
        var panels = {wifi: barHost.wifiMenu, bluetooth: barHost.bluetoothMenu, brightness: barHost.brightnessMenu, display: barHost.brightnessMenu, volume: barHost.volumeMenu,
            mic: barHost.volumeMenu, tailscale: barHost.tailscaleMenu, streaming: barHost.streamingMenu, keyboard: barHost.keyboardMenu, calendar: barHost.calendarMenu,
            weather: barHost.weatherMenu, hardware: barHost.hardwareMenu, ai: barHost.aiMenu, obs: barHost.obsMenu,
            workspace: barHost.workspaceMenu, recording: barHost.recordingMenu, notifications: notificationCenter,
            center: controlCenter, media: mediaMenu, battery: batteryMenu};
        if (kind === "overview") { barHost.toggleOverview(); return; }
        if (!panels[kind]) return;
        if (kind === "mic" || kind === "volume") barHost.volumeMenu.microphone = kind === "mic";
        barHost.showPanel(panels[kind]);
    }
    function inspectPanels() {
        return JSON.stringify(barHost.dockPanels.map(panel => ({name: panel.toString(), visible: panel.visible,
            x: panel.x, y: panel.y, width: panel.width, height: panel.height,
            progress: panel.revealProgress, opened: panel.opened, screen: barHost.modelData.name,
            parent: String(panel.parent), host: String(panel.hostWindow)})));
    }



    // The main barHost receives shortcuts and forwards them to the barHost of the display in use.
    IpcHandler {
        enabled: barHost.isMainBar
        target: "controlCenter"
        function toggle(): void { host.activeBar(barHost).toggleControlCenter(); }
        function show(page: string): void { host.activeBar(barHost).showControlCenter(page); }
    }

    IpcHandler {
        id: panelIpc
        enabled: barHost.isMainBar
        target: "panels"
        function inspect(): string { return host.activeBar(barHost).inspectPanels(); }
        function close(): void { host.activeBar(barHost).closePanels(); }
        function show(kind: string): void { host.activeBar(barHost).showKind(kind); }
    }

}
