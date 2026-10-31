import QtQuick
import Eitr as Eitr

Column {
    required property var host
    required property var barHost
    required property var batteryMenuRef
    required property var bluetoothMenuRef
    required property var brightnessMenuRef
    required property var keyboardMenuRef
    required property var notificationCenterRef
    required property var notificationIconRef
    required property var obsMenuRef
    required property var remoteAccessServiceRef
    required property var streamingMenuRef
    required property var tailscaleMenuRef
    required property var volumeMenuRef
    required property var wifiMenuRef
    readonly property alias verticalEndItem: verticalEnd
    readonly property alias verticalWifiIconItem: verticalWifiIcon
    readonly property alias verticalBluetoothIconItem: verticalBluetoothIcon
    readonly property alias verticalDisplayIconItem: verticalDisplayIcon
    readonly property alias verticalVolumeIconItem: verticalVolumeIcon
    readonly property alias verticalTailscaleIconItem: verticalTailscaleIcon
    readonly property alias verticalStreamingIconItem: verticalStreamingIcon
    readonly property alias verticalObsIconItem: verticalObsIcon
    readonly property alias verticalKeyboardIconItem: verticalKeyboardIcon
    readonly property alias verticalUpdatesIconItem: verticalUpdatesIcon
    readonly property alias verticalBatteryIconItem: verticalBatteryIcon
    readonly property alias verticalNotificationIconItem: verticalNotificationIcon

    id: verticalEnd
    opacity: barHost.expanded ? 1 : 0
    enabled: barHost.expanded
    Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
    anchors.bottom: parent.bottom
    anchors.bottomMargin: barHost.islandsLayout ? verticalEnd.host.screenGaps[2] + 4 : barHost.centeredLayout ? barHost.endPadding : 8
    anchors.horizontalCenter: parent.horizontalCenter
    spacing: verticalEnd.host.workspaceItemSpacing
    VerticalBarIcon {
        host: verticalEnd.host
        icon: verticalEnd.host.statusOpen ? "⌄" : "⌃"
        visible: !barHost.centeredLayout && !verticalEnd.host.notchLayout
        tooltip: verticalEnd.host.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")
        open: true; clickable: true
        onClicked: verticalEnd.host.statusOpen = !verticalEnd.host.statusOpen
    }
    PluginBarItems {
        foreground: verticalEnd.host.fg; background: verticalEnd.host.barBackground(); accent: verticalEnd.host.activeBg
        vertical: true; open: verticalEnd.host.iconsOpen; slotSize: verticalEnd.host.workspaceItemSize; slotSpacing: verticalEnd.host.workspaceItemSpacing
        onPanelRequested: function(plugin, panel, target) { barHost.openPluginPanel(plugin, panel, target); }
    }
    StatusCommand {
        host: verticalEnd.host
        id: verticalWifiIcon
        text: verticalEnd.host.wifiGlyph
        hoverLabel: "WiFi"; fontSize: 16
        open: verticalEnd.host.iconsOpen; height: open ? 24 : 0; fixedWidth: 56; clickable: true
        anchors.horizontalCenter: parent.horizontalCenter
        onClicked: barHost.togglePanel(wifiMenuRef)
        onOpenChanged: if (!open) wifiMenuRef.opened = false
    }
    VerticalBarIcon { host: verticalEnd.host; id: verticalBluetoothIcon; icon: "󰂯"; tooltip: Eitr.I18n.tr("Bluetooth"); open: verticalEnd.host.iconsOpen; clickable: true; onClicked: barHost.togglePanel(bluetoothMenuRef); onOpenChanged: if (!open) bluetoothMenuRef.opened = false }
    VerticalBarIcon { host: verticalEnd.host; id: verticalDisplayIcon; icon: "󰍹"; tooltip: Eitr.I18n.tr("Display"); open: verticalEnd.host.iconsOpen; clickable: true; onClicked: barHost.togglePanel(brightnessMenuRef); onOpenChanged: if (!open) brightnessMenuRef.opened = false }
    VerticalBarIcon { host: verticalEnd.host; id: verticalVolumeIcon; icon: "\u{F02CE}"; tooltip: Eitr.I18n.tr("Audio/Mic"); open: verticalEnd.host.iconsOpen; clickable: true; onClicked: barHost.togglePanel(volumeMenuRef); onOpenChanged: if (!open) volumeMenuRef.opened = false }
    VerticalBarIcon { host: verticalEnd.host; id: verticalTailscaleIcon; visible: remoteAccessServiceRef.allowed; icon: "󰌘"; tooltip: "Tailscale"; open: verticalEnd.host.iconsOpen; clickable: true; onClicked: barHost.togglePanel(tailscaleMenuRef); onOpenChanged: if (!open) tailscaleMenuRef.opened = false }
    VerticalBarIcon { host: verticalEnd.host; id: verticalStreamingIcon; visible: remoteAccessServiceRef.allowed; icon: "󰢹"; tooltip: Eitr.I18n.tr("Streaming"); open: verticalEnd.host.iconsOpen; clickable: true; onClicked: barHost.togglePanel(streamingMenuRef); onOpenChanged: if (!open) streamingMenuRef.opened = false }
    VerticalBarIcon { host: verticalEnd.host; id: verticalObsIcon; icon: obsMenuRef.obsState.recording ? (obsMenuRef.obsState.paused ? "󰏤" : "󰑋") : "󰻂"; iconSize: obsMenuRef.obsState.recording && !obsMenuRef.obsState.paused ? 22 : 16; tooltip: obsMenuRef.obsState.recording ? (obsMenuRef.obsState.paused ? Eitr.I18n.tr("Recording paused") : Eitr.I18n.tr("Recording")) : Eitr.I18n.tr("OBS Studio"); open: verticalEnd.host.iconsOpen; clickable: true; onClicked: barHost.togglePanel(obsMenuRef); onOpenChanged: if (!open) obsMenuRef.opened = false }
    VerticalBarIcon { host: verticalEnd.host; id: verticalKeyboardIcon; icon: keyboardMenuRef.activeCode || "󰌌"; iconSize: 11; tooltip: keyboardMenuRef.activeLabel ? Eitr.I18n.tr("Keyboard · {layout}", {layout: keyboardMenuRef.activeLabel}) : Eitr.I18n.tr("Keyboard"); open: verticalEnd.host.iconsOpen && keyboardMenuRef.layouts.length > 1; clickable: true; onClicked: barHost.togglePanel(keyboardMenuRef); onOpenChanged: if (!open) keyboardMenuRef.opened = false }
    VerticalBarIcon {
        host: verticalEnd.host
        id: verticalUpdatesIcon
        icon: verticalEnd.host.updatesIcon; iconSize: 17; spinning: verticalEnd.host.updates.checking
        tooltip: verticalEnd.host.updatesTooltip; open: verticalEnd.host.iconsOpen
        clickable: true; rightClickable: true
        onClicked: function(button) { if (button === Qt.RightButton) verticalEnd.host.checkUpdates(); else verticalEnd.host.openSystemUpdate(); }
    }
    VerticalBarIcon { host: verticalEnd.host; id: verticalBatteryIcon; icon: verticalEnd.host.batteryIcon; tooltip: Math.round(verticalEnd.host.battery.percent) + "% · " + verticalEnd.host.battery.status; open: verticalEnd.host.battery.available; visible: verticalEnd.host.battery.available; clickable: true; onClicked: barHost.togglePanel(batteryMenuRef) }
    VerticalBarIcon {
        host: verticalEnd.host
        id: verticalNotificationIcon
        icon: notificationIconRef.text; tooltip: Eitr.I18n.tr("Notifications"); open: true; clickable: true
        onClicked: barHost.togglePanel(notificationCenterRef)
    }
}
