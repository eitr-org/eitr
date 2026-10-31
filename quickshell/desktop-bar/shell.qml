import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import "WorkspaceModel.js" as WorkspaceModel

ShellRoot {
    Component.onCompleted: {
        Quickshell.watchFiles = Quickshell.env("EITR_LIVE_RELOAD") === "1";
        PluginRegistry.startDiagnostics();
    }
    id: shell
    signal handbookOpened()
    NetworkService { id: networkOwner }
    NotificationService { id: notificationsService }
    RemoteAccessService { id: remoteAccessService; observing: shell.remotePanelsOpen }
    WelcomeSession { host: shell }
    LiveWallpaper {}
    PluginDesktop {
        id: pluginDesktop
        foreground: shell.fg; background: shell.barBackground(); accent: shell.activeBg
        grid: shell.windowGaps[0]
    }
    RealmEffects {
        accent: shell.activeBg
        defaultScreen: shell.targetScreens()[0] || null
    }
    ReloadErrorPopup {
        foreground: shell.fg
        background: shell.barBackground()
        targetScreen: shell.targetScreens()[0] || null
        barEdge: shell.barEdge
    }

    property int remoteObservers: 0
    readonly property bool remotePanelsOpen: remoteObservers > 0
    property bool statusOpen: false
    property bool barVisible: true
    property int barHeight: 30
    property color bg: Qt.rgba(24 / 255, 24 / 255, 36 / 255, 0.38)
    property color fg: "#cdd6f4"
    property color activeFg: "#11111b"
    property color activeBg: "#cdd6f4"
    property color hoverBg: Qt.rgba(180 / 255, 190 / 255, 254 / 255, 0.15)
    property bool idleLockEnabled: false
    readonly property string idleLockGlyph: idleLockEnabled ? "󱫗" : "󱫖"
    readonly property string idleLockTooltip: idleLockEnabled ? Eitr.I18n.tr("Idle Lock: On") : Eitr.I18n.tr("Idle Lock: Off")
    function switchIdleLock() { if (!toggleIdleLock.running) toggleIdleLock.running = true; }
    property var battery: PowerService.battery
    readonly property string batteryIcon: battery.status === "Charging" ? "󰂄" : battery.percent < 20 ? "󰁻" : battery.percent < 60 ? "󰁾" : "󰁹"
    property string primaryDisplay: DisplayService.topology.primary
    property var preferredOutputs: DisplayService.topology.preferred
    property string workspaceStyle: "Runes"
    readonly property int workspaceCount: WorkspaceModel.ceiling(WorkspaceModel.occupied(Hyprland.toplevels.values),
        Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : 0)
    readonly property int workspaceItemSize: 24
    readonly property int workspaceItemSpacing: 4
    property color workspaceMenuBg: "#181824"
    property color workspaceMenuFg: "#cdd6f4"
    property string barAppearance: "solid"
    property string barLayout: "unified"
    property bool barPinned: false
    property bool barAutoHide: false
    property bool barDock: true
    DockClients { id: dockClients; observing: shell.barDock && !FocusMode.enabled }
    property string barMediaStyle: "bars"
    property string barClock: "12h"
    // "all" puts a bar on every display; the main one keeps notifications.
    property string barScreens: "main"
    property var windowGaps: DisplayService.topology.windowGaps
    property var screenGaps: DisplayService.topology.screenGaps
    readonly property bool islandsLayout: barLayout === "islands"
    readonly property bool notchLayout: barLayout === "notch"
    readonly property real tabStripThickness: 7
    // Radius of the four bends on each Tabs slope.
    readonly property real tabBendRound: 6
    readonly property bool centeredLayout: barLayout === "centered"
    readonly property bool iconsOpen: centeredLayout || notchLayout || statusOpen
    property string barEdge: "top"
    property bool settingsDirty: false
    property string dragCandidate: ""
    property bool barPointerHeld: false
    readonly property bool verticalBar: barEdge === "left" || barEdge === "right"
    readonly property var desktopApplications: DesktopEntries.applications.values

    function barBackground() {
        return barAppearance === "solid" ? workspaceMenuBg : bg;
    }

    function barDoubleClick(button) {
        if (button === Qt.LeftButton) updateBarSetting("appearance", barAppearance === "solid" ? "transparent" : "solid");
        else if (button === Qt.RightButton) updateBarSetting("layout", barLayout === "unified" ? "centered" : barLayout === "centered" ? "notch" : barLayout === "notch" ? "islands" : "unified");
    }

    BarPreferences { id: preferences; host: shell }
    function updateBarSetting(key, value) { preferences.updateBarSetting(key, value); }
    function persistBarSettings() { preferences.persistBarSettings(); }
    function setWorkspaceStyle(style) { preferences.setWorkspaceStyle(style); }

    Process {
        id: idleLockStatus
        command: ["pgrep", "-x", "hypridle"]
        running: true
        onExited: function(code) { shell.idleLockEnabled = code === 0; }
    }

    Timer {
        interval: 30000
        running: true
        repeat: true
        onTriggered: if (!idleLockStatus.running && !toggleIdleLock.running) idleLockStatus.running = true
    }

    Process {
        id: toggleIdleLock
        command: ["bash", Eitr.Paths.code("walker/scripts/actions/toggle/idle-lock.sh")]
        onExited: if (!idleLockStatus.running) idleLockStatus.running = true
    }

    SessionHooks { id: sessionHooks; host: shell }
    function runHook(args) { sessionHooks.runHook(args); }

    UpdatesStatus { id: updatesStatus }
    readonly property alias updates: updatesStatus.updates
    readonly property alias updatesIcon: updatesStatus.updatesIcon
    readonly property alias updatesTooltip: updatesStatus.updatesTooltip
    function checkUpdates() { updatesStatus.checkUpdates(); }
    function openSystemUpdate() { updatesStatus.openSystemUpdate(); }
    // Hold-to-talk dictation state (DictationState.qml) drives the recording dot.
    DictationState { id: dictation }
    readonly property alias dictating: dictation.dictating
    readonly property alias transcribing: dictation.transcribing
    readonly property alias dictationLevels: dictation.dictationLevels

    TimePicker { defaultScreen: shell.targetScreens()[0] || null; foreground: shell.fg; background: shell.barBackground() }
    AppearancePicker { defaultScreen: shell.targetScreens()[0] || null }

    function focusWorkspace(id) {
        var command = WorkspaceModel.focusCommand(id);
        if (command.length) Quickshell.execDetached(command);
    }

    // With a bar on every display, each bar marks the workspace shown on its own display.
    function workspaceActive(index, screen) {
        if (barScreens === "all" && screen) {
            var monitor = Hyprland.monitorFor(screen);
            return !!(monitor && monitor.activeWorkspace && monitor.activeWorkspace.id === index);
        }
        return Hyprland.focusedWorkspace && Hyprland.focusedWorkspace.id === index;
    }

    function workspaceLabel(index, screen) {
        if (workspaceStyle === "Glyph") return workspaceActive(index + 1, screen) ? "✦" : "✧";
        return String(index + 1);
    }

    function workspaceApps(workspaceId) {
        var names = [];
        for (var window of Hyprland.toplevels.values) {
            if (!window.workspace || window.workspace.id !== workspaceId) continue;
            var info = window.lastIpcObject;
            if (info.mapped === false) continue;
            var appId = (window.wayland && window.wayland.appId) || info.class || info.initialClass || "";
            var entry = desktopApplications.find(app => app.id === appId || app.startupClass === appId)
                || DesktopEntries.heuristicLookup(appId);
            var name = entry ? entry.name : appId;
            if (name && names.indexOf(name) === -1) names.push(name);
        }
        return names.join("\n");
    }

    // display-primary.py owns the choice and reports it as primaryDisplay.
    // This fallback mirrors its choose_primary() order (saved/reported name,
    // first connected machine-local preferred output, else the largest screen)
    // so startup and unmatched names pick the same screen without a bar jump.
    function mainScreen() {
        var screens = Quickshell.screens || [];
        var byName = {};
        var largest = null;
        for (var i = 0; i < screens.length; i++) {
            if (!screens[i])
                continue;
            byName[screens[i].name] = screens[i];
            if (!largest || screens[i].width * screens[i].height > largest.width * largest.height)
                largest = screens[i];
        }
        if (primaryDisplay && byName[primaryDisplay])
            return byName[primaryDisplay];
        for (var j = 0; j < preferredOutputs.length; j++) {
            if (byName[preferredOutputs[j]])
                return byName[preferredOutputs[j]];
        }
        return largest;
    }

    // Bars by screen name, so shortcuts reach the bar of the display in use.
    property var barsByScreen: ({})
    function registerBar(bar) {
        var bars = Object.assign({}, barsByScreen);
        bars[bar.modelData.name] = bar;
        barsByScreen = bars;
    }
    function unregisterBar(bar) {
        var bars = Object.assign({}, barsByScreen);
        if (bars[bar.modelData.name] === bar) delete bars[bar.modelData.name];
        barsByScreen = bars;
    }
    function activeBar(fallback) {
        var focused = Hyprland.focusedMonitor;
        return (focused && barsByScreen[focused.name]) || fallback;
    }
    function isActiveBar(bar) {
        var active = activeBar(null);
        return active ? active === bar : bar.isMainBar;
    }

    // The main display first, then, when the bar is shown on every display, the others.
    function targetScreens() {
        var main = mainScreen();
        if (!main)
            return [];
        if (barScreens !== "all")
            return [main];
        return [main].concat((Quickshell.screens || []).filter(screen => screen && screen !== main));
    }

    FocusStrips { host: shell }
    readonly property string wifiGlyph: networkOwner.glyph
    readonly property string focusNetworkGlyph: networkOwner.focusGlyph

    Variants {
        model: shell.targetScreens()

        delegate: Component {
            BarWindow {
                host: shell
                networkServiceRef: networkOwner
                notificationsRef: notificationsService
                remoteServiceRef: remoteAccessService
                dockClientsRef: dockClients
                idleLockProcessRef: toggleIdleLock
            }
        }
    }
}
