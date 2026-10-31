import ".."
import QtQuick
import QtQuick.Layouts

BarSection {
    required property var host
    readonly property alias rightSideItem: barHorizontalStatus.rightSideItem
    readonly property alias statusToggleItem: barHorizontalStatus.statusToggleItem
    readonly property alias wifiIconItem: barHorizontalStatus.wifiIconItem
    readonly property alias wifiMenuItem: barHorizontalStatus.wifiMenuItem
    readonly property alias bluetoothIconItem: barHorizontalStatus.bluetoothIconItem
    readonly property alias bluetoothMenuItem: barHorizontalStatus.bluetoothMenuItem
    readonly property alias brightnessIconItem: barHorizontalStatus.brightnessIconItem
    readonly property alias brightnessMenuItem: barHorizontalStatus.brightnessMenuItem
    readonly property alias volumeIconItem: barHorizontalStatus.volumeIconItem
    readonly property alias volumeMenuItem: barHorizontalStatus.volumeMenuItem
    readonly property alias tailscaleIconItem: barHorizontalStatus.tailscaleIconItem
    readonly property alias tailscaleMenuItem: barHorizontalStatus.tailscaleMenuItem
    readonly property alias streamingIconItem: barHorizontalStatus.streamingIconItem
    readonly property alias streamingMenuItem: barHorizontalStatus.streamingMenuItem
    readonly property alias obsIconItem: barHorizontalStatus.obsIconItem
    readonly property alias keyboardIconItem: barHorizontalStatus.keyboardIconItem
    readonly property alias keyboardMenuItem: barHorizontalStatus.keyboardMenuItem
    readonly property alias updatesIconItem: barHorizontalStatus.updatesIconItem
    readonly property alias batteryBarIconItem: barHorizontalStatus.batteryBarIconItem
    readonly property alias obsMenuItem: barHorizontalStatus.obsMenuItem
    readonly property alias recordingMenuItem: barHorizontalStatus.recordingMenuItem
    readonly property alias centerInfoItem: barHorizontalCenter.centerInfoItem
    readonly property alias barCaptureItem: barHorizontalCenter.barCaptureItem
    readonly property alias barPinItem: barHorizontalCenter.barPinItem
    readonly property alias mediaStripItem: barHorizontalCenter.mediaStripItem
    readonly property alias barWeatherItem: barHorizontalCenter.barWeatherItem
    readonly property alias calendarMenuItem: barHorizontalCenter.calendarMenuItem
    readonly property alias weatherMenuItem: barHorizontalCenter.weatherMenuItem
    required property var barHost
    readonly property alias aiMenuItem: aiMenu
    readonly property alias barGesturesItem: barGestures
    readonly property alias barHorizontalCenterItem: barHorizontalCenter
    readonly property alias barHorizontalStatusItem: barHorizontalStatus
    readonly property alias hardwareMenuItem: hardwareMenu
    readonly property alias leftGroupItem: leftGroup
    readonly property alias notificationIconItem: notificationIcon
    readonly property alias workspaceMenuItem: workspaceMenu
    id: surface
    anchors.fill: parent
    visible: !host.verticalBar
    edge: host.barEdge
    background: host.notchLayout || host.centeredLayout || host.islandsLayout ? "transparent" : host.barBackground()
    radius: 0

    BarGestureArea {
        id: barGestures
        anchors.fill: parent
        hostWindow: barHost
        edge: host.barEdge
        onCandidateChanged: host.dragCandidate = candidate
        onPointerHeld: function(held) { host.barPointerHeld = held }
        onDoubleTapped: function(button) { host.barDoubleClick(button) }
        onDropped: function(edge) { host.updateBarSetting("edge", edge) }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: barHost.islandsLayout ? host.screenGaps[3] + 4 : barHost.centeredLayout ? barHost.endPadding : 12
        anchors.rightMargin: 9
        spacing: 0

        BarLeftGroup {
            id: leftGroup
            host: surface.host
            barWindow: barHost
            styleMenu: workspaceMenu
            aiPanel: aiMenu
            hardwarePanel: hardwareMenu
            Layout.alignment: Qt.AlignVCenter
        }
        WorkspaceStyleMenu {
            id: workspaceMenu
            surfaceColor: host.barBackground()
            target: host.verticalBar ? barHost.verticalWorkspaces : leftGroup.workspaces
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
            maximumHeight: barHost.screen.height - 70
            target: host.verticalBar ? barHost.verticalHardwareIcon : leftGroup.hardwareIcon
            barEdge: host.barEdge
            accent: host.activeBg
            foreground: host.fg
            background: host.workspaceMenuBg
        }

        AiUsageMenu {
            id: aiMenu
            surfaceColor: host.barBackground()
            maximumHeight: barHost.screen.height - 70
            leftAligned: true
            target: host.verticalBar ? barHost.verticalAiIcon : leftGroup.aiIcon
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
            host: surface.host
            barHost: surface.barHost
            barCaptureRef: barHost.barCapture
            batteryMenuRef: barHost.batteryMenu
            networkOwnerRef: barHost.networkServiceRef
            notificationIconRef: notificationIcon
            remoteAccessServiceRef: barHost.remoteServiceRef
            verticalBluetoothIconRef: barHost.verticalBluetoothIcon
            verticalCaptureRef: barHost.verticalCapture
            verticalDisplayIconRef: barHost.verticalDisplayIcon
            verticalKeyboardIconRef: barHost.verticalKeyboardIcon
            verticalObsIconRef: barHost.verticalObsIcon
            verticalStreamingIconRef: barHost.verticalStreamingIcon
            verticalTailscaleIconRef: barHost.verticalTailscaleIcon
            verticalVolumeIconRef: barHost.verticalVolumeIcon
            verticalWifiIconRef: barHost.verticalWifiIcon
        }

    NotificationWidget {

        host: surface.host

        notificationService: barHost.notificationsRef
        id: notificationIcon
        onOpenRequested: barHost.togglePanel(barHost.notificationCenter)
        opacity: barHost.expanded ? 1 : 0
        enabled: barHost.expanded
        visible: !host.verticalBar
        anchors.right: parent.right
        anchors.rightMargin: barHost.islandsLayout ? host.screenGaps[1] + 4 : barHost.centeredLayout ? barHost.endPadding : 13
        anchors.verticalCenter: parent.verticalCenter
    }

    BarHorizontalCenter {
        id: barHorizontalCenter
        host: surface.host
        barHost: surface.barHost
        hardwareStatusRef: leftGroup.hardwareStatus
        mediaMenuRef: barHost.mediaMenu
        obsMenuRef: barHost.obsMenu
        recordingMenuRef: barHost.recordingMenu
        verticalCalendarIconRef: barHost.verticalCalendarIcon
        verticalWeatherIconRef: barHost.verticalWeatherIcon
        workspacesRef: leftGroup.workspaces
    }
}
