import ".."
import QtQuick
import Quickshell.Bluetooth
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "BluetoothDevices.js" as BluetoothDevices

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
    // The device a row click is pairing or connecting, and the step it is on.
    property var pendingDevice: null
    property string pendingStep: ""
    property bool sawConnecting: false
    property var failedDevice: null
    property string failure: ""
    property var confirmingForget: null
    readonly property bool powered: !!adapter && adapter.enabled
    readonly property var groups: BluetoothDevices.groups(adapter && adapter.devices ? adapter.devices.values : [])
    readonly property var stateLabels: ({pairing: Eitr.I18n.tr("Pairing..."), connecting: Eitr.I18n.tr("Connecting..."), connected: Eitr.I18n.tr("Connected"), paired: Eitr.I18n.tr("Paired"), "new": Eitr.I18n.tr("Not paired")})
    width: parent ? parent.width : 0
    spacing: 18
    onActiveChanged: if (!active) { discovery.stop(); confirmingForget = null; }
    function activate(device) {
        const action = BluetoothDevices.rowAction(device);
        if (!live || !powered || !action || pendingDevice) return;
        failedDevice = null; failure = ""; confirmingForget = null;
        pendingDevice = device; pendingStep = action; sawConnecting = false;
        deadline.restart();
        if (action === "pair") device.pair(); else device.connect();
    }
    function finish(error) {
        if (!pendingDevice) return;
        failedDevice = error ? pendingDevice : null;
        failure = error;
        pendingDevice = null; pendingStep = ""; sawConnecting = false;
        deadline.stop();
    }
    function cancelPairing(device) {
        if (live) device.cancelPair();
        if (pendingDevice === device) finish("");
    }
    function checkPairing() {
        if (!pendingDevice || pendingStep !== "pair" || pendingDevice.pairing) return;
        if (pendingDevice.paired) { pendingStep = "connect"; pendingDevice.connect(); }
        else finish(Eitr.I18n.tr("Pairing failed. Put the device in pairing mode and try again."));
    }
    function disconnect(device) { if (live) device.disconnect(); }
    function forget(device) {
        if (confirmingForget !== device) { confirmingForget = device; return; }
        confirmingForget = null;
        if (live) device.forget();
    }
    function dismiss() {
        if (confirmingForget) { confirmingForget = null; return true; }
        return false;
    }
    function label(device) {
        const state = BluetoothDevices.state(device, pendingDevice === device ? pendingStep : "");
        const text = state === "unnamed" ? String(device.address || "") : stateLabels[state];
        const battery = device.connected ? BluetoothDevices.batteryText(device) : "";
        return battery ? text + " · " + battery : text;
    }
    Connections {
        target: page.pendingDevice
        ignoreUnknownSignals: true
        function onPairingChanged() { Qt.callLater(page.checkPairing); }
        function onPairedChanged() { Qt.callLater(page.checkPairing); }
        function onConnectedChanged() { if (page.pendingDevice && page.pendingDevice.connected) page.finish(""); }
        function onStateChanged() {
            const state = page.pendingDevice ? page.pendingDevice.state : null;
            if (state === BluetoothDeviceState.Connecting) page.sawConnecting = true;
            else if (state === BluetoothDeviceState.Disconnected && page.sawConnecting && page.pendingStep === "connect")
                page.finish(Eitr.I18n.tr("Could not connect. Make sure the device is on and in range."));
        }
    }
    Timer {
        id: deadline
        interval: 30000
        onTriggered: page.finish(page.pendingStep === "pair" ? Eitr.I18n.tr("Pairing timed out.") : Eitr.I18n.tr("Could not connect. Make sure the device is on and in range."))
    }
    BluetoothDiscovery { id: discovery; adapter: page.adapter }
    component DeviceRow: ConnectionRow {
        id: deviceRow
        required property var modelData
        readonly property bool pending: page.pendingDevice === modelData
        objectName: "settings-bluetooth-row"
        text: BluetoothDevices.named(modelData) ? modelData.name : Eitr.I18n.tr("Unnamed device")
        glyph: BluetoothDevices.glyph(modelData)
        detail: page.label(modelData)
        error: page.failedDevice === modelData ? page.failure : ""
        selected: !!modelData.connected
        loading: pending || !!modelData.pairing
        activatable: page.powered && !page.pendingDevice && BluetoothDevices.rowAction(modelData) !== ""
        foreground: page.foreground
        onActivated: page.activate(modelData)
        PanelButton {
            visible: deviceRow.loading && (page.pendingStep === "pair" || !!deviceRow.modelData.pairing)
            width: 84; height: 28; foreground: page.foreground
            text: Eitr.I18n.tr("Cancel")
            onClicked: page.cancelPairing(deviceRow.modelData)
        }
        PanelButton {
            visible: !!deviceRow.modelData.connected
            width: 100; height: 28; foreground: page.foreground
            text: Eitr.I18n.tr("Disconnect"); available: page.powered
            onClicked: page.disconnect(deviceRow.modelData)
        }
        PanelButton {
            visible: !!deviceRow.modelData.paired && !deviceRow.loading
            width: 84; height: 28; foreground: page.foreground
            text: page.confirmingForget === deviceRow.modelData ? Eitr.I18n.tr("Confirm") : Eitr.I18n.tr("Forget")
            Accessible.name: page.confirmingForget === deviceRow.modelData ? Eitr.I18n.tr("Confirm removal") : Eitr.I18n.tr("Forget")
            onClicked: page.forget(deviceRow.modelData)
        }
    }
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
        Repeater { model: page.groups.connected; DeviceRow {} }
        SettingsText { visible: !page.groups.connected.length; text: Eitr.I18n.tr("No connected devices"); opacity: PanelStyle.secondaryTextOpacity }
    }
    ControlCard {
        visible: page.powered
        title: Eitr.I18n.tr("Known devices")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        spacing: PanelStyle.selectionRowGap
        Repeater { model: page.groups.known; DeviceRow {} }
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
        Repeater { model: page.groups.other; DeviceRow {} }
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
        Repeater { model: page.showUnnamed ? page.groups.unnamed : []; DeviceRow {} }
    }
}
