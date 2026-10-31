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
                    : tabItemStart(leftGroup.hardwareStatus) + leftGroup.hardwareStatus.width) + tabsPadding
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
                    : leftGroup.workspaces.width + itemGap + leftGroup.hardwareStatus.width + itemGap + (mediaStrip.visible ? mediaStrip.width + itemGap : 0) + barPin.width + itemGap + (barCapture.shown ? barCapture.width + itemGap : 0))
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
                    Region { item: bar.wifiMenu.opened ? bar.wifiMenu : null }
                    Region { item: bar.bluetoothMenu.opened ? bar.bluetoothMenu : null }
                    Region { item: bar.brightnessMenu.opened ? bar.brightnessMenu : null }
                    Region { item: bar.volumeMenu.opened ? bar.volumeMenu : null }
                    Region { item: bar.tailscaleMenu.opened ? bar.tailscaleMenu : null }
                    Region { item: bar.streamingMenu.opened ? bar.streamingMenu : null }
                    Region { item: bar.keyboardMenu.opened ? bar.keyboardMenu : null }
                    Region { item: bar.calendarMenu.opened ? bar.calendarMenu : null }
                    Region { item: bar.weatherMenu.opened ? bar.weatherMenu : null }
                    Region { item: hardwareMenu.opened ? hardwareMenu : null }
                    Region { item: aiMenu.opened ? aiMenu : null }
                    Region { item: bar.obsMenu.opened ? bar.obsMenu : null }
                    Region { item: bar.recordingMenu.opened ? bar.recordingMenu : null }
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

                // Centre and status items remain available to the bar geometry and panel frame.
                readonly property alias verticalMiddle: barVerticalCenter.verticalMiddleItem
                readonly property alias verticalMedia: barVerticalCenter.verticalMediaItem
                readonly property alias verticalCapture: barVerticalCenter.verticalCaptureItem
                readonly property alias verticalPin: barVerticalCenter.verticalPinItem
                readonly property alias verticalCalendarIcon: barVerticalCenter.verticalCalendarIconItem
                readonly property alias verticalWeatherIcon: barVerticalCenter.verticalWeatherIconItem
                readonly property alias verticalEnd: barVerticalStatus.verticalEndItem
                readonly property alias verticalWifiIcon: barVerticalStatus.verticalWifiIconItem
                readonly property alias verticalBluetoothIcon: barVerticalStatus.verticalBluetoothIconItem
                readonly property alias verticalDisplayIcon: barVerticalStatus.verticalDisplayIconItem
                readonly property alias verticalVolumeIcon: barVerticalStatus.verticalVolumeIconItem
                readonly property alias verticalTailscaleIcon: barVerticalStatus.verticalTailscaleIconItem
                readonly property alias verticalStreamingIcon: barVerticalStatus.verticalStreamingIconItem
                readonly property alias verticalObsIcon: barVerticalStatus.verticalObsIconItem
                readonly property alias verticalKeyboardIcon: barVerticalStatus.verticalKeyboardIconItem
                readonly property alias verticalUpdatesIcon: barVerticalStatus.verticalUpdatesIconItem
                readonly property alias verticalBatteryIcon: barVerticalStatus.verticalBatteryIconItem
                readonly property alias verticalNotificationIcon: barVerticalStatus.verticalNotificationIconItem
                readonly property alias rightSide: barHorizontalStatus.rightSideItem
                readonly property alias statusToggle: barHorizontalStatus.statusToggleItem
                readonly property alias wifiIcon: barHorizontalStatus.wifiIconItem
                readonly property alias wifiMenu: barHorizontalStatus.wifiMenuItem
                readonly property alias bluetoothIcon: barHorizontalStatus.bluetoothIconItem
                readonly property alias bluetoothMenu: barHorizontalStatus.bluetoothMenuItem
                readonly property alias brightnessIcon: barHorizontalStatus.brightnessIconItem
                readonly property alias brightnessMenu: barHorizontalStatus.brightnessMenuItem
                readonly property alias volumeIcon: barHorizontalStatus.volumeIconItem
                readonly property alias volumeMenu: barHorizontalStatus.volumeMenuItem
                readonly property alias tailscaleIcon: barHorizontalStatus.tailscaleIconItem
                readonly property alias tailscaleMenu: barHorizontalStatus.tailscaleMenuItem
                readonly property alias streamingIcon: barHorizontalStatus.streamingIconItem
                readonly property alias streamingMenu: barHorizontalStatus.streamingMenuItem
                readonly property alias obsIcon: barHorizontalStatus.obsIconItem
                readonly property alias keyboardIcon: barHorizontalStatus.keyboardIconItem
                readonly property alias keyboardMenu: barHorizontalStatus.keyboardMenuItem
                readonly property alias updatesIcon: barHorizontalStatus.updatesIconItem
                readonly property alias batteryBarIcon: barHorizontalStatus.batteryBarIconItem
                readonly property alias obsMenu: barHorizontalStatus.obsMenuItem
                readonly property alias recordingMenu: barHorizontalStatus.recordingMenuItem
                readonly property alias centerInfo: barHorizontalCenter.centerInfoItem
                readonly property alias barCapture: barHorizontalCenter.barCaptureItem
                readonly property alias barPin: barHorizontalCenter.barPinItem
                readonly property alias mediaStrip: barHorizontalCenter.mediaStripItem
                readonly property alias barWeather: barHorizontalCenter.barWeatherItem
                readonly property alias calendarMenu: barHorizontalCenter.calendarMenuItem
                readonly property alias weatherMenu: barHorizontalCenter.weatherMenuItem

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
                    target: shell.verticalBar ? bar.verticalNotificationIcon : notificationIcon
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
                    wifiControl: networkOwner; bluetoothControl: bar.bluetoothMenu; displayControl: bar.brightnessMenu
                    keyboardControl: bar.keyboardMenu
                    wifiGlyph: shell.verticalBar ? bar.verticalWifiIcon.text : bar.wifiIcon.text
                    battery: shell.battery; mediaPlayer: bar.mediaStrip.player
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
                    target: shell.verticalBar ? bar.verticalCalendarIcon : bar.mediaStrip
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    player: bar.mediaStrip.player
                }
                BatteryMenu {
                    id: batteryMenu
                    target: shell.verticalBar ? bar.verticalBatteryIcon : bar.batteryBarIcon
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    battery: shell.battery; displayControl: bar.brightnessMenu
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
                    IslandSurface { first: shell.verticalBar ? verticalControlCenterLogo : leftGroup.controlCenterLogo }
                    IslandSurface { first: shell.verticalBar ? verticalOverviewIcon : leftGroup.overviewIcon; last: shell.verticalBar ? verticalWorkspaces : leftGroup.workspaces }
                    IslandSurface { first: shell.verticalBar ? verticalHardware : leftGroup.hardwareStatus }
                    IslandSurface { first: shell.verticalBar ? bar.verticalCalendarIcon : bar.centerInfo }
                    IslandSurface { first: shell.verticalBar ? bar.verticalWeatherIcon : bar.barWeather }
                    IslandSurface { first: shell.verticalBar ? bar.verticalMedia : bar.mediaStrip; shown: shell.verticalBar ? bar.verticalMedia.visible : bar.mediaStrip.visible }
                    IslandSurface { first: shell.verticalBar ? bar.verticalCapture : bar.barCapture; shown: shell.verticalBar ? bar.verticalCapture.shown : bar.barCapture.shown }
                    IslandSurface { first: shell.verticalBar ? bar.verticalEnd : bar.rightSide; last: shell.verticalBar ? bar.verticalEnd : notificationIcon }
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

                    BarVerticalCenter {
                        id: barVerticalCenter
                        host: shell
                        barHost: bar
                        barWeatherRef: bar.barWeather
                        calendarMenuRef: bar.calendarMenu
                        mediaMenuRef: mediaMenu
                        mediaStripRef: bar.mediaStrip
                        obsMenuRef: bar.obsMenu
                        recordingMenuRef: bar.recordingMenu
                        weatherMenuRef: bar.weatherMenu
                    }

                    BarVerticalStatus {
                        id: barVerticalStatus
                        host: shell
                        barHost: bar
                        batteryMenuRef: batteryMenu
                        bluetoothMenuRef: bar.bluetoothMenu
                        brightnessMenuRef: bar.brightnessMenu
                        keyboardMenuRef: bar.keyboardMenu
                        notificationCenterRef: notificationCenter
                        notificationIconRef: notificationIcon
                        obsMenuRef: bar.obsMenu
                        remoteAccessServiceRef: remoteAccessService
                        streamingMenuRef: bar.streamingMenu
                        tailscaleMenuRef: bar.tailscaleMenu
                        volumeMenuRef: bar.volumeMenu
                        wifiMenuRef: bar.wifiMenu
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

                        BarLeftGroup {
                            id: leftGroup
                            host: shell
                            barWindow: bar
                            styleMenu: workspaceMenu
                            aiPanel: aiMenu
                            hardwarePanel: hardwareMenu
                            Layout.alignment: Qt.AlignVCenter
                        }
                        WorkspaceStyleMenu {
                            id: workspaceMenu
                            surfaceColor: shell.barBackground()
                            target: shell.verticalBar ? verticalWorkspaces : leftGroup.workspaces
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

                        SystemMonitorMenu {
                            id: hardwareMenu
                            surfaceColor: shell.barBackground()
                            maximumHeight: bar.screen.height - 70
                            target: shell.verticalBar ? verticalHardwareIcon : leftGroup.hardwareIcon
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
                            target: shell.verticalBar ? verticalAiIcon : leftGroup.aiIcon
                            barEdge: shell.barEdge
                            accent: shell.activeBg
                            foreground: shell.fg
                            background: shell.workspaceMenuBg
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                    }

                        BarHorizontalStatus {
                            id: barHorizontalStatus
                            host: shell
                            barHost: bar
                            barCaptureRef: bar.barCapture
                            batteryMenuRef: batteryMenu
                            networkOwnerRef: networkOwner
                            notificationIconRef: notificationIcon
                            remoteAccessServiceRef: remoteAccessService
                            verticalBluetoothIconRef: bar.verticalBluetoothIcon
                            verticalCaptureRef: bar.verticalCapture
                            verticalDisplayIconRef: bar.verticalDisplayIcon
                            verticalKeyboardIconRef: bar.verticalKeyboardIcon
                            verticalObsIconRef: bar.verticalObsIcon
                            verticalStreamingIconRef: bar.verticalStreamingIcon
                            verticalTailscaleIconRef: bar.verticalTailscaleIcon
                            verticalVolumeIconRef: bar.verticalVolumeIcon
                            verticalWifiIconRef: bar.verticalWifiIcon
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

                    BarHorizontalCenter {
                        id: barHorizontalCenter
                        host: shell
                        barHost: bar
                        hardwareStatusRef: leftGroup.hardwareStatus
                        mediaMenuRef: mediaMenu
                        obsMenuRef: bar.obsMenu
                        recordingMenuRef: bar.recordingMenu
                        verticalCalendarIconRef: bar.verticalCalendarIcon
                        verticalWeatherIconRef: bar.verticalWeatherIcon
                        workspacesRef: leftGroup.workspaces
                    }
                }

                }

            }

        }

    }

    // OBS recording or streaming, and dictation (SUPER+D): a red dot or the
    // microphone's level bars just before the clock. Hidden, it takes no space.

}
