import ".."
import QtQuick
import QtQuick.Shapes
import Eitr as Eitr
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "../PanelStyle.js" as PanelStyle
import "../EdgeSlopes.js" as EdgeSlopes

PanelWindow {
    id: bar

    required property var host
    required property var networkServiceRef
    required property var notificationsRef
    required property var remoteServiceRef
    required property var dockClientsRef
    required property var idleLockProcessRef

    required property var modelData
    readonly property bool isMainBar: modelData === host.mainScreen()
    readonly property Item stripItem: barContents
    // Vertical bars keep the horizontal depth: the clock stacks and the weather shows only its icon.
    readonly property real normalThickness: host.barHeight
    readonly property real thinThickness: normalThickness
    // Space between a tab's outermost item and its slope, the same on every tab.
    readonly property real tabsPadding: 4
    function tabItemStart(item) {
        var start = 0;
        while (item && item !== barContents) {
            start += host.verticalBar ? item.y : item.x;
            item = item.parent;
        }
        return start;
    }
    readonly property real tabLeadingEnd: (host.verticalBar
        ? tabItemStart(verticalStart) + verticalStart.height
        : tabItemStart(leftGroup.hardwareStatus) + leftGroup.hardwareStatus.width) + tabsPadding
    readonly property real tabTrailingStart: tabItemStart(host.verticalBar ? verticalEnd : rightSide) - tabsPadding
    readonly property real tabCenterStart: (host.verticalBar
        ? tabItemStart(verticalMedia.visible ? verticalMedia : verticalCapture.shown ? verticalCapture : verticalCalendarIcon)
        : tabItemStart(mediaStrip.visible ? mediaStrip : barCapture.shown ? barCapture : centerInfo)) - tabsPadding
    readonly property real tabCenterEnd: (host.verticalBar
        ? tabItemStart(verticalCalendarIcon) + verticalCalendarIcon.height + (notchLayout ? weatherReveal : 3 + verticalWeatherIcon.height)
        : tabItemStart(centerInfo) + centerInfo.width + (notchLayout ? weatherReveal : 6 + barWeather.width)) + tabsPadding
    readonly property var outerGaps: host.screenGaps
    readonly property bool centeredLayout: host.centeredLayout
    readonly property bool islandsLayout: host.islandsLayout
    // Islands float half the outer gap off the screen edge; pills keep the full gap between them.
    readonly property real islandGap: outerGaps[({top: 0, right: 1, bottom: 2, left: 3})[host.barEdge]] / 2
    readonly property real islandSpacing: islandGap * 2 + 8
    readonly property real reservedThickness: normalThickness + (islandsLayout ? islandGap : 0)
    readonly property bool notchLayout: host.notchLayout
    readonly property real panelGap: host.verticalBar ? host.windowGaps[1] + host.windowGaps[3] : host.windowGaps[0] + host.windowGaps[2]
    property bool hoverExpanded: false
    readonly property bool pointerInside: barHover.hovered || centeredHover.hovered
    onPointerInsideChanged: {
        if (pointerInside) { collapseDelay.stop(); hoverExpanded = true; }
        else collapseDelay.restart();
    }
    readonly property bool expanded: !centeredLayout || host.barPinned || hoverExpanded || panelOpen || pendingPanel !== null || host.barPointerHeld
    readonly property real itemGap: host.workspaceItemSpacing
    readonly property real endPadding: host.verticalBar ? 8 : 12
    readonly property real centerPadding: (centerExtent - (host.verticalBar ? verticalCalendarIcon.height : centerInfo.width)) / 2
    readonly property real leadingExtent: endPadding - centerPadding + (host.verticalBar
        ? verticalStart.height + itemGap + (mediaStrip.player ? verticalMedia.height + itemGap : 0) + verticalPin.height + itemGap + (verticalCapture.shown ? verticalCapture.height + itemGap : 0)
        : leftGroup.workspaces.width + itemGap + leftGroup.hardwareStatus.width + itemGap + (mediaStrip.visible ? mediaStrip.width + itemGap : 0) + barPin.width + itemGap + (barCapture.shown ? barCapture.width + itemGap : 0))
    readonly property real trailingExtent: endPadding - centerPadding + (host.verticalBar
        ? itemGap + verticalWeatherIcon.height + itemGap + verticalEnd.height
        : itemGap + barWeather.width + itemGap + rightSide.width + itemGap + notificationIcon.width)
    property real leadingReveal: centeredLayout && expanded ? Math.min(leadingExtent, (host.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : 0
    property real trailingReveal: centeredLayout && expanded ? Math.min(trailingExtent, (host.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : 0
    Behavior on leadingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    Behavior on trailingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    property bool weatherHovered: false
    readonly property bool weatherExpanded: weatherHovered || weatherMenu.visible || pendingPanel === weatherMenu
    readonly property real weatherExtent: host.verticalBar ? 3 + verticalWeatherIcon.height : 6 + barWeather.width
    property real weatherReveal: notchLayout && weatherExpanded ? weatherExtent : 0
    Behavior on weatherReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    Timer {
        id: weatherCollapseDelay
        interval: collapseDelay.interval
        onTriggered: bar.weatherHovered = false
    }
    readonly property real centerExtent: host.verticalBar ? 56 : centerInfo.width + 24
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
        target: host
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
        barEdge: host.barEdge
        clients: dockClientsRef.clients
        dockEnabled: host.barDock && host.barVisible && !FocusMode.enabled
        foreground: host.fg
        background: host.barBackground()
    }
    WorkspaceOverview {
        id: overview
        ipcEnabled: bar.isMainBar
        screen: bar.screen
        foreground: host.fg
        background: host.bg
        accent: host.activeBg
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
    visible: host.barVisible || panelOpen
    implicitWidth: modelData.width
    implicitHeight: modelData.height
    color: "transparent"
    exclusionMode: ExclusionMode.Normal
    // Auto-hide reserves no space, so revealing the bar slides it over windows instead of re-tiling them.
    exclusiveZone: !FocusMode.enabled && host.barVisible && !host.barAutoHide ? bar.reservedThickness : 0
    WlrLayershell.namespace: "desktop-bar"
    // Notification popups must have a strictly higher layer than
    // panels, rather than depending on same-layer mapping order.
    WlrLayershell.layer: panelOpen && !notificationPopups.visible ? WlrLayer.Overlay : WlrLayer.Top
    mask: dockInput
    WlrLayershell.keyboardFocus: panelOpen ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

    BarAutoHide {
        id: autoHide
        autoHide: host.barAutoHide
        pointerInside: bar.pointerInside || edgeHover.hovered
        held: bar.panelOpen || bar.pendingPanel !== null || bar.pendingOverview || overview.visible || host.barPointerHeld || notificationPopups.visible
    }
    Item {
        id: edgeSensor
        width: host.verticalBar ? 1 : bar.width
        height: host.verticalBar ? bar.height : 1
        x: host.barEdge === "right" ? bar.width - width : 0
        y: host.barEdge === "bottom" ? bar.height - height : 0
        visible: host.barAutoHide
        HoverHandler { id: edgeHover }
    }
    Region {
        id: dockInput
        width: 0; height: 0
        // Focus hides the bar but keeps its window: hiding the window crashes Quickshell.
        Region { item: edgeSensor.visible && !FocusMode.enabled ? edgeSensor : null }
        Region { item: host.barPointerHeld && !FocusMode.enabled ? bar.contentItem : null }
        Region { item: FocusMode.enabled ? null : host.notchLayout ? tabStrip : host.centeredLayout || host.islandsLayout ? null : barContents }
        IslandMask { surfaces: islandSurfaces.children }
        CenteredBarMask { surface: centeredOutline; edge: host.barEdge; depth: bar.normalThickness; bendRound: host.tabBendRound }
        Region { item: host.notchLayout && !FocusMode.enabled ? leadingTab : null }
        Region { item: host.notchLayout && !FocusMode.enabled ? notchTab : null }
        Region { item: host.notchLayout && !FocusMode.enabled ? trailingTab : null }
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
        target: notificationsRef
        function onToggleRequested() {
            // With a bar on every display, only the one in use opens the center.
            if (host.isActiveBar(bar)) bar.togglePanel(notificationCenter);
        }
    }
    Connections {
        target: host
        function onBarVisibleChanged() {
            if (!host.barVisible) bar.closePanels();
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
        service: notificationsRef
        foreground: host.fg
        background: host.barBackground()
        accent: host.activeBg
        barEdge: host.barEdge
    }

    NotificationCenter {
        id: notificationCenter
        service: notificationsRef
        maximumHeight: bar.screen.height - 70
        target: host.verticalBar ? bar.verticalNotificationIcon : notificationIcon
        barEdge: host.barEdge
        surfaceColor: host.barBackground()
        foreground: host.fg
        background: host.workspaceMenuBg
        accent: host.activeBg
    }

    PluginPanel {
        id: pluginPanel
        target: notificationIcon
        barEdge: host.barEdge; surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
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
        screenMargins: host.screenGaps
        target: barContents
        surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
        service: notificationsRef
        wifiControl: networkServiceRef; bluetoothControl: bar.bluetoothMenu; displayControl: bar.brightnessMenu
        keyboardControl: bar.keyboardMenu
        wifiGlyph: host.verticalBar ? bar.verticalWifiIcon.text : bar.wifiIcon.text
        battery: host.battery; mediaPlayer: bar.mediaStrip.player
        idleEnabled: host.idleLockEnabled; idleBusy: idleLockProcessRef.running
        barPosition: host.barEdge; appearance: host.barAppearance; layout: host.barLayout; barScreens: host.barScreens; barAutoHide: host.barAutoHide; barDock: host.barDock; mediaStyle: host.barMediaStyle; clockFormat: host.barClock; workspaceStyle: host.workspaceStyle
        onIdleToggleRequested: if (!idleLockProcessRef.running) idleLockProcessRef.running = true
        onLockRequested: runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")])
        onSettingRequested: function(key, value) { host.updateBarSetting(key, value); }
        onWorkspaceStyleRequested: function(value) { host.setWorkspaceStyle(value); }
        onPanelRequested: function(kind) { panelIpc.show(kind); }
        onPickerRequested: function(kind) { runAfterClose(["bash", Quickshell.shellDir + "/scripts/appearance-picker.sh", kind]); }
    }
    MediaMenu {
        id: mediaMenu
        target: host.verticalBar ? bar.verticalCalendarIcon : bar.mediaStrip
        barEdge: host.barEdge; surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
        player: bar.mediaStrip.player
    }
    BatteryMenu {
        id: batteryMenu
        target: host.verticalBar ? bar.verticalBatteryIcon : bar.batteryBarIcon
        barEdge: host.barEdge; surfaceColor: host.barBackground()
        foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
        battery: host.battery; displayControl: bar.brightnessMenu
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
    Component.onCompleted: host.registerBar(bar)
    Component.onDestruction: host.unregisterBar(bar)

    // The main bar receives shortcuts and forwards them to the bar of the display in use.
    IpcHandler {
        enabled: bar.isMainBar
        target: "controlCenter"
        function toggle(): void { host.activeBar(bar).toggleControlCenter(); }
        function show(page: string): void { host.activeBar(bar).showControlCenter(page); }
    }

    IpcHandler {
        id: panelIpc
        enabled: bar.isMainBar
        target: "panels"
        function inspect(): string { return host.activeBar(bar).inspectPanels(); }
        function close(): void { host.activeBar(bar).closePanels(); }
        function show(kind: string): void { host.activeBar(bar).showKind(kind); }
    }

    anchors {
        top: host.barEdge === "top" || host.verticalBar
        bottom: host.barEdge === "bottom" || host.verticalBar
        left: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "left"
        right: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "right"
    }

    Shape {
        id: centeredOutline
        visible: host.centeredLayout && !FocusMode.enabled
        readonly property real slope: bar.normalThickness + host.tabBendRound
        x: barContents.x - (host.verticalBar ? 0 : slope) + (host.verticalBar ? (host.barEdge === "left" ? -1 : 1) * bar.normalThickness * (1 - autoHide.progress) : 0)
        y: barContents.y - (host.verticalBar ? slope : 0) + (!host.verticalBar ? (host.barEdge === "top" ? -1 : 1) * bar.normalThickness * (1 - autoHide.progress) : 0)
        width: barContents.width + (host.verticalBar ? 0 : 2 * slope)
        height: barContents.height + (host.verticalBar ? 2 * slope : 0)
        HoverHandler { id: centeredHover }
        BarGestureArea {
            anchors.fill: parent
            hostWindow: bar
            edge: host.barEdge
            onCandidateChanged: host.dragCandidate = candidate
            onPointerHeld: function(held) { host.barPointerHeld = held }
            onDoubleTapped: function(button) { host.barDoubleClick(button) }
            onDropped: function(edge) { host.updateBarSetting("edge", edge) }
        }
        antialiasing: true
        ShapePath {
            strokeWidth: -1
            fillColor: host.barBackground()
            PathSvg { path: EdgeSlopes.outline(host.barEdge,
                host.verticalBar ? centeredOutline.height : centeredOutline.width,
                bar.normalThickness, 0, host.tabBendRound,
                [[centeredOutline.slope, (host.verticalBar ? centeredOutline.height : centeredOutline.width) - centeredOutline.slope]]) }
        }
    }

    Item {
        id: barContents
        visible: !FocusMode.enabled
        transform: Translate {
            x: host.verticalBar ? (host.barEdge === "left" ? -1 : 1) * (bar.normalThickness + (host.islandsLayout ? bar.islandGap : 0)) * (1 - autoHide.progress) : 0
            y: !host.verticalBar ? (host.barEdge === "top" ? -1 : 1) * (bar.normalThickness + (host.islandsLayout ? bar.islandGap : 0)) * (1 - autoHide.progress) : 0
        }
        width: host.verticalBar ? bar.thinThickness : (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.width)
        height: host.verticalBar ? (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.height) : bar.thinThickness
        x: host.verticalBar ? (host.barEdge === "right" ? bar.width - width - (bar.islandsLayout ? bar.islandGap : 0) : (bar.islandsLayout ? bar.islandGap : 0)) : bar.centeredLayout ? (bar.width - bar.centerExtent) / 2 - bar.leadingReveal : 0
        y: host.verticalBar ? (bar.centeredLayout ? (bar.height - bar.centerExtent) / 2 - bar.leadingReveal : 0) : (host.barEdge === "bottom" ? bar.height - height - (bar.islandsLayout ? bar.islandGap : 0) : (bar.islandsLayout ? bar.islandGap : 0))
        clip: bar.centeredLayout
        Item {
            id: tabStrip
            visible: host.notchLayout
            width: host.verticalBar ? host.tabStripThickness : parent.width
            height: host.verticalBar ? parent.height : host.tabStripThickness
            x: host.barEdge === "right" ? parent.width - width : 0
            y: host.barEdge === "bottom" ? parent.height - height : 0
        }
        TabSurface { id: leadingTab; start: 0; end: bar.tabLeadingEnd }
        TabSurface { id: notchTab; start: bar.tabCenterStart; end: bar.tabCenterEnd }
        TabSurface { id: trailingTab; start: bar.tabTrailingStart; end: host.verticalBar ? barContents.height : barContents.width }
        component TabSurface: Item {
            property real start
            property real end
            readonly property string barEdge: host.barEdge
            readonly property real revealProgress: 1
            readonly property bool detached: false
            visible: host.notchLayout
            width: host.verticalBar ? bar.normalThickness - host.tabStripThickness : end - start
            height: host.verticalBar ? end - start : bar.normalThickness - host.tabStripThickness
            x: host.verticalBar ? (host.barEdge === "right" ? 0 : host.tabStripThickness) : start
            y: host.verticalBar ? start : (host.barEdge === "bottom" ? 0 : host.tabStripThickness)

        }
        Shape {
            id: tabsOutline
            anchors.fill: parent
            visible: host.notchLayout
            antialiasing: true
            // One alpha silhouette also defines Hyprland's blur coverage.
            ShapePath {
                strokeWidth: -1
                fillColor: host.barBackground()
                PathSvg { path: {
                    return EdgeSlopes.outline(host.barEdge,
                        host.verticalBar ? tabsOutline.height : tabsOutline.width,
                        bar.normalThickness, host.tabStripThickness, host.tabBendRound,
                        [[0, bar.tabLeadingEnd], [bar.tabCenterStart, bar.tabCenterEnd], [bar.tabTrailingStart, host.verticalBar ? tabsOutline.height : tabsOutline.width]]);
                } }
            }
        }
        HoverHandler {
            id: barHover
            // The bar's own handler also sees the pointer over the clock and the weather,
            // whose mouse areas would hide it from a separate hover box behind them.
            readonly property bool overCenterTab: {
                if (!hovered || !bar.notchLayout) return false;
                var along = host.verticalBar ? point.position.y : point.position.x;
                return along >= bar.tabCenterStart && along <= bar.tabCenterEnd;
            }
            onOverCenterTabChanged: {
                if (overCenterTab) { weatherCollapseDelay.stop(); bar.weatherHovered = true; }
                else weatherCollapseDelay.restart();
            }
        }

    PanelWindow {
        screen: bar.screen
        visible: host.dragCandidate !== ""
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "desktop-bar-edge-preview"
        WlrLayershell.layer: WlrLayer.Overlay
        mask: Region {}
        anchors { top: true; bottom: true; left: true; right: true }
        Rectangle {
            readonly property bool vertical: host.dragCandidate === "left" || host.dragCandidate === "right"
            x: host.dragCandidate === "right" ? parent.width - width : 0
            y: host.dragCandidate === "bottom" ? parent.height - height : 0
            width: vertical ? host.barHeight : parent.width
            height: vertical ? parent.height : host.barHeight
            radius: DesktopStyle.radius(6)
            color: Qt.alpha(host.workspaceMenuBg, 0.65)
            border.width: 1
            border.color: host.activeBg
        }
    }

    Item {
        id: islandSurfaces
        visible: !FocusMode.enabled
        anchors.fill: parent
        IslandSurface { first: host.verticalBar ? verticalControlCenterLogo : leftGroup.controlCenterLogo }
        IslandSurface { first: host.verticalBar ? verticalOverviewIcon : leftGroup.overviewIcon; last: host.verticalBar ? verticalWorkspaces : leftGroup.workspaces }
        IslandSurface { first: host.verticalBar ? verticalHardware : leftGroup.hardwareStatus }
        IslandSurface { first: host.verticalBar ? bar.verticalCalendarIcon : bar.centerInfo }
        IslandSurface { first: host.verticalBar ? bar.verticalWeatherIcon : bar.barWeather }
        IslandSurface { first: host.verticalBar ? bar.verticalMedia : bar.mediaStrip; shown: host.verticalBar ? bar.verticalMedia.visible : bar.mediaStrip.visible }
        IslandSurface { first: host.verticalBar ? bar.verticalCapture : bar.barCapture; shown: host.verticalBar ? bar.verticalCapture.shown : bar.barCapture.shown }
        IslandSurface { first: host.verticalBar ? bar.verticalEnd : bar.rightSide; last: host.verticalBar ? bar.verticalEnd : notificationIcon }
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
        x: host.verticalBar ? 0 : leading.x - 4
        y: host.verticalBar ? leading.y - 4 : 0
        width: host.verticalBar ? bar.normalThickness : trailing.x + last.width - leading.x + 8
        height: host.verticalBar ? trailing.y + last.height - leading.y + 8 : bar.normalThickness
        radius: DesktopStyle.radius(PanelStyle.cornerRadius)
        color: host.barBackground()
        BarGestureArea {
            anchors.fill: parent
            hostWindow: bar
            edge: host.barEdge
            onCandidateChanged: host.dragCandidate = candidate
            onPointerHeld: function(held) { host.barPointerHeld = held }
            onDoubleTapped: function(button) { host.barDoubleClick(button) }
            onDropped: function(edge) { host.updateBarSetting("edge", edge) }
        }
    }

    BarSection {
        id: verticalSurface
        anchors.fill: parent
        visible: host.verticalBar
        edge: host.barEdge
        background: host.notchLayout || host.centeredLayout || host.islandsLayout ? "transparent" : host.barBackground()
        radius: 0

        BarGestureArea {
            anchors.fill: parent
            hostWindow: bar
            edge: host.barEdge
            onCandidateChanged: host.dragCandidate = candidate
            onPointerHeld: function(held) { host.barPointerHeld = held }
            onDoubleTapped: function(button) { host.barDoubleClick(button) }
            onDropped: function(edge) { host.updateBarSetting("edge", edge) }
        }

        Column {
            id: verticalStart
            opacity: bar.expanded ? 1 : 0
            enabled: bar.expanded
            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
            y: bar.islandsLayout ? host.screenGaps[0] + 4 : bar.centeredLayout ? bar.endPadding : 8
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: host.workspaceItemSpacing
            Column {
                id: verticalWorkspaces
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: host.workspaceItemSpacing
                EitrLogo {
                    id: verticalControlCenterLogo
                    foreground: host.fg; background: host.workspaceMenuBg
                    slotWidth: host.workspaceItemSize
                    anchors.horizontalCenter: parent.horizontalCenter
                    onClicked: bar.toggleControlCenter()
                }
                Item { width: 1; height: bar.islandsLayout ? bar.islandSpacing - 2 * host.workspaceItemSpacing : 0; visible: bar.islandsLayout }
                VerticalBarIcon { host: bar.host; id: verticalOverviewIcon; icon: "󰕮"; tooltip: Eitr.I18n.tr("Overview"); open: true; clickable: true; onClicked: bar.toggleOverview() }
                Repeater {
                    model: host.workspaceCount
                    BarButton {
                        host: bar.host
                        text: host.workspaceLabel(index, bar.screen)
                        tooltip: active ? "" : host.workspaceApps(index + 1)
                        visualStyle: host.workspaceStyle
                        active: host.workspaceActive(index + 1, bar.screen)
                        width: host.workspaceItemSize; buttonHeight: host.workspaceItemSize; fontSize: 14; cornerRadius: 6; textOffsetY: 0
                        anchors.horizontalCenter: parent.horizontalCenter
                        onClicked: host.focusWorkspace(index + 1)
                        onRightClicked: bar.togglePanel(workspaceMenu)
                    }
                }
            }
            Item { width: 1; height: bar.islandsLayout ? bar.islandSpacing - 2 * host.workspaceItemSpacing : 0; visible: bar.islandsLayout }
            Column {
                id: verticalHardware
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: host.workspaceItemSpacing
                VerticalBarIcon { host: bar.host; id: verticalAiIcon; icon: ""; iconSize: 16; tooltip: Eitr.I18n.tr("AI Usage"); open: true; clickable: true; onClicked: bar.togglePanel(aiMenu) }
                VerticalBarIcon { host: bar.host; id: verticalHardwareIcon; icon: "󰍛"; iconSize: 18; tooltip: Eitr.I18n.tr("Hardware"); open: true; clickable: true; onClicked: bar.togglePanel(hardwareMenu) }
                VerticalBarIcon { host: bar.host; id: verticalIdleLockIcon; icon: host.idleLockGlyph; iconSize: 17; tooltip: host.idleLockTooltip; open: true; clickable: true; onClicked: host.switchIdleLock() }
            }
        }

        BarVerticalCenter {
            id: barVerticalCenter
            host: bar.host
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
            host: bar.host
            barHost: bar
            batteryMenuRef: batteryMenu
            bluetoothMenuRef: bar.bluetoothMenu
            brightnessMenuRef: bar.brightnessMenu
            keyboardMenuRef: bar.keyboardMenu
            notificationCenterRef: notificationCenter
            notificationIconRef: notificationIcon
            obsMenuRef: bar.obsMenu
            remoteAccessServiceRef: remoteServiceRef
            streamingMenuRef: bar.streamingMenu
            tailscaleMenuRef: bar.tailscaleMenu
            volumeMenuRef: bar.volumeMenu
            wifiMenuRef: bar.wifiMenu
        }
    }

    BarSection {
        id: surface
        anchors.fill: parent
        visible: !host.verticalBar
        edge: host.barEdge
        background: host.notchLayout || host.centeredLayout || host.islandsLayout ? "transparent" : host.barBackground()
        radius: 0

        BarGestureArea {
            id: barGestures
            anchors.fill: parent
            hostWindow: bar
            edge: host.barEdge
            onCandidateChanged: host.dragCandidate = candidate
            onPointerHeld: function(held) { host.barPointerHeld = held }
            onDoubleTapped: function(button) { host.barDoubleClick(button) }
            onDropped: function(edge) { host.updateBarSetting("edge", edge) }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: bar.islandsLayout ? host.screenGaps[3] + 4 : bar.centeredLayout ? bar.endPadding : 12
            anchors.rightMargin: 9
            spacing: 0

            BarLeftGroup {
                id: leftGroup
                host: bar.host
                barWindow: bar
                styleMenu: workspaceMenu
                aiPanel: aiMenu
                hardwarePanel: hardwareMenu
                Layout.alignment: Qt.AlignVCenter
            }
            WorkspaceStyleMenu {
                id: workspaceMenu
                surfaceColor: host.barBackground()
                target: host.verticalBar ? verticalWorkspaces : leftGroup.workspaces
                barEdge: host.barEdge
                currentStyle: host.workspaceStyle
                accent: host.activeBg
                foreground: host.workspaceMenuFg
                background: host.workspaceMenuBg
                selectedForeground: host.activeFg
                onSelected: function(style) {
                    host.setWorkspaceStyle(style);
                }
            }

            SystemMonitorMenu {
                id: hardwareMenu
                surfaceColor: host.barBackground()
                maximumHeight: bar.screen.height - 70
                target: host.verticalBar ? verticalHardwareIcon : leftGroup.hardwareIcon
                barEdge: host.barEdge
                accent: host.activeBg
                foreground: host.fg
                background: host.workspaceMenuBg
            }

            AiUsageMenu {
                id: aiMenu
                surfaceColor: host.barBackground()
                maximumHeight: bar.screen.height - 70
                leftAligned: true
                target: host.verticalBar ? verticalAiIcon : leftGroup.aiIcon
                barEdge: host.barEdge
                accent: host.activeBg
                foreground: host.fg
                background: host.workspaceMenuBg
            }

            Item {
                Layout.fillWidth: true
            }

        }

            BarHorizontalStatus {
                id: barHorizontalStatus
                host: bar.host
                barHost: bar
                barCaptureRef: bar.barCapture
                batteryMenuRef: batteryMenu
                networkOwnerRef: networkServiceRef
                notificationIconRef: notificationIcon
                remoteAccessServiceRef: remoteServiceRef
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

            host: bar.host

            notificationService: notificationsRef
            id: notificationIcon
            onOpenRequested: bar.togglePanel(notificationCenter)
            opacity: bar.expanded ? 1 : 0
            enabled: bar.expanded
            visible: !host.verticalBar
            anchors.right: parent.right
            anchors.rightMargin: bar.islandsLayout ? host.screenGaps[1] + 4 : bar.centeredLayout ? bar.endPadding : 13
            anchors.verticalCenter: parent.verticalCenter
        }

        BarHorizontalCenter {
            id: barHorizontalCenter
            host: bar.host
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
