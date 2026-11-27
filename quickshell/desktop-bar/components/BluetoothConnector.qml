import ".."
import QtQuick
import Quickshell.Bluetooth
import Eitr as Eitr
import "BluetoothDevices.js" as BluetoothDevices

// What a click on a Bluetooth device row does, shared by Settings and the bar panel:
// pair then connect a new device, connect a paired one, with progress, a 30 s deadline
// and a plain error on the row that failed. Eitr runs no BlueZ pairing agent, so the adapter
// stays non-pairable and BlueZ would drop an unbonded pairing on the first disconnect: a
// pairing makes the adapter pairable until it finishes and trusts the device once paired.
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
    // Whether this connector made the adapter pairable, so finish() puts it back.
    property bool madePairable: false
    // Paired and still on the link pairing opened, waiting for BlueZ to drop it (see checkPairing).
    property bool settling: false
    // A device just paired here, which the lists keep under Connected until its connection
    // finishes, so its row does not jump to Known Devices while the pairing link drops.
    property bool justPaired: false
    readonly property var holding: justPaired ? pendingDevice : null
    readonly property bool powered: !!adapter && adapter.enabled
    readonly property var stateLabels: ({pairing: Eitr.I18n.tr("Pairing..."), connecting: Eitr.I18n.tr("Connecting..."), connected: Eitr.I18n.tr("Connected"), paired: Eitr.I18n.tr("Paired"), "new": Eitr.I18n.tr("Not paired")})
    function activate(device) {
        const action = BluetoothDevices.rowAction(device);
        if (!live || !powered || !action || pendingDevice) return;
        failedDevice = null; failure = ""; confirmingForget = null;
        pendingDevice = device; pendingStep = action; sawConnecting = false;
        deadline.restart();
        if (action === "pair") {
            if (!adapter.pairable) { adapter.pairable = true; madePairable = true; }
            device.pair();
        } else device.connect();
    }
    function finish(error) {
        if (!pendingDevice) return;
        failedDevice = error ? pendingDevice : null;
        failure = error;
        pendingDevice = null; pendingStep = ""; sawConnecting = false; settling = false; justPaired = false;
        deadline.stop(); settle.stop();
        if (madePairable && adapter) adapter.pairable = false;
        madePairable = false;
    }
    function cancelPairing(device) {
        if (live) device.cancelPair();
        if (pendingDevice === device) finish("");
    }
    function checkPairing() {
        if (!pendingDevice || pendingStep !== "pair" || pendingDevice.pairing) return;
        if (pendingDevice.paired) {
            pendingDevice.trusted = true;
            pendingStep = "connect"; justPaired = true;
            // Pairing leaves only a bare link, which BlueZ drops once it sits idle. Quickshell
            // will not connect a device that is still linked, so wait for that drop and connect then.
            if (pendingDevice.connected) { settling = true; settle.restart(); return; }
            pendingDevice.connect();
        }
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
        // Devices link before pairing completes; checkPairing moves them on to connecting.
        function onConnectedChanged() {
            const device = connector.pendingDevice;
            if (!device || connector.pendingStep !== "connect") return;
            if (device.connected) { if (!connector.settling) connector.finish(""); }
            else if (connector.settling) { connector.settling = false; settle.stop(); deadline.restart(); device.connect(); }
        }
        function onStateChanged() {
            const state = connector.pendingDevice ? connector.pendingDevice.state : null;
            if (state === BluetoothDeviceState.Connecting) connector.sawConnecting = true;
            else if (state === BluetoothDeviceState.Disconnected && connector.sawConnecting && connector.pendingStep === "connect")
                connector.finish(Eitr.I18n.tr("Could not connect. Make sure the device is on and in range."));
        }
    }
    // A device whose profiles connected over the pairing link keeps it; stop waiting then.
    Timer {
        id: settle
        interval: 12000
        onTriggered: connector.finish("")
    }
    Timer {
        id: deadline
        interval: 30000
        onTriggered: connector.finish(connector.pendingStep === "pair" ? Eitr.I18n.tr("Pairing timed out.") : Eitr.I18n.tr("Could not connect. Make sure the device is on and in range."))
    }
}
