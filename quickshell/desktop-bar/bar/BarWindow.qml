import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland

PanelWindow {
    id: bar

    readonly property alias barVerticalCenter: barVerticalPlacement.barVerticalCenterItem
    readonly property alias barVerticalStatus: barVerticalPlacement.barVerticalStatusItem
    readonly property alias verticalAiIcon: barVerticalPlacement.verticalAiIconItem
    readonly property alias verticalControlCenterLogo: barVerticalPlacement.verticalControlCenterLogoItem
    readonly property alias verticalHardware: barVerticalPlacement.verticalHardwareItem
    readonly property alias verticalHardwareIcon: barVerticalPlacement.verticalHardwareIconItem
    readonly property alias verticalIdleLockIcon: barVerticalPlacement.verticalIdleLockIconItem
    readonly property alias verticalOverviewIcon: barVerticalPlacement.verticalOverviewIconItem
    readonly property alias verticalStart: barVerticalPlacement.verticalStartItem
    readonly property alias verticalSurface: barVerticalPlacement
    readonly property alias verticalWorkspaces: barVerticalPlacement.verticalWorkspacesItem

    readonly property alias aiMenu: barHorizontalPlacement.aiMenuItem
    readonly property alias barGestures: barHorizontalPlacement.barGesturesItem
    readonly property alias barHorizontalCenter: barHorizontalPlacement.barHorizontalCenterItem
    readonly property alias barHorizontalStatus: barHorizontalPlacement.barHorizontalStatusItem
    readonly property alias hardwareMenu: barHorizontalPlacement.hardwareMenuItem
    readonly property alias leftGroup: barHorizontalPlacement.leftGroupItem
    readonly property alias notificationIcon: barHorizontalPlacement.notificationIconItem
    readonly property alias surface: barHorizontalPlacement
    readonly property alias workspaceMenu: barHorizontalPlacement.workspaceMenuItem

    readonly property alias islandSurfaces: barIslands

    readonly property alias centeredHover: barCenteredOutline.centeredHoverItem
    readonly property alias centeredOutline: barCenteredOutline

    readonly property alias batteryMenu: barPanels.batteryMenuItem
    readonly property alias controlCenter: barPanels.controlCenterItem
    readonly property alias mediaMenu: barPanels.mediaMenuItem
    readonly property alias notificationCenter: barPanels.notificationCenterItem
    readonly property alias notificationPopups: barPanels.notificationPopupsItem
    readonly property alias panelIpc: barPanels.panelIpcItem
    readonly property alias pluginPanel: barPanels.pluginPanelItem

    readonly property alias autoHideRef: autoHide

    readonly property alias tabStrip: barTabs.tabStripItem
    readonly property alias leadingTab: barTabs.leadingTabItem
    readonly property alias notchTab: barTabs.notchTabItem
    readonly property alias trailingTab: barTabs.trailingTabItem
    readonly property alias tabsOutline: barTabs.tabsOutlineItem

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
    BarInputMask {
        id: dockInput
        host: bar.host
        barHost: bar
        edgeSensorRef: edgeSensor
        tabStripRef: tabStrip
        barContentsRef: barContents
        leadingTabRef: leadingTab
        notchTabRef: notchTab
        trailingTabRef: trailingTab
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
    readonly property alias verticalMiddle: barVerticalPlacement.verticalMiddleItem
    readonly property alias verticalMedia: barVerticalPlacement.verticalMediaItem
    readonly property alias verticalCapture: barVerticalPlacement.verticalCaptureItem
    readonly property alias verticalPin: barVerticalPlacement.verticalPinItem
    readonly property alias verticalCalendarIcon: barVerticalPlacement.verticalCalendarIconItem
    readonly property alias verticalWeatherIcon: barVerticalPlacement.verticalWeatherIconItem
    readonly property alias verticalEnd: barVerticalPlacement.verticalEndItem
    readonly property alias verticalWifiIcon: barVerticalPlacement.verticalWifiIconItem
    readonly property alias verticalBluetoothIcon: barVerticalPlacement.verticalBluetoothIconItem
    readonly property alias verticalDisplayIcon: barVerticalPlacement.verticalDisplayIconItem
    readonly property alias verticalVolumeIcon: barVerticalPlacement.verticalVolumeIconItem
    readonly property alias verticalTailscaleIcon: barVerticalPlacement.verticalTailscaleIconItem
    readonly property alias verticalStreamingIcon: barVerticalPlacement.verticalStreamingIconItem
    readonly property alias verticalObsIcon: barVerticalPlacement.verticalObsIconItem
    readonly property alias verticalKeyboardIcon: barVerticalPlacement.verticalKeyboardIconItem
    readonly property alias verticalUpdatesIcon: barVerticalPlacement.verticalUpdatesIconItem
    readonly property alias verticalBatteryIcon: barVerticalPlacement.verticalBatteryIconItem
    readonly property alias verticalNotificationIcon: barVerticalPlacement.verticalNotificationIconItem
    readonly property alias rightSide: barHorizontalPlacement.rightSideItem
    readonly property alias statusToggle: barHorizontalPlacement.statusToggleItem
    readonly property alias wifiIcon: barHorizontalPlacement.wifiIconItem
    readonly property alias wifiMenu: barHorizontalPlacement.wifiMenuItem
    readonly property alias bluetoothIcon: barHorizontalPlacement.bluetoothIconItem
    readonly property alias bluetoothMenu: barHorizontalPlacement.bluetoothMenuItem
    readonly property alias brightnessIcon: barHorizontalPlacement.brightnessIconItem
    readonly property alias brightnessMenu: barHorizontalPlacement.brightnessMenuItem
    readonly property alias volumeIcon: barHorizontalPlacement.volumeIconItem
    readonly property alias volumeMenu: barHorizontalPlacement.volumeMenuItem
    readonly property alias tailscaleIcon: barHorizontalPlacement.tailscaleIconItem
    readonly property alias tailscaleMenu: barHorizontalPlacement.tailscaleMenuItem
    readonly property alias streamingIcon: barHorizontalPlacement.streamingIconItem
    readonly property alias streamingMenu: barHorizontalPlacement.streamingMenuItem
    readonly property alias obsIcon: barHorizontalPlacement.obsIconItem
    readonly property alias keyboardIcon: barHorizontalPlacement.keyboardIconItem
    readonly property alias keyboardMenu: barHorizontalPlacement.keyboardMenuItem
    readonly property alias updatesIcon: barHorizontalPlacement.updatesIconItem
    readonly property alias batteryBarIcon: barHorizontalPlacement.batteryBarIconItem
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
    function openPluginPanel(plugin, panel, target) { return barPanels.openPluginPanel(plugin, panel, target); }
    function showControlCenter(page) { return barPanels.showControlCenter(page); }
    function toggleControlCenter() { return barPanels.toggleControlCenter(); }
    function showKind(kind) { return barPanels.showKind(kind); }
    function inspectPanels() { return barPanels.inspectPanels(); }

    anchors {
        top: host.barEdge === "top" || host.verticalBar
        bottom: host.barEdge === "bottom" || host.verticalBar
        left: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "left"
        right: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "right"
    }

    BarCenteredOutline {
        id: barCenteredOutline
        host: bar.host
        barHost: bar
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
        BarTabs {
            id: barTabs
            host: bar.host
            barHost: bar
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

    BarIslands {
        id: barIslands
        host: bar.host
        barHost: bar
    }

    BarVerticalPlacement {
        id: barVerticalPlacement
        host: bar.host
        barHost: bar
    }

    BarHorizontalPlacement {
        id: barHorizontalPlacement
        host: bar.host
        barHost: bar
    }

    }

}
