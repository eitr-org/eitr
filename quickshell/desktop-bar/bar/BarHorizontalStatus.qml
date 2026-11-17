import ".."
import QtQuick
import Eitr as Eitr

Row {
    required property var host
    required property var barHost
    required property var barCaptureRef
    required property var batteryMenuRef
    required property var networkOwnerRef
    property var notificationIconRef: null
    required property var remoteAccessServiceRef
    required property var verticalBluetoothIconRef
    required property var verticalCaptureRef
    required property var verticalDisplayIconRef
    required property var verticalKeyboardIconRef
    required property var verticalObsIconRef
    required property var verticalStreamingIconRef
    required property var verticalVolumeIconRef
    required property var verticalWifiIconRef
    readonly property alias rightSideItem: rightSide
    readonly property alias statusToggleItem: statusToggle
    readonly property alias wifiMenuItem: wifiMenu
    readonly property alias bluetoothMenuItem: bluetoothMenu
    readonly property alias brightnessMenuItem: brightnessMenu
    readonly property alias volumeMenuItem: volumeMenu
    readonly property alias streamingMenuItem: streamingMenu
    readonly property alias keyboardMenuItem: keyboardMenu
    readonly property alias obsMenuItem: obsMenu
    readonly property alias recordingMenuItem: recordingMenu

    id: rightSide
    // The fade lives in shownOpacity, so an Islands pill hiding this item under its card
    // overrides a plain binding and gets it back intact.
    property real shownOpacity: barHost.expanded ? 1 : 0
    opacity: shownOpacity
    enabled: barHost.expanded
    Behavior on shownOpacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }

    spacing: rightSide.host.workspaceItemSpacing
    anchors.right: parent.right
    anchors.rightMargin: barHost.islandsLayout ? rightSide.host.screenGaps[1] + 4 : barHost.centeredLayout ? barHost.endPadding : 13
    anchors.verticalCenter: parent.verticalCenter

    Item {
        visible: rightItems.hasHideable && statusToggle.visible
        width: statusToggle.width
        height: statusToggle.height
        StatusIcon {
            host: rightSide.host
            id: statusToggle
            visible: !barHost.centeredLayout && !rightSide.host.notchLayout && !barHost.dynamicLayout && !barHost.dropLayout && !barHost.islandsLayout
            tooltip: rightSide.host.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")

            icon: rightSide.host.statusOpen ? "›" : "‹"
            open: rightItems.hasHideable
            clickable: true
            iconSize: 21
            glyphOffsetY: -1
            onClicked: rightSide.host.statusOpen = !rightSide.host.statusOpen
        }
    }

    BarZoneItems {
        id: rightItems
        host: rightSide.host
        barHost: rightSide.barHost
        zone: "right"
        vertical: false
        open: rightSide.host.iconsOpen
        onPanelRequested: function(plugin, panel, target) { barHost.openPluginPanel(plugin, panel, target); }
    }

    WifiMenu {
        id: wifiMenu
        readonly property string wifiZone: barHost.iconZone ? (barHost.iconZone("wifi") || "right") : "right"
        networkService: networkOwnerRef
        surfaceColor: rightSide.host.barBackground()
        target: barHost.iconTarget ? barHost.iconTarget("wifi", rightSide.host.verticalBar ? verticalWifiIconRef : notificationIconRef) : (rightSide.host.verticalBar ? verticalWifiIconRef : notificationIconRef)
        barEdge: rightSide.host.barEdge
        leftAligned: wifiZone === "left"
        centered: wifiZone === "clockStart" || wifiZone === "clockEnd"
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    BluetoothMenu {
        id: bluetoothMenu
        readonly property string bluetoothZone: barHost.iconZone ? (barHost.iconZone("bluetooth") || "right") : "right"
        surfaceColor: rightSide.host.barBackground()
        target: barHost.iconTarget ? barHost.iconTarget("bluetooth", rightSide.host.verticalBar ? verticalBluetoothIconRef : notificationIconRef) : (rightSide.host.verticalBar ? verticalBluetoothIconRef : notificationIconRef)
        barEdge: rightSide.host.barEdge
        leftAligned: bluetoothZone === "left"
        centered: bluetoothZone === "clockStart" || bluetoothZone === "clockEnd"
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    BrightnessMenu {
        id: brightnessMenu
        readonly property string displayZone: barHost.iconZone ? (barHost.iconZone("display") || "right") : "right"
        maximumHeight: barHost.screen.height - 70
        surfaceColor: rightSide.host.barBackground()
        target: barHost.iconTarget ? barHost.iconTarget("display", rightSide.host.verticalBar ? verticalDisplayIconRef : notificationIconRef) : (rightSide.host.verticalBar ? verticalDisplayIconRef : notificationIconRef)
        barEdge: rightSide.host.barEdge
        leftAligned: displayZone === "left"
        centered: displayZone === "clockStart" || displayZone === "clockEnd"
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
        onPrimarySelected: DisplayService.refresh()
    }

    AudioMenu {
        id: volumeMenu
        readonly property string audioZone: barHost.iconZone ? (barHost.iconZone("audio") || "right") : "right"
        surfaceColor: rightSide.host.barBackground()
        maximumHeight: barHost.screen.height - 70
        target: barHost.iconTarget ? barHost.iconTarget("audio", rightSide.host.verticalBar ? verticalVolumeIconRef : notificationIconRef) : (rightSide.host.verticalBar ? verticalVolumeIconRef : notificationIconRef)
        barEdge: rightSide.host.barEdge
        leftAligned: audioZone === "left"
        centered: audioZone === "clockStart" || audioZone === "clockEnd"
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    RemoteAccessMenu {
        id: streamingMenu
        readonly property string streamingZone: barHost.iconZone ? (barHost.iconZone("streaming") || "right") : "right"
        kind: "streaming"
        service: remoteAccessServiceRef
        onObservationChanged: observing => rightSide.host.remoteObservers += observing ? 1 : -1
        maximumHeight: barHost.screen.height - 70
        surfaceColor: rightSide.host.barBackground()
        target: barHost.iconTarget ? barHost.iconTarget("streaming", rightSide.host.verticalBar ? verticalStreamingIconRef : notificationIconRef) : (rightSide.host.verticalBar ? verticalStreamingIconRef : notificationIconRef)
        barEdge: rightSide.host.barEdge
        leftAligned: streamingZone === "left"
        centered: streamingZone === "clockStart" || streamingZone === "clockEnd"
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    KeyboardLayoutMenu {
        id: keyboardMenu
        readonly property string keyboardZone: barHost.iconZone ? (barHost.iconZone("keyboard") || "right") : "right"
        surfaceColor: rightSide.host.barBackground()
        target: barHost.iconTarget ? barHost.iconTarget("keyboard", rightSide.host.verticalBar ? verticalKeyboardIconRef : notificationIconRef) : (rightSide.host.verticalBar ? verticalKeyboardIconRef : notificationIconRef)
        barEdge: rightSide.host.barEdge
        leftAligned: keyboardZone === "left"
        centered: keyboardZone === "clockStart" || keyboardZone === "clockEnd"
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    ObsMenu {
        id: obsMenu
        readonly property string obsZone: barHost.iconZone ? (barHost.iconZone("obs") || "right") : "right"
        surfaceColor: rightSide.host.barBackground()
        onCaptureStarting: recordingMenu.opened = false
        target: barHost.iconTarget ? barHost.iconTarget("obs", rightSide.host.verticalBar ? verticalObsIconRef : notificationIconRef) : (rightSide.host.verticalBar ? verticalObsIconRef : notificationIconRef)
        barEdge: rightSide.host.barEdge
        leftAligned: obsZone === "left"
        centered: obsZone === "clockStart" || obsZone === "clockEnd"
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    RecordingMenu {
        id: recordingMenu
        surfaceColor: rightSide.host.barBackground()
        controller: obsMenu
        target: rightSide.host.verticalBar ? verticalCaptureRef : barCaptureRef
        barEdge: rightSide.host.barEdge
        centered: true
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }
}
