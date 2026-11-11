import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../components/BluetoothDevices.js" as BluetoothDevices

// Bluetooth opened in Drop's quick controls: connected and known devices, and a scan that
// starts when it opens, with the shared device rows (a click pairs and connects).
Column {
    id: detail
    required property var adapter
    required property color foreground
    required property bool shown
    readonly property var groups: BluetoothDevices.groups(adapter && adapter.devices ? adapter.devices.values : [])
    readonly property bool powered: !!adapter && adapter.enabled
    readonly property alias scanning: discovery.scanning
    function scan() { if (!discovery.scanning) discovery.toggle(); }
    BluetoothConnector { id: connector; adapter: detail.adapter }
    BluetoothDiscovery { id: discovery; adapter: detail.adapter }
    onShownChanged: {
        if (shown && powered) scan();
        else { discovery.stop(); connector.confirmingForget = null; }
    }
    onPoweredChanged: if (shown && powered) scan()
    spacing: 14

    Text {
        visible: !detail.powered
        text: detail.adapter ? Eitr.I18n.tr("Bluetooth is off") : Eitr.I18n.tr("No Bluetooth adapter")
        color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    Repeater {
        model: !detail.powered ? [] : [
            {title: Eitr.I18n.tr("CONNECTED"), devices: detail.groups.connected},
            {title: Eitr.I18n.tr("KNOWN DEVICES"), devices: detail.groups.known},
            {title: Eitr.I18n.tr("SCANNED DEVICES"), devices: detail.groups.other, scanned: true}
        ]
        Column {
            id: section
            required property var modelData
            width: detail.width; spacing: PanelStyle.selectionRowGap
            visible: modelData.devices.length > 0 || !!modelData.scanned
            Text { text: section.modelData.title; color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
            Text {
                visible: section.modelData.devices.length === 0
                text: discovery.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("No devices")
                color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize
            }
            Repeater {
                model: section.modelData.devices
                BluetoothDeviceRow { width: detail.width; connector: connector; foreground: detail.foreground }
            }
        }
    }
}
