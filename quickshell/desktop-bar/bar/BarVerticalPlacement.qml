import ".."
import QtQuick
import Eitr as Eitr

BarSection {
    readonly property alias clockPluginsItem: barVerticalCenter.clockPluginsItem
    required property var host
    readonly property alias verticalEndItem: barVerticalStatus.verticalEndItem
    readonly property alias verticalMiddleItem: barVerticalCenter.verticalMiddleItem
    readonly property alias verticalMediaItem: barVerticalCenter.verticalMediaItem
    readonly property alias verticalCaptureItem: barVerticalCenter.verticalCaptureItem
    readonly property alias verticalPinItem: barVerticalCenter.verticalPinItem
    readonly property alias verticalCalendarIconItem: barVerticalCenter.verticalCalendarIconItem
    readonly property alias verticalWeatherIconItem: barVerticalCenter.verticalWeatherIconItem
    required property var barHost
    readonly property alias barVerticalCenterItem: barVerticalCenter
    readonly property alias barVerticalStatusItem: barVerticalStatus
    readonly property alias verticalControlCenterLogoItem: verticalControlCenterLogo
    readonly property alias verticalHardwareItem: verticalHardware
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
            Item { width: 1; height: barHost.islandsLayout ? barHost.islandSpacing - 2 * host.workspaceItemSpacing + (barHost.islandSurfaces ? barHost.islandSurfaces.afterLogo : 0) : 0; visible: barHost.islandsLayout }
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
        Item { width: 1; height: barHost.islandsLayout ? barHost.islandSpacing - 2 * host.workspaceItemSpacing + (barHost.islandSurfaces ? barHost.islandSurfaces.afterWorkspaces : 0) : 0; visible: barHost.islandsLayout && verticalLeftItems.height > 0 }
        Column {
            id: verticalHardware
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: host.workspaceItemSpacing
            visible: verticalLeftItems.height > 0
            BarZoneItems {
                id: verticalLeftItems
                host: verticalSurface.host
                barHost: verticalSurface.barHost
                zone: "left"
                vertical: true
                observing: !barHost.dynamicLayout || (barHost.dynamicSurfaces ? barHost.dynamicSurfaces.leadingIsland.expanded : false)
                open: !barHost.dropLayout && barHost.expanded
                anchors.horizontalCenter: parent.horizontalCenter
                onPanelRequested: function(plugin, panel, target) { barHost.openPluginPanel(plugin, panel, target); }
            }

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
