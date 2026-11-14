import ".."
import QtQuick
import Eitr as Eitr

BarSection {
    readonly property alias clockPluginsItem: barVerticalCenter.clockPluginsItem
    required property var host
    readonly property alias verticalEndItem: barVerticalStatus.verticalEndItem
    readonly property alias verticalWifiIconItem: barVerticalStatus.verticalWifiIconItem
    readonly property alias verticalBluetoothIconItem: barVerticalStatus.verticalBluetoothIconItem
    readonly property alias verticalDisplayIconItem: barVerticalStatus.verticalDisplayIconItem
    readonly property alias verticalVolumeIconItem: barVerticalStatus.verticalVolumeIconItem
    readonly property alias verticalStreamingIconItem: barVerticalStatus.verticalStreamingIconItem
    readonly property alias verticalObsIconItem: barVerticalStatus.verticalObsIconItem
    readonly property alias verticalKeyboardIconItem: barVerticalStatus.verticalKeyboardIconItem
    readonly property alias verticalUpdatesIconItem: barVerticalStatus.verticalUpdatesIconItem
    readonly property alias verticalBatteryIconItem: barVerticalStatus.verticalBatteryIconItem
    readonly property alias verticalNotificationIconItem: barVerticalStatus.verticalNotificationIconItem
    readonly property alias verticalMiddleItem: barVerticalCenter.verticalMiddleItem
    readonly property alias verticalMediaItem: barVerticalCenter.verticalMediaItem
    readonly property alias verticalCaptureItem: barVerticalCenter.verticalCaptureItem
    readonly property alias verticalPinItem: barVerticalCenter.verticalPinItem
    readonly property alias verticalCalendarIconItem: barVerticalCenter.verticalCalendarIconItem
    readonly property alias verticalWeatherIconItem: barVerticalCenter.verticalWeatherIconItem
    required property var barHost
    readonly property alias barVerticalCenterItem: barVerticalCenter
    readonly property alias barVerticalStatusItem: barVerticalStatus
    readonly property alias verticalAiIconItem: verticalAiIcon
    readonly property alias verticalControlCenterLogoItem: verticalControlCenterLogo
    readonly property alias verticalHardwareItem: verticalHardware
    readonly property alias verticalHardwareIconItem: verticalHardwareIcon
    readonly property alias verticalIdleLockIconItem: verticalIdleLockIcon
    readonly property alias verticalOverviewIconItem: verticalOverviewIcon
    readonly property alias verticalStartItem: verticalStart
    readonly property alias verticalWorkspacesItem: verticalWorkspaces
    id: verticalSurface
    anchors.fill: parent
    visible: host.verticalBar
    edge: host.barEdge
    background: host.notchLayout || host.centeredLayout || host.islandsLayout || host.dynamicLayout || host.dropLayout ? "transparent" : host.barBackground()
    radius: 0

    BarGestureArea {
        anchors.fill: parent
        hostWindow: barHost
        edge: host.barEdge
        onCandidateChanged: host.dragCandidate = candidate
        onPointerHeld: function(held) { host.barPointerHeld = held }
        onDoubleTapped: function(button) { host.barDoubleClick(button) }
        onDropped: function(edge) { host.updateBarSetting("edge", edge) }
    }

    Column {
        id: verticalStart
        // The fade lives in shownOpacity, so an Islands pill hiding this item under its card
        // overrides a plain binding and gets it back intact.
        property real shownOpacity: barHost.expanded ? 1 : 0
        opacity: shownOpacity
        enabled: barHost.expanded
        Behavior on shownOpacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
        y: barHost.islandsLayout ? host.screenGaps[0] + 4 : barHost.centeredLayout ? barHost.endPadding : 8
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
                onClicked: barHost.toggleControlCenter()
            }
            Item { width: 1; height: barHost.islandsLayout ? barHost.islandSpacing - 2 * host.workspaceItemSpacing + barHost.islandSurfaces.afterLogo : 0; visible: barHost.islandsLayout }
            VerticalBarIcon { host: verticalSurface.host; id: verticalOverviewIcon; icon: "󰕮"; tooltip: Eitr.I18n.tr("Overview"); open: true; clickable: true; onClicked: barHost.toggleOverview() }
            Repeater {
                model: host.workspaceRows(barHost.screen).length
                BarButton {
                    host: verticalSurface.host
                    text: host.workspaceLabel(index, barHost.screen)
                    tooltip: active ? "" : host.workspaceApps(host.workspaceEntry(index, barHost.screen).id)
                    visualStyle: host.workspaceStyle
                    active: host.workspaceActive(index + 1, barHost.screen)
                    width: host.workspaceItemSize; buttonHeight: host.workspaceItemSize; fontSize: 14; cornerRadius: 6; textOffsetY: 0
                    anchors.horizontalCenter: parent.horizontalCenter
                    onClicked: host.focusWorkspace(host.workspaceEntry(index, barHost.screen).number, barHost.screen)
                    onRightClicked: barHost.togglePanel(barHost.workspaceMenu)
                }
            }
        }
        Item { width: 1; height: barHost.islandsLayout ? barHost.islandSpacing - 2 * host.workspaceItemSpacing + barHost.islandSurfaces.afterWorkspaces : 0; visible: barHost.islandsLayout }
        Column {
            id: verticalHardware
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: host.workspaceItemSpacing
            VerticalBarIcon { host: verticalSurface.host; id: verticalAiIcon; icon: ""; iconSize: 16; tooltip: Eitr.I18n.tr("AI Usage"); open: true; clickable: true; onClicked: barHost.togglePanel(barHost.aiMenu) }
            VerticalBarIcon { host: verticalSurface.host; id: verticalHardwareIcon; icon: "󰍛"; iconSize: 18; tooltip: Eitr.I18n.tr("Hardware"); open: true; clickable: true; onClicked: barHost.togglePanel(barHost.hardwareMenu) }
            VerticalBarIcon { host: verticalSurface.host; id: verticalIdleLockIcon; icon: host.idleLockGlyph; iconSize: 17; tooltip: host.idleLockTooltip; open: true; clickable: true; onClicked: host.switchIdleLock() }
        }
    }

    BarVerticalCenter {
        id: barVerticalCenter
        host: verticalSurface.host
        barHost: verticalSurface.barHost
        barWeatherRef: barHost.barWeather
        calendarMenuRef: barHost.calendarMenu
        mediaMenuRef: barHost.mediaMenu
        mediaStripRef: barHost.mediaStrip
        obsMenuRef: barHost.obsMenu
        recordingMenuRef: barHost.recordingMenu
        weatherMenuRef: barHost.weatherMenu
    }

    BarVerticalStatus {
        id: barVerticalStatus
        host: verticalSurface.host
        barHost: verticalSurface.barHost
        batteryMenuRef: barHost.batteryMenu
        bluetoothMenuRef: barHost.bluetoothMenu
        brightnessMenuRef: barHost.brightnessMenu
        keyboardMenuRef: barHost.keyboardMenu
        notificationCenterRef: barHost.notificationCenter
        notificationIconRef: barHost.notificationIcon
        obsMenuRef: barHost.obsMenu
        remoteAccessServiceRef: barHost.remoteServiceRef
        streamingMenuRef: barHost.streamingMenu
        volumeMenuRef: barHost.volumeMenu
        wifiMenuRef: barHost.wifiMenu
    }
}
