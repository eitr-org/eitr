import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import Eitr as Eitr
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Services.Pipewire
import Quickshell.Wayland
import "PanelStyle.js" as PanelStyle
import "WorkspaceModel.js" as WorkspaceModel
import "BarGeometry.js" as BarGeometry
import "EdgeSlopes.js" as EdgeSlopes

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

    Connections {
        target: PowerService
        function onBatteryReceived() { shell.checkBatteryLow(); }
    }
    // The user's hooks (distro/lib/run-hook.sh): battery-low once per drop to 15%,
    // post-boot at start (the runner keeps it to once per boot).
    property bool batteryLowHookRan: false
    function runHook(args) {
        var library = Quickshell.env("EITR_LIBRARY_ROOT") || (Eitr.Paths.codeRoot + "/lib");
        Quickshell.execDetached(["bash", library + "/run-hook.sh"].concat(args));
    }
    // The lowest battery warning already given during this discharge (0 = none).
    property int batteryWarned: 0
    function checkBatteryLow() {
        var discharging = shell.battery.available && shell.battery.status === "Discharging";
        var low = discharging && shell.battery.percent <= 15;
        if (low && !batteryLowHookRan) runHook(["battery-low", String(shell.battery.percent)]);
        batteryLowHookRan = low;
        if (!discharging) { batteryWarned = 0; return; }
        var level = shell.battery.percent <= 5 ? 5 : shell.battery.percent <= 10 ? 10 : 0;
        if (level === 0 || (batteryWarned !== 0 && batteryWarned <= level)) return;
        batteryWarned = level;
        Quickshell.execDetached(["notify-send", "--app-name=Battery", "--urgency=" + (level === 5 ? "critical" : "normal"),
            "--icon=battery-caution-symbolic", level === 5 ? "Battery almost empty" : "Battery low",
            shell.battery.percent + "% left. " + (level === 5 ? "Plug in now to avoid losing work." : "Plug in soon.")]);
    }
    Timer { interval: 5000; running: true; onTriggered: shell.runHook(["post-boot"]) }
    // Reminders survive restarts: reschedule them, and show ones that came due while off.
    Timer {
        interval: 6000
        running: true
        onTriggered: Quickshell.execDetached(["python3", Eitr.Paths.codeRoot + "/walker/scripts/actions/tools/reminders.py", "restore"])
    }

    // Checked shortly after login, every six hours, and again after System Update.
    property string updatesToken: DesktopData.observe("updates.status", "shell-updates")
    readonly property var updatesState: DesktopData.topics["updates.status"] || {status: "loading", data: {}}
    readonly property var updates: Object.assign({count: 0, repository: 0, aur: 0, downloadBytes: 0}, updatesState.data,
        {checking: updatesState.status === "loading" || (!!updatesState.inFlight && updatesState.error !== "broker-unavailable")})
    onUpdatesStateChanged: if (updatesState.status === "ready" && !updatesState.inFlight) shell.announceUpdates();
    // A notification goes out only when more updates are pending than were last announced.
    property int announcedUpdates: 0
    readonly property string updatesIcon: updates.checking ? "󰁪" : updates.count > 0 ? "󰚰" : "󰗡"
    readonly property string updatesSize: updates.downloadBytes <= 0 ? ""
        : updates.downloadBytes >= 1073741824 ? (updates.downloadBytes / 1073741824).toFixed(1) + " GB"
        : Math.max(1, Math.round(updates.downloadBytes / 1048576)) + " MB"
    readonly property string updatesTooltip: {
        if (updates.checking) return "Checking for updates";
        if (updatesState.error === "offline") return Eitr.I18n.tr("Offline");
        if (updatesState.status !== "ready") return Eitr.I18n.tr("Updates unavailable · right-click to check again");
        if (updates.count === 0) return "Up to date · right-click to check again";
        return updates.count + (updates.count === 1 ? " update" : " updates") + (updatesSize ? " · " + updatesSize : "");
    }
    function announceUpdates() {
        if (updates.count <= announcedUpdates) {
            announcedUpdates = updates.count;
            return;
        }
        announcedUpdates = updates.count;
        Quickshell.execDetached(["bash", Quickshell.shellDir + "/scripts/updates-notify.sh", String(updates.count), updatesSize]);
    }
    function checkUpdates() { DesktopData.refresh("updates.status"); }
    function openSystemUpdate() {
        var root = Quickshell.env("EITR_CODE_ROOT") || Quickshell.shellDir + "/../..";
        // Floating, with the theme's solid background, like terminals that menus open.
        Quickshell.execDetached([root + "/walker/bin/menu-path/kitty", "-e", "python3", root + "/walker/scripts/actions/task-terminal.py",
            "bash", root + "/walker/scripts/actions/system/update.sh", "system"]);
    }
    IpcHandler {
        target: "updates"
        function refresh(): void { shell.checkUpdates(); }
    }
    // Hold-to-talk dictation (walker/scripts/actions/tools/dictate.sh) turns the
    // recording dot into a live waveform while the microphone listens, then a
    // slow pulse while the speech is transcribed.
    property bool dictating: false
    property bool transcribing: false
    // Microphone levels for the waveform, newest first (drawn at the centre).
    property var dictationLevels: [0, 0, 0, 0]
    IpcHandler {
        target: "dictation"
        function start(): void { shell.transcribing = false; shell.dictating = true; dictationSafety.restart(); }
        function transcribe(): void { shell.dictating = false; shell.transcribing = true; dictationSafety.restart(); }
        function stop(): void { shell.dictating = false; shell.transcribing = false; dictationSafety.stop(); }
    }
    // A lost stop must not leave the dot on.
    Timer { id: dictationSafety; interval: 300000; onTriggered: { shell.dictating = false; shell.transcribing = false; } }
    // The waveform never outlives the recording: while it shows, check every few
    // seconds that a recorder still exists (dictate.sh keeps its pid in these files).
    Timer {
        interval: 3000; repeat: true; running: shell.dictating
        onTriggered: dictationAlive.running = true
    }
    Process {
        id: dictationAlive
        command: ["sh", "-c", "for mode in dictation voice; do f=\"${XDG_RUNTIME_DIR:-/tmp}/eitr-$mode.pid\"; [ -f \"$f\" ] && kill -0 \"$(cat \"$f\")\" 2>/dev/null && exit 0; done; exit 1"]
        onExited: (code) => { if (code !== 0 && shell.dictating) shell.dictating = false; }
    }
    PwNodePeakMonitor {
        id: dictationPeak
        node: Pipewire.defaultAudioSource
        enabled: shell.dictating && node !== null
    }
    Timer {
        interval: 70; repeat: true; running: shell.dictating
        // Speech peaks sit low on a linear scale; the square root lifts them.
        onTriggered: shell.dictationLevels = [Math.min(1, Math.sqrt(dictationPeak.peak) * 1.4)].concat(shell.dictationLevels.slice(0, 3))
    }
    onDictatingChanged: if (!dictating) dictationLevels = [0, 0, 0, 0]

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

    Variants {
        model: FocusMode.enabled ? Quickshell.screens : []
        delegate: Component {
            PanelWindow {
                required property var modelData
                screen: modelData
                anchors { top: true; left: true; right: true }
                implicitHeight: 28; exclusiveZone: 28
                color: "transparent"
                WlrLayershell.namespace: "eitr-focus-strip"
                FocusStrip {
                    anchors.fill: parent
                    tabs: FocusMode.tabs(modelData)
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    clockText: Qt.formatDateTime(focusClock.date, shell.barClock === "24h" ? "HH:mm" : "h:mm AP")
                    networkText: shell.focusNetworkGlyph
                    batteryText: shell.battery.available ? shell.batteryIcon + " " + Math.round(shell.battery.percent) + "%" : ""
                    onSelected: address => FocusMode.activate(address)
                }
            }
        }
    }
    SystemClock { id: focusClock; precision: SystemClock.Minutes }
    readonly property string wifiGlyph: networkOwner.glyph
    readonly property string focusNetworkGlyph: networkOwner.focusGlyph

    Variants {
        model: shell.targetScreens()

        delegate: Component {
            PanelWindow {
                id: bar

                required property var modelData
                readonly property bool isMainBar: modelData === shell.mainScreen()
                readonly property Item stripItem: barContents
                // Vertical bars keep the horizontal depth: the clock stacks and the weather shows only its icon.
                readonly property real normalThickness: shell.barHeight
                readonly property real thinThickness: normalThickness
                // Space between a tab's outermost item and its slope, the same on every tab.
                readonly property real tabsPadding: 4
                function tabItemStart(item) {
                    var start = 0;
                    while (item && item !== barContents) {
                        start += shell.verticalBar ? item.y : item.x;
                        item = item.parent;
                    }
                    return start;
                }
                readonly property real tabLeadingEnd: (shell.verticalBar
                    ? tabItemStart(verticalStart) + verticalStart.height
                    : tabItemStart(hardwareStatus) + hardwareStatus.width) + tabsPadding
                readonly property real tabTrailingStart: tabItemStart(shell.verticalBar ? verticalEnd : rightSide) - tabsPadding
                readonly property real tabCenterStart: (shell.verticalBar
                    ? tabItemStart(verticalMedia.visible ? verticalMedia : verticalCapture.shown ? verticalCapture : verticalCalendarIcon)
                    : tabItemStart(mediaStrip.visible ? mediaStrip : barCapture.shown ? barCapture : centerInfo)) - tabsPadding
                readonly property real tabCenterEnd: (shell.verticalBar
                    ? tabItemStart(verticalCalendarIcon) + verticalCalendarIcon.height + (notchLayout ? weatherReveal : 3 + verticalWeatherIcon.height)
                    : tabItemStart(centerInfo) + centerInfo.width + (notchLayout ? weatherReveal : 6 + barWeather.width)) + tabsPadding
                readonly property var outerGaps: shell.screenGaps
                readonly property bool centeredLayout: shell.centeredLayout
                readonly property bool islandsLayout: shell.islandsLayout
                // Islands float half the outer gap off the screen edge; pills keep the full gap between them.
                readonly property real islandGap: outerGaps[({top: 0, right: 1, bottom: 2, left: 3})[shell.barEdge]] / 2
                readonly property real islandSpacing: islandGap * 2 + 8
                readonly property real reservedThickness: normalThickness + (islandsLayout ? islandGap : 0)
                readonly property bool notchLayout: shell.notchLayout
                readonly property real panelGap: shell.verticalBar ? shell.windowGaps[1] + shell.windowGaps[3] : shell.windowGaps[0] + shell.windowGaps[2]
                property bool hoverExpanded: false
                readonly property bool pointerInside: barHover.hovered || centeredHover.hovered
                onPointerInsideChanged: {
                    if (pointerInside) { collapseDelay.stop(); hoverExpanded = true; }
                    else collapseDelay.restart();
                }
                readonly property bool expanded: !centeredLayout || shell.barPinned || hoverExpanded || panelOpen || pendingPanel !== null || shell.barPointerHeld
                readonly property real itemGap: shell.workspaceItemSpacing
                readonly property real endPadding: shell.verticalBar ? 8 : 12
                readonly property real centerPadding: (centerExtent - (shell.verticalBar ? verticalCalendarIcon.height : centerInfo.width)) / 2
                readonly property real leadingExtent: endPadding - centerPadding + (shell.verticalBar
                    ? verticalStart.height + itemGap + (mediaStrip.player ? verticalMedia.height + itemGap : 0) + verticalPin.height + itemGap + (verticalCapture.shown ? verticalCapture.height + itemGap : 0)
                    : workspaces.width + itemGap + hardwareStatus.width + itemGap + (mediaStrip.visible ? mediaStrip.width + itemGap : 0) + barPin.width + itemGap + (barCapture.shown ? barCapture.width + itemGap : 0))
                readonly property real trailingExtent: endPadding - centerPadding + (shell.verticalBar
                    ? itemGap + verticalWeatherIcon.height + itemGap + verticalEnd.height
                    : itemGap + barWeather.width + itemGap + rightSide.width + itemGap + notificationIcon.width)
                property real leadingReveal: centeredLayout && expanded ? Math.min(leadingExtent, (shell.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : 0
                property real trailingReveal: centeredLayout && expanded ? Math.min(trailingExtent, (shell.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : 0
                Behavior on leadingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
                Behavior on trailingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
                property bool weatherHovered: false
                readonly property bool weatherExpanded: weatherHovered || weatherMenu.visible || pendingPanel === weatherMenu
                readonly property real weatherExtent: shell.verticalBar ? 3 + verticalWeatherIcon.height : 6 + barWeather.width
                property real weatherReveal: notchLayout && weatherExpanded ? weatherExtent : 0
                Behavior on weatherReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
                Timer {
                    id: weatherCollapseDelay
                    interval: collapseDelay.interval
                    onTriggered: bar.weatherHovered = false
                }
                readonly property real centerExtent: shell.verticalBar ? 56 : centerInfo.width + 24
                Timer {
                    id: collapseDelay
                    interval: 350
                    onTriggered: bar.hoverExpanded = false
                }
                readonly property var dockPanels: [wifiMenu, bluetoothMenu, brightnessMenu, volumeMenu, tailscaleMenu, streamingMenu,
                    keyboardMenu, calendarMenu, weatherMenu, hardwareMenu, aiMenu, obsMenu, recordingMenu, workspaceMenu, notificationCenter, controlCenter, mediaMenu, batteryMenu, pluginPanel]
                readonly property bool panelOpen: dockPanels.some(panel => panel.visible)
                readonly property var panelFocusWindows: notificationPopups.visible ? [bar, notificationPopups] : [bar]
                property var pendingPanel: null
                property bool pendingOverview: false

                function closePanels() {
                    pendingPanel = null;
                    pendingOverview = false;
                    overview.opened = false;
                    dockPanels.forEach(panel => panel.opened = false);
                }
                Connections {
                    target: shell
                    function onHandbookOpened() { bar.closePanels(); }
                }
                function showPanel(panel) {
                    pendingOverview = false;
                    overview.opened = false;
                    pendingPanel = panel;
                    dockPanels.forEach(other => other.opened = false);
                    finishPanelSwitch();
                }
                function togglePanel(panel) {
                    if (panel.opened || pendingPanel === panel) closePanels();
                    else showPanel(panel);
                }
                function toggleOverview() {
                    if (overview.opened || pendingOverview) { closePanels(); return; }
                    pendingPanel = null;
                    pendingOverview = true;
                    dockPanels.forEach(panel => panel.opened = false);
                    finishPanelSwitch();
                }
                EdgeDock {
                    screen: bar.screen
                    barEdge: shell.barEdge
                    clients: dockClients.clients
                    dockEnabled: shell.barDock && shell.barVisible && !FocusMode.enabled
                    foreground: shell.fg
                    background: shell.barBackground()
                }
                WorkspaceOverview {
                    id: overview
                    ipcEnabled: bar.isMainBar
                    screen: bar.screen
                    foreground: shell.fg
                    background: shell.bg
                    accent: shell.activeBg
                }
                function finishPanelSwitch() {
                    if (dockPanels.some(panel => panel.visible) || overview.visible) return;
                    if (pendingOverview) {
                        pendingOverview = false;
                        overview.opened = true;
                        return;
                    }
                    if (!pendingPanel) return;
                    var next = pendingPanel;
                    pendingPanel = null;
                    next.opened = true;
                }
                Timer {
                    interval: 16
                    repeat: true
                    running: bar.pendingPanel !== null || bar.pendingOverview
                    onTriggered: bar.finishPanelSwitch()
                }

                screen: modelData
                visible: shell.barVisible || panelOpen
                implicitWidth: modelData.width
                implicitHeight: modelData.height
                color: "transparent"
                exclusionMode: ExclusionMode.Normal
                // Auto-hide reserves no space, so revealing the bar slides it over windows instead of re-tiling them.
                exclusiveZone: !FocusMode.enabled && shell.barVisible && !shell.barAutoHide ? bar.reservedThickness : 0
                WlrLayershell.namespace: "desktop-bar"
                // Notification popups must have a strictly higher layer than
                // panels, rather than depending on same-layer mapping order.
                WlrLayershell.layer: panelOpen && !notificationPopups.visible ? WlrLayer.Overlay : WlrLayer.Top
                mask: dockInput
                WlrLayershell.keyboardFocus: panelOpen ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

                BarAutoHide {
                    id: autoHide
                    autoHide: shell.barAutoHide
                    pointerInside: bar.pointerInside || edgeHover.hovered
                    held: bar.panelOpen || bar.pendingPanel !== null || bar.pendingOverview || overview.visible || shell.barPointerHeld || notificationPopups.visible
                }
                Item {
                    id: edgeSensor
                    width: shell.verticalBar ? 1 : bar.width
                    height: shell.verticalBar ? bar.height : 1
                    x: shell.barEdge === "right" ? bar.width - width : 0
                    y: shell.barEdge === "bottom" ? bar.height - height : 0
                    visible: shell.barAutoHide
                    HoverHandler { id: edgeHover }
                }
                Region {
                    id: dockInput
                    width: 0; height: 0
                    // Focus hides the bar but keeps its window: hiding the window crashes Quickshell.
                    Region { item: edgeSensor.visible && !FocusMode.enabled ? edgeSensor : null }
                    Region { item: shell.barPointerHeld && !FocusMode.enabled ? bar.contentItem : null }
                    Region { item: FocusMode.enabled ? null : shell.notchLayout ? tabStrip : shell.centeredLayout || shell.islandsLayout ? null : barContents }
                    IslandMask { surfaces: islandSurfaces.children }
                    CenteredBarMask { surface: centeredOutline; edge: shell.barEdge; depth: bar.normalThickness; bendRound: shell.tabBendRound }
                    Region { item: shell.notchLayout && !FocusMode.enabled ? leadingTab : null }
                    Region { item: shell.notchLayout && !FocusMode.enabled ? notchTab : null }
                    Region { item: shell.notchLayout && !FocusMode.enabled ? trailingTab : null }
                    Region { item: wifiMenu.opened ? wifiMenu : null }
                    Region { item: bluetoothMenu.opened ? bluetoothMenu : null }
                    Region { item: brightnessMenu.opened ? brightnessMenu : null }
                    Region { item: volumeMenu.opened ? volumeMenu : null }
                    Region { item: tailscaleMenu.opened ? tailscaleMenu : null }
                    Region { item: streamingMenu.opened ? streamingMenu : null }
                    Region { item: keyboardMenu.opened ? keyboardMenu : null }
                    Region { item: calendarMenu.opened ? calendarMenu : null }
                    Region { item: weatherMenu.opened ? weatherMenu : null }
                    Region { item: hardwareMenu.opened ? hardwareMenu : null }
                    Region { item: aiMenu.opened ? aiMenu : null }
                    Region { item: obsMenu.opened ? obsMenu : null }
                    Region { item: recordingMenu.opened ? recordingMenu : null }
                    Region { item: workspaceMenu.opened ? workspaceMenu : null }
                    Region { item: notificationCenter.opened ? notificationCenter : null }
                    Region { item: controlCenter.opened ? controlCenter : null }
                    Region { item: mediaMenu.opened ? mediaMenu : null }
                    Region { item: batteryMenu.opened ? batteryMenu : null }
                    Region { item: pluginPanel.opened ? pluginPanel : null }
                }

                Connections {
                    target: notificationsService
                    function onToggleRequested() {
                        // With a bar on every display, only the one in use opens the center.
                        if (shell.isActiveBar(bar)) bar.togglePanel(notificationCenter);
                    }
                }
                Connections {
                    target: shell
                    function onBarVisibleChanged() {
                        if (!shell.barVisible) bar.closePanels();
                    }
                }

                NotificationPopups {
                    id: notificationPopups
                    screen: bar.screen
                    shown: bar.isMainBar
                    service: notificationsService
                    foreground: shell.fg
                    background: shell.barBackground()
                    accent: shell.activeBg
                    barEdge: shell.barEdge
                }

                NotificationCenter {
                    id: notificationCenter
                    service: notificationsService
                    maximumHeight: bar.screen.height - 70
                    target: shell.verticalBar ? verticalNotificationIcon : notificationIcon
                    barEdge: shell.barEdge
                    surfaceColor: shell.barBackground()
                    foreground: shell.fg
                    background: shell.workspaceMenuBg
                    accent: shell.activeBg
                }

                PluginPanel {
                    id: pluginPanel
                    target: notificationIcon
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                }
                function openPluginPanel(plugin, panel, target) {
                    var entry = PluginRegistry.entries.find(entry => entry.plugin === plugin && entry.id === panel && entry.kind === "panels");
                    if (!entry) return;
                    pluginPanel.target = target;
                    pluginPanel.entry = entry;
                    showPanel(pluginPanel);
                }
                ControlCenter {
                    id: controlCenter
                    screenMargins: shell.screenGaps
                    target: barContents
                    surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    service: notificationsService
                    wifiControl: networkOwner; bluetoothControl: bluetoothMenu; displayControl: brightnessMenu
                    keyboardControl: keyboardMenu
                    wifiGlyph: shell.verticalBar ? verticalWifiIcon.text : wifiIcon.text
                    battery: shell.battery; mediaPlayer: mediaStrip.player
                    idleEnabled: shell.idleLockEnabled; idleBusy: toggleIdleLock.running
                    barPosition: shell.barEdge; appearance: shell.barAppearance; layout: shell.barLayout; barScreens: shell.barScreens; barAutoHide: shell.barAutoHide; barDock: shell.barDock; mediaStyle: shell.barMediaStyle; clockFormat: shell.barClock; workspaceStyle: shell.workspaceStyle
                    onIdleToggleRequested: if (!toggleIdleLock.running) toggleIdleLock.running = true
                    onLockRequested: runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")])
                    onSettingRequested: function(key, value) { shell.updateBarSetting(key, value); }
                    onWorkspaceStyleRequested: function(value) { shell.setWorkspaceStyle(value); }
                    onPanelRequested: function(kind) { panelIpc.show(kind); }
                    onPickerRequested: function(kind) { runAfterClose(["bash", Quickshell.shellDir + "/scripts/appearance-picker.sh", kind]); }
                }
                MediaMenu {
                    id: mediaMenu
                    target: shell.verticalBar ? verticalCalendarIcon : mediaStrip
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    player: mediaStrip.player
                }
                BatteryMenu {
                    id: batteryMenu
                    target: shell.verticalBar ? verticalBatteryIcon : batteryBarIcon
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    battery: shell.battery; displayControl: brightnessMenu
                }
                function showControlCenter(page) {
                    // Accept the System and Capture aliases for Settings and Tools.
                    page = ({system: "settings", capture: "tools"})[page] || page;
                    if (["general", "plugins", "style", "tools", "settings"].indexOf(page) === -1) return;
                    controlCenter.page = page;
                    showPanel(controlCenter);
                }
                function toggleControlCenter() { togglePanel(controlCenter); }
                function showKind(kind) {
                    var panels = {wifi: wifiMenu, bluetooth: bluetoothMenu, brightness: brightnessMenu, display: brightnessMenu, volume: volumeMenu,
                        mic: volumeMenu, tailscale: tailscaleMenu, streaming: streamingMenu, keyboard: keyboardMenu, calendar: calendarMenu,
                        weather: weatherMenu, hardware: hardwareMenu, ai: aiMenu, obs: obsMenu,
                        workspace: workspaceMenu, recording: recordingMenu, notifications: notificationCenter,
                        center: controlCenter, media: mediaMenu, battery: batteryMenu};
                    if (kind === "overview") { toggleOverview(); return; }
                    if (!panels[kind]) return;
                    if (kind === "mic" || kind === "volume") volumeMenu.microphone = kind === "mic";
                    showPanel(panels[kind]);
                }
                function inspectPanels() {
                    return JSON.stringify(dockPanels.map(panel => ({name: panel.toString(), visible: panel.visible,
                        x: panel.x, y: panel.y, width: panel.width, height: panel.height,
                        progress: panel.revealProgress, opened: panel.opened, screen: bar.modelData.name,
                        parent: String(panel.parent), host: String(panel.hostWindow)})));
                }
                Component.onCompleted: shell.registerBar(bar)
                Component.onDestruction: shell.unregisterBar(bar)

                // The main bar receives shortcuts and forwards them to the bar of the display in use.
                IpcHandler {
                    enabled: bar.isMainBar
                    target: "controlCenter"
                    function toggle(): void { shell.activeBar(bar).toggleControlCenter(); }
                    function show(page: string): void { shell.activeBar(bar).showControlCenter(page); }
                }

                IpcHandler {
                    id: panelIpc
                    enabled: bar.isMainBar
                    target: "panels"
                    function inspect(): string { return shell.activeBar(bar).inspectPanels(); }
                    function close(): void { shell.activeBar(bar).closePanels(); }
                    function show(kind: string): void { shell.activeBar(bar).showKind(kind); }
                }

                anchors {
                    top: shell.barEdge === "top" || shell.verticalBar
                    bottom: shell.barEdge === "bottom" || shell.verticalBar
                    left: shell.barEdge === "top" || shell.barEdge === "bottom" || shell.barEdge === "left"
                    right: shell.barEdge === "top" || shell.barEdge === "bottom" || shell.barEdge === "right"
                }

                Shape {
                    id: centeredOutline
                    visible: shell.centeredLayout && !FocusMode.enabled
                    readonly property real slope: bar.normalThickness + shell.tabBendRound
                    x: barContents.x - (shell.verticalBar ? 0 : slope) + (shell.verticalBar ? (shell.barEdge === "left" ? -1 : 1) * bar.normalThickness * (1 - autoHide.progress) : 0)
                    y: barContents.y - (shell.verticalBar ? slope : 0) + (!shell.verticalBar ? (shell.barEdge === "top" ? -1 : 1) * bar.normalThickness * (1 - autoHide.progress) : 0)
                    width: barContents.width + (shell.verticalBar ? 0 : 2 * slope)
                    height: barContents.height + (shell.verticalBar ? 2 * slope : 0)
                    HoverHandler { id: centeredHover }
                    BarGestureArea {
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }
                    antialiasing: true
                    ShapePath {
                        strokeWidth: -1
                        fillColor: shell.barBackground()
                        PathSvg { path: EdgeSlopes.outline(shell.barEdge,
                            shell.verticalBar ? centeredOutline.height : centeredOutline.width,
                            bar.normalThickness, 0, shell.tabBendRound,
                            [[centeredOutline.slope, (shell.verticalBar ? centeredOutline.height : centeredOutline.width) - centeredOutline.slope]]) }
                    }
                }

                Item {
                    id: barContents
                    visible: !FocusMode.enabled
                    transform: Translate {
                        x: shell.verticalBar ? (shell.barEdge === "left" ? -1 : 1) * (bar.normalThickness + (shell.islandsLayout ? bar.islandGap : 0)) * (1 - autoHide.progress) : 0
                        y: !shell.verticalBar ? (shell.barEdge === "top" ? -1 : 1) * (bar.normalThickness + (shell.islandsLayout ? bar.islandGap : 0)) * (1 - autoHide.progress) : 0
                    }
                    width: shell.verticalBar ? bar.thinThickness : (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.width)
                    height: shell.verticalBar ? (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.height) : bar.thinThickness
                    x: shell.verticalBar ? (shell.barEdge === "right" ? bar.width - width - (bar.islandsLayout ? bar.islandGap : 0) : (bar.islandsLayout ? bar.islandGap : 0)) : bar.centeredLayout ? (bar.width - bar.centerExtent) / 2 - bar.leadingReveal : 0
                    y: shell.verticalBar ? (bar.centeredLayout ? (bar.height - bar.centerExtent) / 2 - bar.leadingReveal : 0) : (shell.barEdge === "bottom" ? bar.height - height - (bar.islandsLayout ? bar.islandGap : 0) : (bar.islandsLayout ? bar.islandGap : 0))
                    clip: bar.centeredLayout
                    Item {
                        id: tabStrip
                        visible: shell.notchLayout
                        width: shell.verticalBar ? shell.tabStripThickness : parent.width
                        height: shell.verticalBar ? parent.height : shell.tabStripThickness
                        x: shell.barEdge === "right" ? parent.width - width : 0
                        y: shell.barEdge === "bottom" ? parent.height - height : 0
                    }
                    TabSurface { id: leadingTab; start: 0; end: bar.tabLeadingEnd }
                    TabSurface { id: notchTab; start: bar.tabCenterStart; end: bar.tabCenterEnd }
                    TabSurface { id: trailingTab; start: bar.tabTrailingStart; end: shell.verticalBar ? barContents.height : barContents.width }
                    component TabSurface: Item {
                        property real start
                        property real end
                        readonly property string barEdge: shell.barEdge
                        readonly property real revealProgress: 1
                        readonly property bool detached: false
                        visible: shell.notchLayout
                        width: shell.verticalBar ? bar.normalThickness - shell.tabStripThickness : end - start
                        height: shell.verticalBar ? end - start : bar.normalThickness - shell.tabStripThickness
                        x: shell.verticalBar ? (shell.barEdge === "right" ? 0 : shell.tabStripThickness) : start
                        y: shell.verticalBar ? start : (shell.barEdge === "bottom" ? 0 : shell.tabStripThickness)

                    }
                    Shape {
                        id: tabsOutline
                        anchors.fill: parent
                        visible: shell.notchLayout
                        antialiasing: true
                        // One alpha silhouette also defines Hyprland's blur coverage.
                        ShapePath {
                            strokeWidth: -1
                            fillColor: shell.barBackground()
                            PathSvg { path: {
                                return EdgeSlopes.outline(shell.barEdge,
                                    shell.verticalBar ? tabsOutline.height : tabsOutline.width,
                                    bar.normalThickness, shell.tabStripThickness, shell.tabBendRound,
                                    [[0, bar.tabLeadingEnd], [bar.tabCenterStart, bar.tabCenterEnd], [bar.tabTrailingStart, shell.verticalBar ? tabsOutline.height : tabsOutline.width]]);
                            } }
                        }
                    }
                    HoverHandler {
                        id: barHover
                        // The bar's own handler also sees the pointer over the clock and the weather,
                        // whose mouse areas would hide it from a separate hover box behind them.
                        readonly property bool overCenterTab: {
                            if (!hovered || !bar.notchLayout) return false;
                            var along = shell.verticalBar ? point.position.y : point.position.x;
                            return along >= bar.tabCenterStart && along <= bar.tabCenterEnd;
                        }
                        onOverCenterTabChanged: {
                            if (overCenterTab) { weatherCollapseDelay.stop(); bar.weatherHovered = true; }
                            else weatherCollapseDelay.restart();
                        }
                    }

                PanelWindow {
                    screen: bar.screen
                    visible: shell.dragCandidate !== ""
                    color: "transparent"
                    exclusionMode: ExclusionMode.Ignore
                    WlrLayershell.namespace: "desktop-bar-edge-preview"
                    WlrLayershell.layer: WlrLayer.Overlay
                    mask: Region {}
                    anchors { top: true; bottom: true; left: true; right: true }
                    Rectangle {
                        readonly property bool vertical: shell.dragCandidate === "left" || shell.dragCandidate === "right"
                        x: shell.dragCandidate === "right" ? parent.width - width : 0
                        y: shell.dragCandidate === "bottom" ? parent.height - height : 0
                        width: vertical ? shell.barHeight : parent.width
                        height: vertical ? parent.height : shell.barHeight
                        radius: DesktopStyle.radius(6)
                        color: Qt.alpha(shell.workspaceMenuBg, 0.65)
                        border.width: 1
                        border.color: shell.activeBg
                    }
                }

                Item {
                    id: islandSurfaces
                    visible: !FocusMode.enabled
                    anchors.fill: parent
                    IslandSurface { first: shell.verticalBar ? verticalControlCenterLogo : controlCenterLogo }
                    IslandSurface { first: shell.verticalBar ? verticalOverviewIcon : overviewIcon; last: shell.verticalBar ? verticalWorkspaces : workspaces }
                    IslandSurface { first: shell.verticalBar ? verticalHardware : hardwareStatus }
                    IslandSurface { first: shell.verticalBar ? verticalCalendarIcon : centerInfo }
                    IslandSurface { first: shell.verticalBar ? verticalWeatherIcon : barWeather }
                    IslandSurface { first: shell.verticalBar ? verticalMedia : mediaStrip; shown: shell.verticalBar ? verticalMedia.visible : mediaStrip.visible }
                    IslandSurface { first: shell.verticalBar ? verticalCapture : barCapture; shown: shell.verticalBar ? verticalCapture.shown : barCapture.shown }
                    IslandSurface { first: shell.verticalBar ? verticalEnd : rightSide; last: shell.verticalBar ? verticalEnd : notificationIcon }
                }
                component IslandSurface: Rectangle {
                    required property Item first
                    property Item last: first
                    property bool shown: true
                    visible: bar.islandsLayout && shown
                    readonly property point leading: itemPosition(first)
                    readonly property point trailing: itemPosition(last)
                    function itemPosition(item) {
                        var horizontal = 0;
                        var vertical = 0;
                        while (item && item !== barContents) {
                            horizontal += item.x;
                            vertical += item.y;
                            item = item.parent;
                        }
                        return Qt.point(horizontal, vertical);
                    }
                    x: shell.verticalBar ? 0 : leading.x - 4
                    y: shell.verticalBar ? leading.y - 4 : 0
                    width: shell.verticalBar ? bar.normalThickness : trailing.x + last.width - leading.x + 8
                    height: shell.verticalBar ? trailing.y + last.height - leading.y + 8 : bar.normalThickness
                    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                    color: shell.barBackground()
                    BarGestureArea {
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }
                }

                BarSection {
                    id: verticalSurface
                    anchors.fill: parent
                    visible: shell.verticalBar
                    edge: shell.barEdge
                    background: shell.notchLayout || shell.centeredLayout || shell.islandsLayout ? "transparent" : shell.barBackground()
                    radius: 0

                    BarGestureArea {
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }

                    Column {
                        id: verticalStart
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
                        y: bar.islandsLayout ? shell.screenGaps[0] + 4 : bar.centeredLayout ? bar.endPadding : 8
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: shell.workspaceItemSpacing
                        Column {
                            id: verticalWorkspaces
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: shell.workspaceItemSpacing
                            EitrLogo {
                                id: verticalControlCenterLogo
                                foreground: shell.fg; background: shell.workspaceMenuBg
                                slotWidth: shell.workspaceItemSize
                                anchors.horizontalCenter: parent.horizontalCenter
                                onClicked: bar.toggleControlCenter()
                            }
                            Item { width: 1; height: bar.islandsLayout ? bar.islandSpacing - 2 * shell.workspaceItemSpacing : 0; visible: bar.islandsLayout }
                            VerticalBarIcon { host: shell; id: verticalOverviewIcon; icon: "󰕮"; tooltip: Eitr.I18n.tr("Overview"); open: true; clickable: true; onClicked: bar.toggleOverview() }
                            Repeater {
                                model: shell.workspaceCount
                                BarButton {
                                    host: shell
                                    text: shell.workspaceLabel(index, bar.screen)
                                    tooltip: active ? "" : shell.workspaceApps(index + 1)
                                    visualStyle: shell.workspaceStyle
                                    active: shell.workspaceActive(index + 1, bar.screen)
                                    width: shell.workspaceItemSize; buttonHeight: shell.workspaceItemSize; fontSize: 14; cornerRadius: 6; textOffsetY: 0
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    onClicked: shell.focusWorkspace(index + 1)
                                    onRightClicked: bar.togglePanel(workspaceMenu)
                                }
                            }
                        }
                        Item { width: 1; height: bar.islandsLayout ? bar.islandSpacing - 2 * shell.workspaceItemSpacing : 0; visible: bar.islandsLayout }
                        Column {
                            id: verticalHardware
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: shell.workspaceItemSpacing
                            VerticalBarIcon { host: shell; id: verticalAiIcon; icon: ""; iconSize: 16; tooltip: Eitr.I18n.tr("AI Usage"); open: true; clickable: true; onClicked: bar.togglePanel(aiMenu) }
                            VerticalBarIcon { host: shell; id: verticalHardwareIcon; icon: "󰍛"; iconSize: 18; tooltip: Eitr.I18n.tr("Hardware"); open: true; clickable: true; onClicked: bar.togglePanel(hardwareMenu) }
                            VerticalBarIcon { host: shell; id: verticalIdleLockIcon; icon: shell.idleLockGlyph; iconSize: 17; tooltip: shell.idleLockTooltip; open: true; clickable: true; onClicked: shell.switchIdleLock() }
                        }
                    }

                    Item {
                        id: verticalMiddle
                        anchors.alignWhenCentered: false
                        anchors.horizontalCenterOffset: 0
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: bar.centeredLayout ? (bar.leadingReveal - bar.trailingReveal) / 2 : 0
                        width: parent.width
                        height: 40
                        Column {
                            id: verticalMedia
                            anchors.horizontalCenterOffset: 0
                            anchors.bottom: bar.centeredLayout ? verticalPin.top : verticalCapture.top
                            anchors.bottomMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: bar.centeredLayout ? bar.itemGap : 2
                            visible: mediaStrip.player !== null && bar.expanded
                            MediaIndicator {
                                anchors.horizontalCenter: parent.horizontalCenter
                                rotation: 90
                                style: shell.barMediaStyle
                                playing: mediaStrip.playing
                                active: shell.barVisible && shell.verticalBar && bar.expanded
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                                title: mediaStrip.title
                                onDetailsRequested: bar.togglePanel(mediaMenu)
                            }
                            VerticalBarIcon {
                                host: shell
                                icon: "󰒮"; tooltip: Eitr.I18n.tr("Previous"); open: true
                                clickable: !!mediaStrip.player && mediaStrip.player.canGoPrevious
                                onClicked: mediaStrip.player.previous()
                            }
                            VerticalBarIcon {
                                host: shell
                                icon: mediaStrip.playing ? "󰏤" : "󰐊"; tooltip: mediaStrip.title; open: true
                                clickable: !!mediaStrip.player && mediaStrip.player.canTogglePlaying
                                onClicked: mediaStrip.player.togglePlaying()
                            }
                            VerticalBarIcon {
                                host: shell
                                icon: "󰒭"; tooltip: Eitr.I18n.tr("Next"); open: true
                                clickable: !!mediaStrip.player && mediaStrip.player.canGoNext
                                onClicked: mediaStrip.player.next()
                            }
                            VerticalBarIcon {
                                host: shell
                                icon: "󰝚"; tooltip: Eitr.I18n.tr("Media"); open: true; clickable: true
                                onClicked: bar.togglePanel(mediaMenu)
                            }
                        }
                        CaptureIndicator {
                            host: shell
                            id: verticalCapture
                            anchors.bottom: verticalCalendarIcon.top
                            anchors.horizontalCenterOffset: 0
                            anchors.bottomMargin: shown ? (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3) : 0
                            anchors.horizontalCenter: parent.horizontalCenter
                            height: shown ? 24 : 0
                            recording: obsMenu.obsState.recording || obsMenu.obsState.streaming
                            recordingPaused: obsMenu.obsState.paused && !obsMenu.obsState.streaming
                            streaming: obsMenu.obsState.streaming
                            dictating: shell.dictating
                            transcribing: shell.transcribing
                            dictationLevels: shell.dictationLevels
                            onRecordingClicked: bar.togglePanel(recordingMenu)
                        }
                        VerticalBarIcon {
                            host: shell
                            id: verticalPin
                            anchors.horizontalCenterOffset: 0
                            anchors.bottom: verticalCapture.top
                            anchors.bottomMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3
                            anchors.horizontalCenter: parent.horizontalCenter
                            icon: shell.barPinned ? "󰐃" : "󰐄"
                            tooltip: shell.barPinned ? Eitr.I18n.tr("Unpin bar") : Eitr.I18n.tr("Pin bar open")
                            visible: bar.centeredLayout && bar.expanded
                            open: true; clickable: true
                            onClicked: shell.updateBarSetting("pinned", shell.barPinned ? "no" : "yes")
                        }
                        ClockButton {
                            host: shell
                            id: verticalCalendarIcon
                            anchors.centerIn: parent
                            compact: true
                            onClicked: bar.togglePanel(calendarMenu)
                        }
                        Item {
                            anchors.top: verticalCalendarIcon.bottom
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: parent.width
                            height: bar.notchLayout ? bar.weatherReveal : (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3) + verticalWeatherIcon.height
                            clip: bar.notchLayout
                            WeatherWidget {
                                host: shell
                                id: verticalWeatherIcon
                                visible: bar.expanded
                                enabled: !bar.notchLayout || bar.weatherExpanded
                                y: parent.height - height
                                anchors.horizontalCenter: parent.horizontalCenter
                                autoRefresh: false
                                compact: true
                                text: barWeather.text
                                temp: barWeather.temp
                                onClicked: bar.togglePanel(weatherMenu)
                            }
                        }
                    }

                    Column {
                        id: verticalEnd
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: bar.islandsLayout ? shell.screenGaps[2] + 4 : bar.centeredLayout ? bar.endPadding : 8
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: shell.workspaceItemSpacing
                        VerticalBarIcon {
                            host: shell
                            icon: shell.statusOpen ? "⌄" : "⌃"
                            visible: !bar.centeredLayout && !shell.notchLayout
                            tooltip: shell.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")
                            open: true; clickable: true
                            onClicked: shell.statusOpen = !shell.statusOpen
                        }
                        PluginBarItems {
                            foreground: shell.fg; background: shell.barBackground(); accent: shell.activeBg
                            vertical: true; open: shell.iconsOpen; slotSize: shell.workspaceItemSize; slotSpacing: shell.workspaceItemSpacing
                            onPanelRequested: function(plugin, panel, target) { bar.openPluginPanel(plugin, panel, target); }
                        }
                        StatusCommand {
                            host: shell
                            id: verticalWifiIcon
                            text: shell.wifiGlyph
                            hoverLabel: "WiFi"; fontSize: 16
                            open: shell.iconsOpen; height: open ? 24 : 0; fixedWidth: 56; clickable: true
                            anchors.horizontalCenter: parent.horizontalCenter
                            onClicked: bar.togglePanel(wifiMenu)
                            onOpenChanged: if (!open) wifiMenu.opened = false
                        }
                        VerticalBarIcon { host: shell; id: verticalBluetoothIcon; icon: "󰂯"; tooltip: Eitr.I18n.tr("Bluetooth"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(bluetoothMenu); onOpenChanged: if (!open) bluetoothMenu.opened = false }
                        VerticalBarIcon { host: shell; id: verticalDisplayIcon; icon: "󰍹"; tooltip: Eitr.I18n.tr("Display"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(brightnessMenu); onOpenChanged: if (!open) brightnessMenu.opened = false }
                        VerticalBarIcon { host: shell; id: verticalVolumeIcon; icon: "\u{F02CE}"; tooltip: Eitr.I18n.tr("Audio/Mic"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(volumeMenu); onOpenChanged: if (!open) volumeMenu.opened = false }
                        VerticalBarIcon { host: shell; id: verticalTailscaleIcon; visible: remoteAccessService.allowed; icon: "󰌘"; tooltip: "Tailscale"; open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(tailscaleMenu); onOpenChanged: if (!open) tailscaleMenu.opened = false }
                        VerticalBarIcon { host: shell; id: verticalStreamingIcon; visible: remoteAccessService.allowed; icon: "󰢹"; tooltip: Eitr.I18n.tr("Streaming"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(streamingMenu); onOpenChanged: if (!open) streamingMenu.opened = false }
                        VerticalBarIcon { host: shell; id: verticalObsIcon; icon: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? "󰏤" : "󰑋") : "󰻂"; iconSize: obsMenu.obsState.recording && !obsMenu.obsState.paused ? 22 : 16; tooltip: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? Eitr.I18n.tr("Recording paused") : Eitr.I18n.tr("Recording")) : Eitr.I18n.tr("OBS Studio"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(obsMenu); onOpenChanged: if (!open) obsMenu.opened = false }
                        VerticalBarIcon { host: shell; id: verticalKeyboardIcon; icon: keyboardMenu.activeCode || "󰌌"; iconSize: 11; tooltip: keyboardMenu.activeLabel ? Eitr.I18n.tr("Keyboard · {layout}", {layout: keyboardMenu.activeLabel}) : Eitr.I18n.tr("Keyboard"); open: shell.iconsOpen && keyboardMenu.layouts.length > 1; clickable: true; onClicked: bar.togglePanel(keyboardMenu); onOpenChanged: if (!open) keyboardMenu.opened = false }
                        VerticalBarIcon {
                            host: shell
                            id: verticalUpdatesIcon
                            icon: shell.updatesIcon; iconSize: 17; spinning: shell.updates.checking
                            tooltip: shell.updatesTooltip; open: shell.iconsOpen
                            clickable: true; rightClickable: true
                            onClicked: function(button) { if (button === Qt.RightButton) shell.checkUpdates(); else shell.openSystemUpdate(); }
                        }
                        VerticalBarIcon { host: shell; id: verticalBatteryIcon; icon: shell.batteryIcon; tooltip: Math.round(shell.battery.percent) + "% · " + shell.battery.status; open: shell.battery.available; visible: shell.battery.available; clickable: true; onClicked: bar.togglePanel(batteryMenu) }
                        VerticalBarIcon {
                            host: shell
                            id: verticalNotificationIcon
                            icon: notificationIcon.text; tooltip: Eitr.I18n.tr("Notifications"); open: true; clickable: true
                            onClicked: bar.togglePanel(notificationCenter)
                        }
                    }
                }

                BarSection {
                    id: surface
                    anchors.fill: parent
                    visible: !shell.verticalBar
                    edge: shell.barEdge
                    background: shell.notchLayout || shell.centeredLayout || shell.islandsLayout ? "transparent" : shell.barBackground()
                    radius: 0

                    BarGestureArea {
                        id: barGestures
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: bar.islandsLayout ? shell.screenGaps[3] + 4 : bar.centeredLayout ? bar.endPadding : 12
                        anchors.rightMargin: 9
                        spacing: 0

                        Row {
                            id: workspaces
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded
                            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }

                            spacing: shell.workspaceItemSpacing
                            Layout.alignment: Qt.AlignVCenter

                            EitrLogo {
                                id: controlCenterLogo
                                foreground: shell.fg; background: shell.workspaceMenuBg
                                slotWidth: shell.workspaceItemSize
                                anchors.verticalCenter: parent.verticalCenter
                                onClicked: bar.toggleControlCenter()
                            }
                            Item { width: bar.islandsLayout ? bar.islandSpacing - 2 * shell.workspaceItemSpacing : 0; height: 1; visible: bar.islandsLayout }
                            StatusIcon {
                                host: shell
                                id: overviewIcon
                                icon: "󰕮"; tooltip: Eitr.I18n.tr("Overview"); open: true; clickable: true
                                slotWidth: shell.workspaceItemSize
                                anchors.verticalCenter: parent.verticalCenter
                                onClicked: bar.toggleOverview()
                            }
                            Repeater {
                                model: shell.workspaceCount

                                BarButton {

                                    host: shell
                                    text: shell.workspaceLabel(index, bar.screen)
                                    tooltip: active ? "" : shell.workspaceApps(index + 1)
                                    visualStyle: shell.workspaceStyle
                                    active: shell.workspaceActive(index + 1, bar.screen)
                                    width: shell.workspaceItemSize
                                    buttonHeight: shell.workspaceItemSize
                                    anchors.verticalCenter: parent.verticalCenter
                                    fontSize: 14
                                    cornerRadius: 6
                                    textOffsetY: 0
                                    onClicked: shell.focusWorkspace(index + 1)
                                    onRightClicked: bar.togglePanel(workspaceMenu)
                                }

                            }

                            WorkspaceStyleMenu {
                                id: workspaceMenu
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalWorkspaces : workspaces
                                barEdge: shell.barEdge
                                currentStyle: shell.workspaceStyle
                                accent: shell.activeBg
                                foreground: shell.workspaceMenuFg
                                background: shell.workspaceMenuBg
                                selectedForeground: shell.activeFg
                                onSelected: function(style) {
                                    shell.setWorkspaceStyle(style);
                                }
                            }

                        }

                        Row {
                            id: hardwareStatus
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded
                            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
                            Layout.alignment: Qt.AlignVCenter
                            Layout.leftMargin: bar.islandsLayout ? bar.islandSpacing : shell.workspaceItemSpacing
                            spacing: shell.workspaceItemSpacing

                            StatusIcon {

                                host: shell
                                id: aiIcon
                                slotWidth: shell.workspaceItemSize
                                icon: ""
                                iconSize: 16
                                tooltip: Eitr.I18n.tr("AI Usage")
                                open: true
                                clickable: true
                                onClicked: bar.togglePanel(aiMenu)
                            }

                            StatusIcon {

                                host: shell
                                id: hardwareIcon
                                slotWidth: shell.workspaceItemSize
                                icon: "󰍛"
                                iconSize: 18
                                tooltip: Eitr.I18n.tr("Hardware")
                                open: true
                                clickable: true
                                onClicked: bar.togglePanel(hardwareMenu)
                            }

                            // A plain switch: a click turns automatic idle locking on or off.
                            StatusIcon {
                                host: shell
                                id: idleLockIcon
                                slotWidth: shell.workspaceItemSize
                                icon: shell.idleLockGlyph
                                iconSize: 17
                                tooltip: shell.idleLockTooltip
                                open: true
                                clickable: true
                                onClicked: shell.switchIdleLock()
                            }
                        }

                        SystemMonitorMenu {
                            id: hardwareMenu
                            surfaceColor: shell.barBackground()
                            maximumHeight: bar.screen.height - 70
                            target: shell.verticalBar ? verticalHardwareIcon : hardwareIcon
                            barEdge: shell.barEdge
                            accent: shell.activeBg
                            foreground: shell.fg
                            background: shell.workspaceMenuBg
                        }

                        AiUsageMenu {
                            id: aiMenu
                            surfaceColor: shell.barBackground()
                            maximumHeight: bar.screen.height - 70
                            leftAligned: true
                            target: shell.verticalBar ? verticalAiIcon : aiIcon
                            barEdge: shell.barEdge
                            accent: shell.activeBg
                            foreground: shell.fg
                            background: shell.workspaceMenuBg
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                    }

                        Row {
                            id: rightSide
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded
                            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }

                            spacing: shell.workspaceItemSpacing
                            anchors.right: notificationIcon.left
                            anchors.rightMargin: shell.workspaceItemSpacing
                            anchors.verticalCenter: parent.verticalCenter

                            StatusIcon {

                                host: shell
                                id: statusToggle
                                visible: !bar.centeredLayout && !shell.notchLayout
                                tooltip: shell.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")

                                icon: shell.statusOpen ? "›" : "‹"
                                open: true
                                clickable: true
                                iconSize: 21
                                glyphOffsetY: -1
                                onClicked: shell.statusOpen = !shell.statusOpen
                            }

                            PluginBarItems {
                                foreground: shell.fg; background: shell.barBackground(); accent: shell.activeBg
                                open: shell.iconsOpen; slotSize: shell.workspaceItemSize; slotSpacing: shell.workspaceItemSpacing
                                onPanelRequested: function(plugin, panel, target) { bar.openPluginPanel(plugin, panel, target); }
                            }

                            StatusCommand {

                                host: shell
                                id: wifiIcon
                                text: shell.wifiGlyph
                                hoverLabel: "WiFi"
                                fontSize: 16
                                open: shell.iconsOpen
                                slotWidth: shell.workspaceItemSize
                                fixedWidth: shell.workspaceItemSize
                                clickable: true
                                onClicked: bar.togglePanel(wifiMenu)
                                onOpenChanged: if (!open) wifiMenu.opened = false
                            }

                            WifiMenu {
                                id: wifiMenu
                                networkService: networkOwner
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalWifiIcon : (shell.iconsOpen ? wifiIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {

                                host: shell
                                id: bluetoothIcon
                                icon: "󰂯"
                                tooltip: Eitr.I18n.tr("Bluetooth")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(bluetoothMenu)
                                onOpenChanged: if (!open) bluetoothMenu.opened = false
                            }

                            BluetoothMenu {
                                id: bluetoothMenu
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalBluetoothIcon : (shell.iconsOpen ? bluetoothIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {

                                host: shell
                                id: brightnessIcon
                                icon: "󰍹"
                                tooltip: Eitr.I18n.tr("Display")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(brightnessMenu)
                                onOpenChanged: if (!open) brightnessMenu.opened = false
                            }

                            BrightnessMenu {
                                id: brightnessMenu
                                maximumHeight: bar.screen.height - 70
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalDisplayIcon : (shell.iconsOpen ? brightnessIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                                onPrimarySelected: DisplayService.refresh()
                            }

                            StatusIcon {

                                host: shell
                                id: volumeIcon
                                icon: "\u{F02CE}"
                                tooltip: Eitr.I18n.tr("Audio/Mic")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(volumeMenu)
                                onOpenChanged: if (!open) volumeMenu.opened = false
                            }

                            AudioMenu {
                                id: volumeMenu
                                surfaceColor: shell.barBackground()
                                maximumHeight: bar.screen.height - 70
                                target: shell.verticalBar ? verticalVolumeIcon : (shell.iconsOpen ? volumeIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {

                                host: shell
                                id: tailscaleIcon
                                visible: remoteAccessService.allowed
                                icon: "󰌘"
                                tooltip: "Tailscale"
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(tailscaleMenu)
                                onOpenChanged: if (!open) tailscaleMenu.opened = false
                            }
                            RemoteAccessMenu {
                                id: tailscaleMenu
                                kind: "tailscale"
                                service: remoteAccessService
                                onObservationChanged: observing => shell.remoteObservers += observing ? 1 : -1
                                maximumHeight: bar.screen.height - 70
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalTailscaleIcon : tailscaleIcon
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }
                            StatusIcon {
                                host: shell
                                id: streamingIcon
                                visible: remoteAccessService.allowed
                                icon: "󰢹"
                                tooltip: Eitr.I18n.tr("Streaming")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(streamingMenu)
                                onOpenChanged: if (!open) streamingMenu.opened = false
                            }
                            RemoteAccessMenu {
                                id: streamingMenu
                                kind: "streaming"
                                service: remoteAccessService
                                onObservationChanged: observing => shell.remoteObservers += observing ? 1 : -1
                                maximumHeight: bar.screen.height - 70
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalStreamingIcon : streamingIcon
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {

                                host: shell
                                id: obsIcon
                                icon: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? "󰏤" : "󰑋") : "󰻂"
                                iconSize: obsMenu.obsState.recording && !obsMenu.obsState.paused ? 22 : 16
                                tooltip: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? Eitr.I18n.tr("Recording paused") : Eitr.I18n.tr("Recording")) : Eitr.I18n.tr("OBS Studio")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(obsMenu)
                                onOpenChanged: if (!open) obsMenu.opened = false
                            }

                            StatusIcon {

                                host: shell
                                id: keyboardIcon
                                // Like macOS's input menu: the active layout's code, shown
                                // only when there is more than one layout to switch between.
                                icon: keyboardMenu.activeCode || "󰌌"
                                iconSize: 11
                                tooltip: keyboardMenu.activeLabel ? Eitr.I18n.tr("Keyboard · {layout}", {layout: keyboardMenu.activeLabel}) : Eitr.I18n.tr("Keyboard")
                                open: shell.iconsOpen && keyboardMenu.layouts.length > 1
                                clickable: true
                                onClicked: bar.togglePanel(keyboardMenu)
                                onOpenChanged: if (!open) keyboardMenu.opened = false
                            }

                            KeyboardLayoutMenu {
                                id: keyboardMenu
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalKeyboardIcon : (shell.iconsOpen ? keyboardIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {

                                host: shell
                                id: updatesIcon
                                icon: shell.updatesIcon
                                iconSize: 17
                                spinning: shell.updates.checking
                                tooltip: shell.updatesTooltip
                                open: shell.iconsOpen
                                clickable: true
                                rightClickable: true
                                onClicked: function(button) {
                                    if (button === Qt.RightButton) shell.checkUpdates();
                                    else shell.openSystemUpdate();
                                }
                            }

                            StatusIcon {

                                host: shell
                                id: batteryBarIcon
                                icon: shell.batteryIcon
                                tooltip: Math.round(shell.battery.percent) + "% · " + shell.battery.status
                                open: shell.battery.available; visible: shell.battery.available
                                clickable: true; onClicked: bar.togglePanel(batteryMenu)
                            }

                            ObsMenu {
                                id: obsMenu
                                surfaceColor: shell.barBackground()
                                onCaptureStarting: recordingMenu.opened = false
                                target: shell.verticalBar ? verticalObsIcon : obsIcon
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            RecordingMenu {
                                id: recordingMenu
                                surfaceColor: shell.barBackground()
                                controller: obsMenu
                                target: shell.verticalBar ? verticalCapture : barCapture
                                barEdge: shell.barEdge
                                centered: true
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                        }

                    NotificationWidget {

                        host: shell

                        notificationService: notificationsService
                        id: notificationIcon
                        onOpenRequested: bar.togglePanel(notificationCenter)
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        visible: !shell.verticalBar
                        anchors.right: parent.right
                        anchors.rightMargin: bar.islandsLayout ? shell.screenGaps[1] + 4 : bar.centeredLayout ? bar.endPadding : 13
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    ClockButton {

                        host: shell
                        id: centerInfo
                        anchors.alignWhenCentered: false
                        anchors.centerIn: parent
                        anchors.horizontalCenterOffset: bar.centeredLayout ? (bar.leadingReveal - bar.trailingReveal) / 2 : 0
                        anchors.verticalCenterOffset: 0
                        onClicked: bar.togglePanel(calendarMenu)
                    }

                    CaptureIndicator {

                        host: shell
                        id: barCapture
                        anchors.right: centerInfo.left
                        anchors.rightMargin: shown ? (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 6) : 0
                        anchors.verticalCenter: parent.verticalCenter
                        recording: obsMenu.obsState.recording || obsMenu.obsState.streaming
                        recordingPaused: obsMenu.obsState.paused && !obsMenu.obsState.streaming
                        streaming: obsMenu.obsState.streaming
                        dictating: shell.dictating
                        transcribing: shell.transcribing
                        dictationLevels: shell.dictationLevels
                        onRecordingClicked: bar.togglePanel(recordingMenu)
                    }

                    StatusIcon {

                        host: shell
                        id: barPin
                        visible: bar.centeredLayout && bar.expanded
                        anchors.right: barCapture.left
                        anchors.rightMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 6
                        anchors.verticalCenter: parent.verticalCenter
                        icon: shell.barPinned ? "󰐃" : "󰐄"
                        tooltip: shell.barPinned ? Eitr.I18n.tr("Unpin bar") : Eitr.I18n.tr("Pin bar open")
                        open: true; clickable: true
                        onClicked: shell.updateBarSetting("pinned", shell.barPinned ? "no" : "yes")
                    }

                    MediaStrip {
                        id: mediaStrip
                        mediaStyle: shell.barMediaStyle
                        audioEnabled: shell.barVisible && !shell.verticalBar && bar.expanded
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        anchors.right: bar.centeredLayout ? barPin.left : barCapture.left
                        anchors.rightMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 12
                        anchors.verticalCenter: parent.verticalCenter
                        itemSpacing: bar.centeredLayout ? bar.itemGap : 1
                        indicatorSpacing: bar.centeredLayout ? bar.itemGap : 6
                        availableWidth: bar.centeredLayout
                            ? Math.max(0, bar.width / 2 - centerInfo.width / 2 - workspaces.width - hardwareStatus.width - barPin.width - barCapture.width - bar.itemGap * (barCapture.shown ? 5 : 4) - bar.endPadding)
                            : Math.max(0, centerInfo.x - hardwareStatus.mapToItem(centerInfo.parent, hardwareStatus.width, 0).x - (bar.islandsLayout ? 2 * bar.islandSpacing + (barCapture.shown ? barCapture.width + bar.islandSpacing : 0) : 24))
                        foreground: shell.fg
                        background: shell.workspaceMenuBg
                        onDetailsRequested: bar.togglePanel(mediaMenu)
                    }

                    Item {
                        anchors.left: centerInfo.right
                        anchors.verticalCenter: centerInfo.verticalCenter
                        width: bar.notchLayout ? bar.weatherReveal : (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 6) + barWeather.width
                        height: barWeather.height
                        clip: bar.notchLayout
                        WeatherWidget {
                            host: shell
                            id: barWeather
                            x: parent.width - width
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded && (!bar.notchLayout || bar.weatherExpanded)
                            onClicked: bar.togglePanel(weatherMenu)
                        }
                    }

                    CalendarMenu {
                        id: calendarMenu
                        surfaceColor: shell.barBackground()
                        target: shell.verticalBar ? verticalCalendarIcon : centerInfo
                        barEdge: shell.barEdge
                        centered: true
                        accent: shell.activeBg
                        foreground: shell.fg
                        background: shell.workspaceMenuBg
                    }

                    WeatherMenu {
                        id: weatherMenu
                        surfaceColor: shell.barBackground()
                        target: shell.verticalBar ? verticalWeatherIcon : centerInfo
                        barEdge: shell.barEdge
                        centered: true
                        accent: shell.activeBg
                        foreground: shell.fg
                        background: shell.workspaceMenuBg
                    }

                }

                }

            }

        }

    }

    // OBS recording or streaming, and dictation (SUPER+D): a red dot or the
    // microphone's level bars just before the clock. Hidden, it takes no space.

}
