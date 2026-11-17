import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland

PanelWindow {
    id: bar

    readonly property var barVerticalCenter: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.barVerticalCenterItem : emptyVertical
    readonly property var barVerticalStatus: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.barVerticalStatusItem : emptyVertical
    readonly property var verticalAiIcon: verticalIcons["ai"] || emptyVertical
    readonly property var verticalControlCenterLogo: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalControlCenterLogoItem : emptyVertical
    readonly property var verticalHardware: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalHardwareItem : emptyVertical
    readonly property var verticalHardwareIcon: verticalIcons["hardware"] || emptyVertical
    readonly property var verticalIdleLockIcon: verticalIcons["idleLock"] || emptyVertical
    readonly property var verticalOverviewIcon: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalOverviewIconItem : emptyVertical
    readonly property var verticalStart: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalStartItem : emptyVertical
    readonly property var verticalSurface: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item : emptyVertical
    readonly property var verticalWorkspaces: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalWorkspacesItem : emptyVertical

    readonly property alias aiMenu: barHorizontalPlacement.aiMenuItem
    readonly property alias barGestures: barHorizontalPlacement.barGesturesItem
    readonly property alias barHorizontalCenter: barHorizontalPlacement.barHorizontalCenterItem
    readonly property alias barHorizontalStatus: barHorizontalPlacement.barHorizontalStatusItem
    readonly property alias hardwareMenu: barHorizontalPlacement.hardwareMenuItem
    readonly property alias leftGroup: barHorizontalPlacement.leftGroupItem
    readonly property var notificationIcon: horizontalIcons["notifications"] || rightSide
    readonly property alias surface: barHorizontalPlacement
    readonly property alias workspaceMenu: barHorizontalPlacement.workspaceMenuItem

    property var horizontalIcons: ({})
    property var verticalIcons: ({})
    function setIconItem(vertical, id, item, expectingMatch) {
        const next = BarIconOrder.updateRegistry(vertical ? verticalIcons : horizontalIcons, id, item, expectingMatch);
        if (!next) return;
        if (vertical) verticalIcons = next; else horizontalIcons = next;
    }
    function registerIconItem(vertical, id, item) { setIconItem(vertical, id, item, null); }
    function unregisterIconItem(vertical, id, item) { setIconItem(vertical, id, null, item); }
    function iconZone(id) { return BarIconOrder.zoneOf(id); }
    function iconItem(id) { return (host.verticalBar ? verticalIcons[id] : horizontalIcons[id]) || null; }
    function iconTarget(id, fallback, hiddenFallback) {
        return BarIconOrder.resolveTarget(iconItem(id), iconZone(id), host.iconsOpen, host.verticalBar,
            hiddenFallback || notificationIcon || rightSide, fallback || stripItem);
    }

    readonly property var islandSurfaces: barIslandsLoader.item

    readonly property var centeredHover: barCenteredOutlineLoader.item ? barCenteredOutlineLoader.item.centeredHoverItem : null
    readonly property var centeredOutline: barCenteredOutlineLoader.item

    readonly property alias batteryMenu: barPanels.batteryMenuItem
    readonly property alias controlCenter: barPanels.controlCenterItem
    readonly property alias mediaMenu: barPanels.mediaMenuItem
    readonly property alias dropDashboard: barPanels.dropDashboardItem
    readonly property alias notificationCenter: barPanels.notificationCenterItem
    readonly property alias notificationPopups: barPanels.notificationPopupsItem
    readonly property alias panelIpc: barPanels.panelIpcItem
    readonly property alias pluginPanel: barPanels.pluginPanelItem

    readonly property alias autoHideRef: autoHide

    readonly property var tabStrip: barTabsLoader.item ? barTabsLoader.item.tabStripItem : null
    readonly property var leadingTab: barTabsLoader.item ? barTabsLoader.item.leadingTabItem : null
    readonly property var notchTab: barTabsLoader.item ? barTabsLoader.item.notchTabItem : null
    readonly property var trailingTab: barTabsLoader.item ? barTabsLoader.item.trailingTabItem : null
    readonly property var tabsOutline: barTabsLoader.item ? barTabsLoader.item.tabsOutlineItem : null

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
    // The tab slopes start right at the outermost icons.
    readonly property real tabsPadding: 0
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
        : leftGroup.hardwareStatus.width > 0
            ? tabItemStart(leftGroup.hardwareStatus) + leftGroup.hardwareStatus.width
            : tabItemStart(leftGroup.workspaces) + leftGroup.workspaces.width) + tabsPadding
    readonly property real tabTrailingStart: tabItemStart(host.verticalBar ? verticalEnd : rightSide) - tabsPadding
    readonly property var clockPlugins: host.verticalBar ? (barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.clockPluginsItem : emptyVertical) : barHorizontalPlacement.clockPluginsItem
    readonly property real clockPluginExtent: (host.verticalBar ? clockPlugins.implicitHeight : clockPlugins.implicitWidth) > 0
        ? (host.verticalBar ? clockPlugins.implicitHeight : clockPlugins.implicitWidth) + (islandsLayout ? islandSpacing : centeredLayout ? itemGap : host.verticalBar ? 3 : 6) : 0
    readonly property real tabCenterStart: (host.verticalBar
        ? tabItemStart(verticalMedia.visible ? verticalMedia : verticalCapture.shown ? verticalCapture : clockPlugins.height > 0 ? clockPlugins : verticalCalendarIcon)
        : tabItemStart(mediaStrip.visible ? mediaStrip : barCapture.shown ? barCapture : clockPlugins.width > 0 ? clockPlugins : centerInfo)) - tabsPadding
    readonly property real tabCenterEnd: (host.verticalBar
        ? tabItemStart(verticalCalendarIcon) + verticalCalendarIcon.height + (notchLayout ? weatherReveal : weatherExtent)
        : tabItemStart(centerInfo) + centerInfo.width + (notchLayout ? weatherReveal : weatherExtent)) + tabsPadding
    readonly property var outerGaps: host.screenGaps
    readonly property bool centeredLayout: host.centeredLayout
    readonly property bool islandsLayout: host.islandsLayout
    readonly property bool dynamicLayout: host.dynamicLayout
    readonly property bool dropLayout: host.dropLayout
    readonly property bool floatingIslands: islandsLayout || dynamicLayout || dropLayout
    readonly property var dynamicSurfaces: barDynamicLoader.item
    readonly property var dropSurfaces: barDropLoader.item
    // Islands float half the outer gap off the screen edge; pills keep the full gap between them.
    readonly property real islandGap: outerGaps[({top: 0, right: 1, bottom: 2, left: 3})[host.barEdge]] / 2
    readonly property real islandSpacing: islandGap * 2 + 8
    // Attached islands sit against the edge: no gap before the pills, only their depth reserved.
    readonly property bool attachedIslands: host.attachedIslands
    readonly property real edgeGap: floatingIslands && !attachedIslands ? islandGap : 0
    readonly property real reservedThickness: normalThickness + edgeGap
    readonly property bool notchLayout: host.notchLayout
    readonly property real panelGap: host.verticalBar ? host.windowGaps[1] + host.windowGaps[3] : host.windowGaps[0] + host.windowGaps[2]
    property bool hoverExpanded: false
    readonly property bool pointerInside: barHover.hovered || (centeredHover && centeredHover.hovered)
    onPointerInsideChanged: {
        if (pointerInside) { collapseDelay.stop(); if (!moments.current) hoverExpanded = true; }
        else collapseDelay.restart();
    }
    readonly property bool expanded: !centeredLayout || host.barPinned || hoverExpanded || panelOpen || pendingPanel !== null || host.barPointerHeld
    readonly property real itemGap: host.workspaceItemSpacing
    readonly property real endPadding: host.verticalBar ? 8 : 4
    readonly property real centerPadding: (centerExtent - (host.verticalBar ? verticalCalendarIcon.height : centerInfo.width)) / 2
    readonly property real leadingExtent: clockPluginExtent + endPadding - centerPadding + (host.verticalBar
        ? verticalStart.height + itemGap + (mediaStrip.present ? verticalMedia.height + itemGap : 0) + verticalPin.height + itemGap + (verticalCapture.shown ? verticalCapture.height + itemGap : 0)
        : leftGroup.workspaces.width + (leftGroup.hardwareStatus.width > 0 ? itemGap + leftGroup.hardwareStatus.width : 0) + itemGap + (mediaStrip.visible ? mediaStrip.width + itemGap : 0) + barPin.width + itemGap + (barCapture.shown ? barCapture.width + itemGap : 0))
    readonly property real trailingExtent: endPadding - centerPadding + (host.verticalBar
        ? (verticalWeatherIcon.height > 0 ? itemGap + verticalWeatherIcon.height : 0) + (verticalEnd.height > 0 ? itemGap + verticalEnd.height : 0)
        : (barWeather.width > 0 ? itemGap + barWeather.width : 0) + (rightSide.width > 0 ? itemGap + rightSide.width : 0))
    // Collapsed, Centered still opens room before the clock for what is happening beside it.
    readonly property bool activityShown: host.verticalBar ? verticalCapture.shown : barCapture.shown
    readonly property real collapsedLeading: activityShown
        ? Math.max(0, endPadding - centerPadding + (host.verticalBar ? verticalCapture.height : barCapture.width) + itemGap) : 0
    property real leadingReveal: !centeredLayout ? 0 : expanded ? Math.min(leadingExtent, (host.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : collapsedLeading
    property real trailingReveal: centeredLayout && expanded ? Math.min(trailingExtent, (host.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : 0
    Behavior on leadingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    Behavior on trailingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    // Tabs always shows the weather after the clock, inside the centre tab.
    readonly property real weatherExtent: host.verticalBar ? (verticalWeatherIcon.height > 0 ? 3 + verticalWeatherIcon.height : 0) : (barWeather.width > 0 ? 6 + barWeather.width : 0)
    readonly property real weatherReveal: notchLayout ? weatherExtent : 0
    // Centered: the slopes start right at the clock (its button keeps 8 px of padding).
    property real momentExtent: centeredLayout && !expanded
        ? (host.verticalBar ? verticalCalendarIcon.momentExtent : centerInfo.momentExtent) : 0
    Behavior on momentExtent { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    readonly property real centerExtent: Math.max(host.verticalBar ? 56 : centerInfo.width,
        momentExtent)
    Timer {
        id: collapseDelay
        interval: 350
        onTriggered: bar.hoverExpanded = false
    }
    readonly property var dockPanels: [wifiMenu, bluetoothMenu, brightnessMenu, volumeMenu, streamingMenu,
        keyboardMenu, calendarMenu, weatherMenu, hardwareMenu, aiMenu, obsMenu, recordingMenu, workspaceMenu, notificationCenter, controlCenter, mediaMenu, dropDashboard, batteryMenu, pluginPanel].filter(panel => !!panel)
    readonly property bool panelOpen: dockPanels.some(panel => panel.visible)
    readonly property var panelFocusWindows: notificationPopups.visible ? [bar, notificationPopups] : [bar]
    property var pendingPanel: null
    property bool pendingOverview: false
    readonly property bool overviewOpen: overview.visible

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
    function panel(kind) { return barPanels.ensure(kind); }
    function toggleKind(kind) { barPanels.toggleKind(kind); }
    function showPanel(panel) {
        if (!panel) return;
        pendingOverview = false;
        overview.opened = false;
        pendingPanel = panel;
        dockPanels.forEach(other => other.opened = false);
        finishPanelSwitch();
    }
    function togglePanel(panel) {
        if (!panel) return;
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
        workspaceRows: host.workspaceAssignments
        monitorName: bar.screen ? bar.screen.name : host.primaryDisplay
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
    // The window stays mapped while the bar is hidden: Quickshell deletes a hidden layer
    // window, and panels it hosted crashed Qt on the stale window. Hiding draws nothing
    // and passes every click through instead. Opacity, not visible: panelOpen reads the
    // panels' visibility, and they live under this content item.
    readonly property bool shown: host.barVisible || panelOpen
    contentItem.opacity: shown ? 1 : 0
    implicitWidth: modelData.width
    implicitHeight: modelData.height
    color: "transparent"
    exclusionMode: ExclusionMode.Normal
    // Auto-hide reserves no space, so revealing the bar slides it over windows instead of re-tiling them.
    // Nothing is reserved during the first second: the saved auto-hide preference loads just after
    // the bar starts, and a zone changed that early could stay stuck at its first value in Hyprland
    // (windows kept a bar-high gap). Changes after that apply normally.
    exclusiveZone: zoneReady.done && !FocusMode.enabled && host.barVisible && !host.barAutoHide ? bar.reservedThickness : 0
    Timer { id: zoneReady; property bool done: false; interval: 1000; running: true; onTriggered: done = true }
    WlrLayershell.namespace: "desktop-bar"
    // Notification popups must have a strictly higher layer than
    // panels, rather than depending on same-layer mapping order.
    WlrLayershell.layer: panelOpen && !notificationPopups.visible ? WlrLayer.Overlay : WlrLayer.Top
    property var choicePopups: []
    mask: shown ? dockInput : hiddenInput
    Region { id: hiddenInput }
    WlrLayershell.keyboardFocus: panelOpen ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

    BarAutoHide {
        id: autoHide
        autoHide: host.barAutoHide
        pointerInside: bar.pointerInside || edgeHover.hovered
        // Drop's dashboard lets go as soon as it starts closing, so its card can retract
        // into the edge in one motion instead of first folding back into the pill.
        // A new notification also brings the bar out until its popups have gone.
        held: bar.dockPanels.some(panel => panel === bar.dropDashboard ? panel.opened : panel.visible) || bar.pendingPanel !== null || bar.pendingOverview || overview.visible || host.barPointerHeld
            || clockActivity.alerting || !!moments.current
    }
    readonly property alias moments: moments
    BarMoments { id: moments; host: bar.host; barHost: bar }
    BarMomentPlacement { host: bar.host; barHost: bar; owner: moments }
    readonly property alias clockActivity: clockActivity
    ClockActivityState { id: clockActivity; host: bar.host; barHost: bar }
    // An empty item the input mask adds and drops as the auto-hide slide settles.
    Item { id: slideSettled; width: 0; height: 0 }
    Item {
        id: edgeSensor
        // A 1 px trigger at the edge; once revealed it spans the bar's depth, so moving
        // along the bar toward an island across click-through gaps keeps it shown.
        readonly property real depth: autoHide.progress > 0 ? bar.reservedThickness : 1
        width: host.verticalBar ? depth : bar.width
        height: host.verticalBar ? bar.height : depth
        x: host.barEdge === "right" ? bar.width - width : 0
        y: host.barEdge === "bottom" ? bar.height - height : 0
        visible: host.barAutoHide
        HoverHandler { id: edgeHover }
    }
    BarInputMask {
        id: dockInput
        host: bar.host
        barHost: bar
        edgeSensorRef: edgeSensor
        tabStripRef: tabStrip
        barContentsRef: barContents
        slideSettledRef: slideSettled
        leadingTabRef: leadingTab
        notchTabRef: notchTab
        trailingTabRef: trailingTab
    }

    Connections {
        target: notificationsRef
        function onToggleRequested() {
            // With a bar on every display, only the one in use opens the center.
            if (host.isActiveBar(bar)) bar.toggleKind("notifications");
        }
    }
    Connections {
        target: host
        function onBarVisibleChanged() {
            if (!host.barVisible) bar.closePanels();
        }
    }

    // Centre and status items remain available to the bar geometry and panel frame.
    readonly property var verticalMiddle: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalMiddleItem : emptyVertical
    readonly property var verticalMedia: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalMediaItem : emptyVertical
    readonly property var verticalCapture: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalCaptureItem : emptyVertical
    readonly property var verticalPin: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalPinItem : emptyVertical
    readonly property var verticalCalendarIcon: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalCalendarIconItem : emptyVertical
    readonly property var verticalWeatherIcon: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalWeatherIconItem : emptyVertical
    readonly property var verticalEnd: barVerticalPlacementLoader.item ? barVerticalPlacementLoader.item.verticalEndItem : emptyVertical
    readonly property var verticalWifiIcon: verticalIcons["wifi"] || emptyVertical
    readonly property var verticalBluetoothIcon: verticalIcons["bluetooth"] || emptyVertical
    readonly property var verticalDisplayIcon: verticalIcons["display"] || emptyVertical
    readonly property var verticalVolumeIcon: verticalIcons["audio"] || emptyVertical
    readonly property var verticalStreamingIcon: verticalIcons["streaming"] || emptyVertical
    readonly property var verticalObsIcon: verticalIcons["obs"] || emptyVertical
    readonly property var verticalKeyboardIcon: verticalIcons["keyboard"] || emptyVertical
    readonly property var verticalUpdatesIcon: verticalIcons["updates"] || emptyVertical
    readonly property var verticalBatteryIcon: verticalIcons["battery"] || emptyVertical
    readonly property var verticalNotificationIcon: verticalIcons["notifications"] || emptyVertical
    readonly property alias rightSide: barHorizontalPlacement.rightSideItem
    readonly property alias statusToggle: barHorizontalPlacement.statusToggleItem
    readonly property var wifiIcon: horizontalIcons["wifi"] || null
    readonly property alias wifiMenu: barHorizontalPlacement.wifiMenuItem
    readonly property var bluetoothIcon: horizontalIcons["bluetooth"] || null
    readonly property alias bluetoothMenu: barHorizontalPlacement.bluetoothMenuItem
    readonly property var brightnessIcon: horizontalIcons["display"] || null
    readonly property alias brightnessMenu: barHorizontalPlacement.brightnessMenuItem
    readonly property var volumeIcon: horizontalIcons["audio"] || null
    readonly property alias volumeMenu: barHorizontalPlacement.volumeMenuItem
    readonly property var streamingIcon: horizontalIcons["streaming"] || null
    readonly property alias streamingMenu: barHorizontalPlacement.streamingMenuItem
    readonly property var obsIcon: horizontalIcons["obs"] || null
    readonly property var keyboardIcon: horizontalIcons["keyboard"] || null
    readonly property alias keyboardMenu: barHorizontalPlacement.keyboardMenuItem
    readonly property var updatesIcon: horizontalIcons["updates"] || null
    readonly property var batteryBarIcon: horizontalIcons["battery"] || null
    readonly property alias obsMenu: barHorizontalPlacement.obsMenuItem
    readonly property alias recordingMenu: barHorizontalPlacement.recordingMenuItem
    readonly property alias centerInfo: barHorizontalPlacement.centerInfoItem
    readonly property alias barCapture: barHorizontalPlacement.barCaptureItem
    readonly property alias barPin: barHorizontalPlacement.barPinItem
    readonly property alias mediaStrip: barHorizontalPlacement.mediaStripItem
    readonly property alias barWeather: barHorizontalPlacement.barWeatherItem
    readonly property alias calendarMenu: barHorizontalPlacement.calendarMenuItem
    readonly property alias weatherMenu: barHorizontalPlacement.weatherMenuItem

    BarPanels {
        id: barPanels
        host: bar.host
        barHost: bar
    }
    Component.onCompleted: host.registerBar(bar)
    Component.onDestruction: host.unregisterBar(bar)
    function openPluginPanel(plugin, panel, target) {
        if (plugin === "weather" && panel === "forecast" && PluginRegistry.weatherEnabled) {
            if (target) weatherMenu.morphAnchor = target;
            togglePanel(weatherMenu);
            return;
        }
        return barPanels.openPluginPanel(plugin, panel, target);
    }
    function showControlCenter(page) { return barPanels.showControlCenter(page); }
    function toggleControlCenter() { return barPanels.toggleControlCenter(); }
    function showKind(kind) { return barPanels.showKind(kind); }
    function showClock(page) { return host ? host.showClock(page) : undefined; }
    function clickPlugin(plugin) { return barPanels.clickPlugin(plugin); }
    function inspectPanels() { return barPanels.inspectPanels(); }

    anchors {
        top: host.barEdge === "top" || host.verticalBar
        bottom: host.barEdge === "bottom" || host.verticalBar
        left: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "left"
        right: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "right"
    }

    Loader {
        id: barCenteredOutlineLoader
        active: bar.centeredLayout
        sourceComponent: BarCenteredOutline {
            id: barCenteredOutline
            host: bar.host
            barHost: bar
        }
    }

    Item {
        id: barContents
        visible: !FocusMode.enabled
        transform: Translate {
            // Drop stays in place: its pill shrinks into the auto-hide dot instead of sliding.
            readonly property real distance: bar.dropLayout ? 0 : (bar.normalThickness + bar.edgeGap) * (1 - autoHide.progress)
            x: host.verticalBar ? (host.barEdge === "left" ? -1 : 1) * distance : 0
            y: !host.verticalBar ? (host.barEdge === "top" ? -1 : 1) * distance : 0
        }
        width: host.verticalBar ? bar.thinThickness : (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.width)
        height: host.verticalBar ? (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.height) : bar.thinThickness
        x: host.verticalBar ? (host.barEdge === "right" ? bar.width - width - bar.edgeGap : bar.edgeGap) : bar.centeredLayout ? (bar.width - bar.centerExtent) / 2 - bar.leadingReveal : 0
        y: host.verticalBar ? (bar.centeredLayout ? (bar.height - bar.centerExtent) / 2 - bar.leadingReveal : 0) : (host.barEdge === "bottom" ? bar.height - height - bar.edgeGap : bar.edgeGap)
        clip: bar.centeredLayout
        Loader {
            id: barTabsLoader
            anchors.fill: parent
            active: bar.notchLayout
            sourceComponent: BarTabs {
                id: barTabs
                host: bar.host
                barHost: bar
            }
        }
        HoverHandler {
            id: barHover
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

    Loader {
        id: barIslandsLoader
        anchors.fill: parent
        active: bar.islandsLayout
        sourceComponent: BarIslands {
            id: barIslands
            host: bar.host
            barHost: bar
        }
    }

    Loader {
        id: barDynamicLoader
        z: 1
        anchors.fill: parent
        active: bar.dynamicLayout
        sourceComponent: BarDynamic {
            id: barDynamic
            host: bar.host
            barHost: bar
        }
    }

    Loader {
        id: barDropLoader
        z: 1
        anchors.fill: parent
        active: bar.dropLayout
        sourceComponent: BarDrop {
            id: barDrop
            host: bar.host
            barHost: bar
        }
    }

    Item {
        id: emptyVertical
        visible: false
        property bool shown: false
        property string text: ""
    }
    Loader {
        id: barVerticalPlacementLoader
        anchors.fill: parent
        active: bar.host.verticalBar
        sourceComponent: BarVerticalPlacement {
            host: bar.host
            barHost: bar
        }
    }

    BarHorizontalPlacement {
        id: barHorizontalPlacement
        host: bar.host
        barHost: bar
    }

    }

}
