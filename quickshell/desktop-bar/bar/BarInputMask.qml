import ".."
import Quickshell

Region {
    required property var host
    required property var barHost
    required property var edgeSensorRef
    required property var tabStripRef
    required property var barContentsRef
    required property var leadingTabRef
    required property var notchTabRef
    required property var trailingTabRef

    id: dockInput
    width: 0; height: 0
    // Focus hides the bar but keeps its window: hiding the window crashes Quickshell.
    Region { item: edgeSensorRef.visible && !FocusMode.enabled ? edgeSensorRef : null }
    Region { item: host.barPointerHeld && !FocusMode.enabled ? barHost.contentItem : null }
    Region { item: FocusMode.enabled ? null : host.notchLayout ? tabStripRef : host.centeredLayout || host.islandsLayout ? null : barContentsRef }
    IslandMask { surfaces: barHost.islandSurfaces.children }
    CenteredBarMask { surface: barHost.centeredOutline; edge: host.barEdge; depth: barHost.normalThickness; bendRound: host.tabBendRound }
    Region { item: host.notchLayout && !FocusMode.enabled ? leadingTabRef : null }
    Region { item: host.notchLayout && !FocusMode.enabled ? notchTabRef : null }
    Region { item: host.notchLayout && !FocusMode.enabled ? trailingTabRef : null }
    Region { item: barHost.wifiMenu.opened ? barHost.wifiMenu : null }
    Region { item: barHost.bluetoothMenu.opened ? barHost.bluetoothMenu : null }
    Region { item: barHost.brightnessMenu.opened ? barHost.brightnessMenu : null }
    Region { item: barHost.volumeMenu.opened ? barHost.volumeMenu : null }
    Region { item: barHost.tailscaleMenu.opened ? barHost.tailscaleMenu : null }
    Region { item: barHost.streamingMenu.opened ? barHost.streamingMenu : null }
    Region { item: barHost.keyboardMenu.opened ? barHost.keyboardMenu : null }
    Region { item: barHost.calendarMenu.opened ? barHost.calendarMenu : null }
    Region { item: barHost.weatherMenu.opened ? barHost.weatherMenu : null }
    Region { item: barHost.hardwareMenu.opened ? barHost.hardwareMenu : null }
    Region { item: barHost.aiMenu.opened ? barHost.aiMenu : null }
    Region { item: barHost.obsMenu.opened ? barHost.obsMenu : null }
    Region { item: barHost.recordingMenu.opened ? barHost.recordingMenu : null }
    Region { item: barHost.workspaceMenu.opened ? barHost.workspaceMenu : null }
    Region { item: barHost.notificationCenter.opened ? barHost.notificationCenter : null }
    Region { item: barHost.controlCenter.opened ? barHost.controlCenter : null }
    Region { item: barHost.mediaMenu.opened ? barHost.mediaMenu : null }
    Region { item: barHost.batteryMenu.opened ? barHost.batteryMenu : null }
    Region { item: barHost.pluginPanel.opened ? barHost.pluginPanel : null }
}
