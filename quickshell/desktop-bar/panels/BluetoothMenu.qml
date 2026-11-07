import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Bluetooth
import "../components/BluetoothDevices.js" as BluetoothDevices

ThemedPopup {
    id: menu
    implicitWidth: 468
    implicitHeight: Math.min(508, Math.max(248, groupColumn.height + 122))
    property var adapter: Bluetooth.defaultAdapter
    property bool showUnnamed: false
    property var groups: BluetoothDevices.groups([])
    readonly property var availableGroups: BluetoothDevices.groups(adapter && adapter.devices ? adapter.devices.values : [])
    // Lists rebuild only after the panel has unfolded (DockPanel.updateContent).
    onAvailableGroupsChanged: menu.updateContent(function() { menu.groups = menu.availableGroups; })
    Component.onCompleted: groups = availableGroups
    readonly property var sections: [
        {title: Eitr.I18n.tr("CONNECTED"), devices: groups.connected, empty: Eitr.I18n.tr("No devices")},
        {title: Eitr.I18n.tr("KNOWN DEVICES"), devices: groups.known, empty: Eitr.I18n.tr("No devices")},
        {title: Eitr.I18n.tr("SCANNED DEVICES"), devices: groups.other, unnamed: true,
         empty: discovery.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("No devices")}
    ]
    BluetoothConnector { id: bluetoothConnector; adapter: menu.adapter }
    BluetoothDiscovery { id: discovery; adapter: menu.adapter }
    onOpenedChanged: if (!opened) { discovery.stop(); bluetoothConnector.confirmingForget = null; }
    Item {
        anchors.fill: parent
        anchors.margins: 0
        Item {
            id: header
            width: parent.width
            height: 40
            PanelHeading { compact: menu.embedded; visible: !menu.embedded; anchors.verticalCenter: parent.verticalCenter; text: Eitr.I18n.tr("Bluetooth"); foreground: menu.foreground; accent: menu.accent; rune: "connectivity" }
            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                PanelButton {
                    id: scanButton
                    width: 34; height: 32
                    text: discovery.scanning ? "\uF04D" : "\uF021"; icon: true; compactIconBackground: true
                    foreground: menu.foreground
                    available: !!menu.adapter && menu.adapter.enabled
                    Accessible.name: discovery.scanning ? Eitr.I18n.tr("Stop scan") : Eitr.I18n.tr("Scan")
                    onClicked: discovery.toggle()
                    HoverHandler { id: scanHover }
                    BarTooltip { target: scanButton; hovered: scanHover.hovered; text: scanButton.Accessible.name; foreground: menu.foreground; background: menu.background }
                }
                PanelSwitch { checked: !!menu.adapter && menu.adapter.enabled; enabled: !!menu.adapter; foreground: menu.foreground; accent: menu.accent; onClicked: menu.adapter.enabled = checked }
            }
        }
        Flickable {
            anchors.top: header.bottom
            anchors.topMargin: 18
            anchors.bottom: parent.bottom
            width: parent.width
            contentHeight: groupColumn.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: groupColumn
                width: parent.width
                spacing: 20
                Text { visible: !menu.adapter || !menu.adapter.enabled; text: menu.adapter ? Eitr.I18n.tr("Bluetooth is off") : Eitr.I18n.tr("No Bluetooth adapter"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                Repeater {
                    model: menu.sections
                    Column {
                        id: section
                        required property var modelData
                        width: groupColumn.width
                        spacing: PanelStyle.selectionRowGap
                        PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
                        Text { text: section.modelData.title; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { visible: section.modelData.devices.length === 0; text: section.modelData.empty; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
                        // A click on the row pairs and connects; Disconnect and Forget sit inside it.
                        Repeater {
                            model: section.modelData.devices
                            BluetoothDeviceRow { width: groupColumn.width; connector: bluetoothConnector; foreground: menu.foreground }
                        }
                        ToggleRow {
                            width: groupColumn.width
                            visible: !!section.modelData.unnamed && menu.groups.unnamed.length > 0
                            text: Eitr.I18n.tr("Show unnamed devices")
                            description: Eitr.I18n.tr("Devices without a name: %1").arg(menu.groups.unnamed.length)
                            foreground: menu.foreground
                            accent: menu.accent
                            checked: menu.showUnnamed
                            onToggled: checked => menu.showUnnamed = checked
                        }
                        Repeater {
                            model: section.modelData.unnamed && menu.showUnnamed ? menu.groups.unnamed : []
                            BluetoothDeviceRow { width: groupColumn.width; connector: bluetoothConnector; foreground: menu.foreground }
                        }
                    }
                }
            }
        }
    }
}
