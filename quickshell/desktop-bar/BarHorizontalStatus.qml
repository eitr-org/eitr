import QtQuick
import Eitr as Eitr

Row {
    required property var host
    required property var barHost
    required property var barCaptureRef
    required property var batteryMenuRef
    required property var networkOwnerRef
    required property var notificationIconRef
    required property var remoteAccessServiceRef
    required property var verticalBluetoothIconRef
    required property var verticalCaptureRef
    required property var verticalDisplayIconRef
    required property var verticalKeyboardIconRef
    required property var verticalObsIconRef
    required property var verticalStreamingIconRef
    required property var verticalTailscaleIconRef
    required property var verticalVolumeIconRef
    required property var verticalWifiIconRef
    readonly property alias rightSideItem: rightSide
    readonly property alias statusToggleItem: statusToggle
    readonly property alias wifiIconItem: wifiIcon
    readonly property alias wifiMenuItem: wifiMenu
    readonly property alias bluetoothIconItem: bluetoothIcon
    readonly property alias bluetoothMenuItem: bluetoothMenu
    readonly property alias brightnessIconItem: brightnessIcon
    readonly property alias brightnessMenuItem: brightnessMenu
    readonly property alias volumeIconItem: volumeIcon
    readonly property alias volumeMenuItem: volumeMenu
    readonly property alias tailscaleIconItem: tailscaleIcon
    readonly property alias tailscaleMenuItem: tailscaleMenu
    readonly property alias streamingIconItem: streamingIcon
    readonly property alias streamingMenuItem: streamingMenu
    readonly property alias obsIconItem: obsIcon
    readonly property alias keyboardIconItem: keyboardIcon
    readonly property alias keyboardMenuItem: keyboardMenu
    readonly property alias updatesIconItem: updatesIcon
    readonly property alias batteryBarIconItem: batteryBarIcon
    readonly property alias obsMenuItem: obsMenu
    readonly property alias recordingMenuItem: recordingMenu

    id: rightSide
    opacity: barHost.expanded ? 1 : 0
    enabled: barHost.expanded
    Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }

    spacing: rightSide.host.workspaceItemSpacing
    anchors.right: notificationIconRef.left
    anchors.rightMargin: rightSide.host.workspaceItemSpacing
    anchors.verticalCenter: parent.verticalCenter

    StatusIcon {

        host: rightSide.host
        id: statusToggle
        visible: !barHost.centeredLayout && !rightSide.host.notchLayout
        tooltip: rightSide.host.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")

        icon: rightSide.host.statusOpen ? "›" : "‹"
        open: true
        clickable: true
        iconSize: 21
        glyphOffsetY: -1
        onClicked: rightSide.host.statusOpen = !rightSide.host.statusOpen
    }

    PluginBarItems {
        foreground: rightSide.host.fg; background: rightSide.host.barBackground(); accent: rightSide.host.activeBg
        open: rightSide.host.iconsOpen; slotSize: rightSide.host.workspaceItemSize; slotSpacing: rightSide.host.workspaceItemSpacing
        onPanelRequested: function(plugin, panel, target) { barHost.openPluginPanel(plugin, panel, target); }
    }

    StatusCommand {

        host: rightSide.host
        id: wifiIcon
        text: rightSide.host.wifiGlyph
        hoverLabel: "WiFi"
        fontSize: 16
        open: rightSide.host.iconsOpen
        slotWidth: rightSide.host.workspaceItemSize
        fixedWidth: rightSide.host.workspaceItemSize
        clickable: true
        onClicked: barHost.togglePanel(wifiMenu)
        onOpenChanged: if (!open) wifiMenu.opened = false
    }

    WifiMenu {
        id: wifiMenu
        networkService: networkOwnerRef
        surfaceColor: rightSide.host.barBackground()
        target: rightSide.host.verticalBar ? verticalWifiIconRef : (rightSide.host.iconsOpen ? wifiIcon : notificationIconRef)
        barEdge: rightSide.host.barEdge
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    StatusIcon {

        host: rightSide.host
        id: bluetoothIcon
        icon: "󰂯"
        tooltip: Eitr.I18n.tr("Bluetooth")
        open: rightSide.host.iconsOpen
        clickable: true
        onClicked: barHost.togglePanel(bluetoothMenu)
        onOpenChanged: if (!open) bluetoothMenu.opened = false
    }

    BluetoothMenu {
        id: bluetoothMenu
        surfaceColor: rightSide.host.barBackground()
        target: rightSide.host.verticalBar ? verticalBluetoothIconRef : (rightSide.host.iconsOpen ? bluetoothIcon : notificationIconRef)
        barEdge: rightSide.host.barEdge
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    StatusIcon {

        host: rightSide.host
        id: brightnessIcon
        icon: "󰍹"
        tooltip: Eitr.I18n.tr("Display")
        open: rightSide.host.iconsOpen
        clickable: true
        onClicked: barHost.togglePanel(brightnessMenu)
        onOpenChanged: if (!open) brightnessMenu.opened = false
    }

    BrightnessMenu {
        id: brightnessMenu
        maximumHeight: barHost.screen.height - 70
        surfaceColor: rightSide.host.barBackground()
        target: rightSide.host.verticalBar ? verticalDisplayIconRef : (rightSide.host.iconsOpen ? brightnessIcon : notificationIconRef)
        barEdge: rightSide.host.barEdge
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
        onPrimarySelected: DisplayService.refresh()
    }

    StatusIcon {

        host: rightSide.host
        id: volumeIcon
        icon: "\u{F02CE}"
        tooltip: Eitr.I18n.tr("Audio/Mic")
        open: rightSide.host.iconsOpen
        clickable: true
        onClicked: barHost.togglePanel(volumeMenu)
        onOpenChanged: if (!open) volumeMenu.opened = false
    }

    AudioMenu {
        id: volumeMenu
        surfaceColor: rightSide.host.barBackground()
        maximumHeight: barHost.screen.height - 70
        target: rightSide.host.verticalBar ? verticalVolumeIconRef : (rightSide.host.iconsOpen ? volumeIcon : notificationIconRef)
        barEdge: rightSide.host.barEdge
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    StatusIcon {

        host: rightSide.host
        id: tailscaleIcon
        visible: remoteAccessServiceRef.allowed
        icon: "󰌘"
        tooltip: "Tailscale"
        open: rightSide.host.iconsOpen
        clickable: true
        onClicked: barHost.togglePanel(tailscaleMenu)
        onOpenChanged: if (!open) tailscaleMenu.opened = false
    }
    RemoteAccessMenu {
        id: tailscaleMenu
        kind: "tailscale"
        service: remoteAccessServiceRef
        onObservationChanged: observing => rightSide.host.remoteObservers += observing ? 1 : -1
        maximumHeight: barHost.screen.height - 70
        surfaceColor: rightSide.host.barBackground()
        target: rightSide.host.verticalBar ? verticalTailscaleIconRef : tailscaleIcon
        barEdge: rightSide.host.barEdge
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }
    StatusIcon {
        host: rightSide.host
        id: streamingIcon
        visible: remoteAccessServiceRef.allowed
        icon: "󰢹"
        tooltip: Eitr.I18n.tr("Streaming")
        open: rightSide.host.iconsOpen
        clickable: true
        onClicked: barHost.togglePanel(streamingMenu)
        onOpenChanged: if (!open) streamingMenu.opened = false
    }
    RemoteAccessMenu {
        id: streamingMenu
        kind: "streaming"
        service: remoteAccessServiceRef
        onObservationChanged: observing => rightSide.host.remoteObservers += observing ? 1 : -1
        maximumHeight: barHost.screen.height - 70
        surfaceColor: rightSide.host.barBackground()
        target: rightSide.host.verticalBar ? verticalStreamingIconRef : streamingIcon
        barEdge: rightSide.host.barEdge
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    StatusIcon {

        host: rightSide.host
        id: obsIcon
        icon: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? "󰏤" : "󰑋") : "󰻂"
        iconSize: obsMenu.obsState.recording && !obsMenu.obsState.paused ? 22 : 16
        tooltip: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? Eitr.I18n.tr("Recording paused") : Eitr.I18n.tr("Recording")) : Eitr.I18n.tr("OBS Studio")
        open: rightSide.host.iconsOpen
        clickable: true
        onClicked: barHost.togglePanel(obsMenu)
        onOpenChanged: if (!open) obsMenu.opened = false
    }

    StatusIcon {

        host: rightSide.host
        id: keyboardIcon
        // Like macOS's input menu: the active layout's code, shown
        // only when there is more than one layout to switch between.
        icon: keyboardMenu.activeCode || "󰌌"
        iconSize: 11
        tooltip: keyboardMenu.activeLabel ? Eitr.I18n.tr("Keyboard · {layout}", {layout: keyboardMenu.activeLabel}) : Eitr.I18n.tr("Keyboard")
        open: rightSide.host.iconsOpen && keyboardMenu.layouts.length > 1
        clickable: true
        onClicked: barHost.togglePanel(keyboardMenu)
        onOpenChanged: if (!open) keyboardMenu.opened = false
    }

    KeyboardLayoutMenu {
        id: keyboardMenu
        surfaceColor: rightSide.host.barBackground()
        target: rightSide.host.verticalBar ? verticalKeyboardIconRef : (rightSide.host.iconsOpen ? keyboardIcon : notificationIconRef)
        barEdge: rightSide.host.barEdge
        accent: rightSide.host.activeBg
        foreground: rightSide.host.fg
        background: rightSide.host.workspaceMenuBg
    }

    StatusIcon {

        host: rightSide.host
        id: updatesIcon
        icon: rightSide.host.updatesIcon
        iconSize: 17
        spinning: rightSide.host.updates.checking
        tooltip: rightSide.host.updatesTooltip
        open: rightSide.host.iconsOpen
        clickable: true
        rightClickable: true
        onClicked: function(button) {
            if (button === Qt.RightButton) rightSide.host.checkUpdates();
            else rightSide.host.openSystemUpdate();
        }
    }

    StatusIcon {

        host: rightSide.host
        id: batteryBarIcon
        icon: rightSide.host.batteryIcon
        tooltip: Math.round(rightSide.host.battery.percent) + "% · " + rightSide.host.battery.status
        open: rightSide.host.battery.available; visible: rightSide.host.battery.available
        clickable: true; onClicked: barHost.togglePanel(batteryMenuRef)
    }

    ObsMenu {
        id: obsMenu
        surfaceColor: rightSide.host.barBackground()
        onCaptureStarting: recordingMenu.opened = false
        target: rightSide.host.verticalBar ? verticalObsIconRef : obsIcon
        barEdge: rightSide.host.barEdge
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
