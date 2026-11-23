import ".."
import QtQuick
import QtQuick.Layouts

BarSection {
    readonly property alias clockPluginsItem: barHorizontalCenter.clockPluginsItem
    required property var host
    readonly property alias rightSideItem: barHorizontalStatus.rightSideItem
    readonly property alias statusToggleItem: barHorizontalStatus.statusToggleItem
    readonly property alias wifiMenuItem: barHorizontalStatus.wifiMenuItem
    readonly property alias bluetoothMenuItem: barHorizontalStatus.bluetoothMenuItem
    readonly property alias brightnessMenuItem: barHorizontalStatus.brightnessMenuItem
    readonly property alias volumeMenuItem: barHorizontalStatus.volumeMenuItem
    readonly property alias streamingMenuItem: barHorizontalStatus.streamingMenuItem
    readonly property alias keyboardMenuItem: barHorizontalStatus.keyboardMenuItem
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
    readonly property alias workspaceMenuItem: workspaceMenu
    id: surface
    anchors.fill: parent
    visible: !host.verticalBar
    edge: host.barEdge
    background: host.notchLayout || host.centeredLayout || host.islandsLayout || host.dynamicLayout || host.dropLayout ? "transparent" : host.barSurface()
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
            // Left-aligned in its own cell, without a filler after it: Dynamic moves the group
            // out and back, which would otherwise land it after the filler.
            Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
        }
        WorkspaceStyleMenu {
            workspaceNumbers: host.workspaceRows(barHost.screen).map(workspace => workspace.number)
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
            readonly property string hardwareZone: barHost.iconZone("hardware") || "left"
            pluginAvailable: PluginRegistry.hardwareEnabled === true
            surfaceColor: host.barBackground()
            maximumHeight: barHost.screen.height - 70
            leftAligned: hardwareZone === "left"
            centered: hardwareZone === "clockStart" || hardwareZone === "clockEnd"
            target: barHost.iconTarget("hardware", null, null)
            barEdge: host.barEdge
            accent: host.activeBg
            foreground: host.fg
            background: host.workspaceMenuBg
        }

        AiUsageMenu {
            id: aiMenu
            readonly property string aiZone: barHost.iconZone("ai") || "left"
            pluginAvailable: PluginRegistry.aiUsageEnabled === true
            surfaceColor: host.barBackground()
            maximumHeight: barHost.screen.height - 70
            leftAligned: aiZone === "left"
            centered: aiZone === "clockStart" || aiZone === "clockEnd"
            target: barHost.iconTarget("ai", null, null)
            barEdge: host.barEdge
            accent: host.activeBg
            foreground: host.fg
            background: host.workspaceMenuBg
        }

    }

        BarHorizontalStatus {
            id: barHorizontalStatus
            host: surface.host
            barHost: surface.barHost
            barCaptureRef: barHost.barCapture
            batteryMenuRef: barHost.batteryMenu
            networkOwnerRef: barHost.networkServiceRef
            remoteAccessServiceRef: barHost.remoteServiceRef
            verticalBluetoothIconRef: barHost.verticalBluetoothIcon
            verticalCaptureRef: barHost.verticalCapture
            verticalDisplayIconRef: barHost.verticalDisplayIcon
            verticalKeyboardIconRef: barHost.verticalKeyboardIcon
            verticalObsIconRef: barHost.verticalObsIcon
            verticalStreamingIconRef: barHost.verticalStreamingIcon
            verticalVolumeIconRef: barHost.verticalVolumeIcon
            verticalWifiIconRef: barHost.verticalWifiIcon
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
