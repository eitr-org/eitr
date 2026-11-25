import ".."
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
    property var notificationIconRef: null
    required property var obsMenuRef
    required property var remoteAccessServiceRef
    required property var streamingMenuRef
    required property var volumeMenuRef
    required property var wifiMenuRef
    readonly property alias statusToggleItem: verticalStatusToggle
    readonly property alias verticalEndItem: verticalEnd

    readonly property alias rightZone: verticalRightItems

    id: verticalEnd
    // The fade lives in shownOpacity, so an Islands pill hiding this item under its card
    // overrides a plain binding and gets it back intact.
    property real shownOpacity: barHost.expanded ? 1 : 0
    opacity: shownOpacity
    enabled: barHost.expanded
    Behavior on shownOpacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
    anchors.bottom: parent.bottom
    anchors.bottomMargin: barHost.islandsLayout ? verticalEnd.host.screenGaps[2] + 4 : barHost.centeredLayout ? barHost.endPadding : 8
    anchors.horizontalCenter: parent.horizontalCenter
    spacing: verticalEnd.host.workspaceItemSpacing

    StatusIcon {
        host: verticalEnd.host
        id: verticalStatusToggle
        icon: verticalEnd.host.statusOpen ? "⌄" : "⌃"
        visible: verticalEnd.host.statusCollapsible && verticalRightItems.hasHideable
        tooltip: verticalEnd.host.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")
        open: true
        height: 24
        anchors.horizontalCenter: parent.horizontalCenter
        clickable: true
        onClicked: verticalEnd.host.statusOpen = !verticalEnd.host.statusOpen
    }

    BarZoneItems {
        id: verticalRightItems
        host: verticalEnd.host
        barHost: verticalEnd.barHost
        zone: "right"
        vertical: true
        open: verticalEnd.host.iconsOpen
        anchors.horizontalCenter: parent.horizontalCenter
        onPanelRequested: function(plugin, panel, target) { barHost.openPluginPanel(plugin, panel, target); }
    }
}
