import ".."
import QtQuick
import Quickshell.Bluetooth
import Eitr as Eitr
import "BluetoothDevices.js" as BluetoothDevices

// What a click on a Bluetooth device row does, shared by Settings and the bar panel:
// pair then connect a new device, connect a paired one, with progress, a 30 s deadline
// and a plain error on the row that failed.
Item {
    id: connector
    property var adapter: Bluetooth.defaultAdapter
    property bool live: true
    // The device a row click is pairing or connecting, and the step it is on.
    property var pendingDevice: null
    property string pendingStep: ""
    property bool sawConnecting: false
    property var failedDevice: null
    property string failure: ""
    property var confirmingForget: null
    readonly property bool powered: !!adapter && adapter.enabled
    readonly property var stateLabels: ({pairing: Eitr.I18n.tr("Pairing..."), connecting: Eitr.I18n.tr("Connecting..."), connected: Eitr.I18n.tr("Connected"), paired: Eitr.I18n.tr("Paired"), "new": Eitr.I18n.tr("Not paired")})
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
        target: connector.pendingDevice
        ignoreUnknownSignals: true
        function onPairingChanged() { Qt.callLater(connector.checkPairing); }
        function onPairedChanged() { Qt.callLater(connector.checkPairing); }
        function onConnectedChanged() { if (connector.pendingDevice && connector.pendingDevice.connected) connector.finish(""); }
        function onStateChanged() {
            const state = connector.pendingDevice ? connector.pendingDevice.state : null;
            if (state === BluetoothDeviceState.Connecting) connector.sawConnecting = true;
            else if (state === BluetoothDeviceState.Disconnected && connector.sawConnecting && connector.pendingStep === "connect")
                connector.finish(Eitr.I18n.tr("Could not connect. Make sure the device is on and in range."));
        }
    }
    Timer {
        id: deadline
        interval: 30000
        onTriggered: connector.finish(connector.pendingStep === "pair" ? Eitr.I18n.tr("Pairing timed out.") : Eitr.I18n.tr("Could not connect. Make sure the device is on and in range."))
    }
}
