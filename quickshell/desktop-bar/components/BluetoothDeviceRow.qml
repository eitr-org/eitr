import ".."
import QtQuick
import Eitr as Eitr
import "BluetoothDevices.js" as BluetoothDevices

// One Bluetooth device, in Settings and the bar panel: a click on the row pairs and
// connects (through the shared BluetoothConnector); Disconnect, Forget and Cancel sit
// inside the row.
ConnectionRow {
    id: deviceRow
    required property var modelData
    required property var connector
    readonly property bool pending: connector.pendingDevice === modelData
    objectName: "bluetooth-device-row"
    text: BluetoothDevices.named(modelData) ? modelData.name : Eitr.I18n.tr("Unnamed device")
    glyph: BluetoothDevices.glyph(modelData)
    detail: connector.label(modelData)
    error: connector.failedDevice === modelData ? connector.failure : ""
    selected: !!modelData.connected
    loading: pending || !!modelData.pairing
    activatable: connector.powered && !connector.pendingDevice && BluetoothDevices.rowAction(modelData) !== ""
    onActivated: connector.activate(modelData)
    PanelButton {
        visible: deviceRow.loading && (deviceRow.connector.pendingStep === "pair" || !!deviceRow.modelData.pairing)
        width: 84; height: 28; foreground: deviceRow.foreground
        text: Eitr.I18n.tr("Cancel")
        onClicked: deviceRow.connector.cancelPairing(deviceRow.modelData)
    }
    PanelButton {
        visible: !!deviceRow.modelData.connected
        width: 100; height: 28; foreground: deviceRow.foreground
        text: Eitr.I18n.tr("Disconnect"); available: deviceRow.connector.powered
        onClicked: deviceRow.connector.disconnect(deviceRow.modelData)
    }
    PanelButton {
        visible: !!deviceRow.modelData.paired && !deviceRow.loading
        width: 84; height: 28; foreground: deviceRow.foreground
        text: deviceRow.connector.confirmingForget === deviceRow.modelData ? Eitr.I18n.tr("Confirm") : Eitr.I18n.tr("Forget")
        Accessible.name: deviceRow.connector.confirmingForget === deviceRow.modelData ? Eitr.I18n.tr("Confirm removal") : Eitr.I18n.tr("Forget")
        onClicked: deviceRow.connector.forget(deviceRow.modelData)
    }
}
