import ".."
import QtQuick
import Quickshell.Bluetooth
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../components/BluetoothDevices.js" as BluetoothDevices

// Settings > Connections > Bluetooth: the same BlueZ adapter, actions and discovery as the
// bar's Bluetooth panel, laid out like the Wi-Fi tab. Clicking a row pairs and connects.
Column {
    id: page
    objectName: "settings-bluetooth-page"
    required property color foreground
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    property var adapter: Bluetooth.defaultAdapter
    property bool showUnnamed: false
    readonly property bool powered: bluetoothConnector.powered
    readonly property alias pendingDevice: bluetoothConnector.pendingDevice
    readonly property alias pendingStep: bluetoothConnector.pendingStep
    readonly property var groups: BluetoothDevices.groups(adapter && adapter.devices ? adapter.devices.values : [])
    width: parent ? parent.width : 0
    spacing: 18
    onActiveChanged: if (!active) { discovery.stop(); bluetoothConnector.confirmingForget = null; }
    function dismiss() { return bluetoothConnector.dismiss(); }
    BluetoothConnector { id: bluetoothConnector; adapter: page.adapter; live: page.live }
    BluetoothDiscovery { id: discovery; adapter: page.adapter }
    ToggleRow {
        objectName: "settings-bluetooth-power"
        text: Eitr.I18n.tr("Bluetooth")
        description: page.adapter ? Eitr.I18n.tr("Turn Bluetooth on or off") + (page.adapter.name ? " · " + page.adapter.name : "") : Eitr.I18n.tr("No Bluetooth adapter")
        foreground: page.foreground
        accent: page.accent
        checked: page.powered
        available: !!page.adapter
        onToggled: checked => { if (page.live) page.adapter.enabled = checked; }
    }
    SettingsText {
        visible: !!page.adapter && !page.powered
        text: Eitr.I18n.tr("Bluetooth is off")
        opacity: PanelStyle.secondaryTextOpacity
    }
    ControlCard {
        visible: page.powered
        title: Eitr.I18n.tr("Connected devices")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        spacing: PanelStyle.selectionRowGap
        Repeater { model: page.groups.connected; BluetoothDeviceRow { connector: bluetoothConnector; foreground: page.foreground } }
        SettingsText { visible: !page.groups.connected.length; text: Eitr.I18n.tr("No connected devices"); opacity: PanelStyle.secondaryTextOpacity }
    }
    ControlCard {
        visible: page.powered
        title: Eitr.I18n.tr("Known devices")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        spacing: PanelStyle.selectionRowGap
        Repeater { model: page.groups.known; BluetoothDeviceRow { connector: bluetoothConnector; foreground: page.foreground } }
        SettingsText { visible: !page.groups.known.length; text: Eitr.I18n.tr("No paired devices"); opacity: PanelStyle.secondaryTextOpacity }
    }
    ControlCard {
        objectName: "settings-bluetooth-other"
        visible: page.powered
        title: Eitr.I18n.tr("Other devices")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        spacing: PanelStyle.selectionRowGap
        headerActions: PanelButton {
            objectName: "settings-bluetooth-scan"
            width: 84; height: 26
            text: discovery.scanning ? Eitr.I18n.tr("Stop") : Eitr.I18n.tr("Scan")
            leadingIcon: "\uF021"; leadingSpin: discovery.scanning
            textSize: PanelStyle.captionSize
            foreground: page.foreground
            available: page.powered
            Accessible.name: discovery.scanning ? Eitr.I18n.tr("Stop scan") : Eitr.I18n.tr("Scan")
            onClicked: if (page.live) discovery.toggle()
        }
        Repeater { model: page.groups.other; BluetoothDeviceRow { connector: bluetoothConnector; foreground: page.foreground } }
        SettingsText {
            visible: !page.groups.other.length
            text: discovery.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("Press Scan to look for nearby devices.")
            opacity: PanelStyle.secondaryTextOpacity
        }
        ToggleRow {
            objectName: "settings-bluetooth-unnamed"
            visible: page.groups.unnamed.length > 0
            text: Eitr.I18n.tr("Show unnamed devices")
            description: Eitr.I18n.tr("Devices without a name: %1").arg(page.groups.unnamed.length)
            foreground: page.foreground
            accent: page.accent
            checked: page.showUnnamed
            onToggled: checked => page.showUnnamed = checked
        }
        Repeater { model: page.showUnnamed ? page.groups.unnamed : []; BluetoothDeviceRow { connector: bluetoothConnector; foreground: page.foreground } }
    }
}
