import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import Quickshell.Services.Pipewire
import Quickshell.Bluetooth
import "../PanelStyle.js" as PanelStyle

// A Control Center control opened in place: back, its name, its own switch, then its
// list (WiFi networks, Bluetooth devices, or the sound or microphone devices).
Column {
    id: detail
    required property var centerRef
    // "wifi", "bluetooth", "sound" or "microphone".
    required property string kind
    required property bool watching
    signal closed()
    readonly property var wifi: centerRef.wifiControl
    readonly property var bluetooth: centerRef.bluetoothControl
    readonly property var airplane: PowerService.radios
    readonly property PwNode sink: Pipewire.defaultAudioSink
    readonly property PwNode source: Pipewire.defaultAudioSource
    readonly property color foreground: centerRef.foreground
    readonly property color background: centerRef.background
    readonly property color accent: centerRef.accent
    PwObjectTracker { objects: [detail.sink, detail.source] }
    width: parent.width
    spacing: 12

    Item {
        width: parent.width; height: 32
        PanelButton {
            id: back
            width: 28; height: 28; icon: true; anchors.verticalCenter: parent.verticalCenter
            text: "󰅁"; foreground: detail.foreground
            Accessible.name: Eitr.I18n.tr("Back")
            onClicked: detail.closed()
        }
        Text {
            x: back.width + 8; anchors.verticalCenter: parent.verticalCenter
            text: ({wifi: Eitr.I18n.tr("WiFi"), bluetooth: Eitr.I18n.tr("Bluetooth"), sound: Eitr.I18n.tr("Sound"), microphone: Eitr.I18n.tr("Microphone")})[detail.kind] || ""
            color: detail.accent; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
            font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2
        }
        Row {
            anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
            spacing: 10
            PanelLoadingIndicator {
                width: 24; height: 24; anchors.verticalCenter: parent.verticalCenter
                visible: detail.kind === "wifi" || detail.kind === "bluetooth"
                busy: detail.kind === "wifi" ? !!detail.wifi.device && detail.wifi.device.scanning : bluetoothDetail.scanning
                foreground: detail.foreground; background: detail.background
            }
            PanelSwitch {
                anchors.verticalCenter: parent.verticalCenter
                foreground: detail.foreground; accent: detail.accent
                readonly property var node: detail.kind === "sound" ? detail.sink : detail.kind === "microphone" ? detail.source : null
                checked: detail.kind === "wifi" ? !!detail.wifi.device && detail.wifi.device.powered
                    : detail.kind === "bluetooth" ? !!detail.bluetooth.adapter && detail.bluetooth.adapter.enabled
                    : !!node && !!node.audio && !node.audio.muted
                enabled: detail.kind === "wifi" ? !!detail.wifi.device && !detail.wifi.busy && !detail.airplane.enabled
                    : detail.kind === "bluetooth" ? !!detail.bluetooth.adapter && !detail.airplane.enabled : !!node && !!node.audio
                onClicked: {
                    if (detail.kind === "wifi") detail.wifi.act(detail.centerRef, "power", detail.wifi.device.path, checked ? "true" : "false");
                    else if (detail.kind === "bluetooth") detail.bluetooth.adapter.enabled = checked;
                    else node.audio.muted = !checked;
                }
            }
        }
    }
    Flickable {
        width: parent.width
        height: Math.min(360, contentHeight)
        contentHeight: Math.max(wifiDetail.visible ? wifiDetail.implicitHeight : 0, bluetoothDetail.visible ? bluetoothDetail.implicitHeight : 0,
            soundDetail.visible ? soundDetail.implicitHeight : 0)
        clip: true; boundsBehavior: Flickable.StopAtBounds
        DropWifiDetail {
            id: wifiDetail
            visible: detail.kind === "wifi"; shown: visible && detail.watching
            width: parent.width
            barHost: detail.centerRef.barRef; wifi: detail.wifi
            foreground: detail.foreground; background: detail.background; accent: detail.accent
        }
        DropBluetoothDetail {
            id: bluetoothDetail
            visible: detail.kind === "bluetooth"; shown: visible && detail.watching
            width: parent.width
            adapter: detail.bluetooth.adapter || Bluetooth.defaultAdapter
            foreground: detail.foreground
        }
        DropAudioDetail {
            id: soundDetail
            visible: detail.kind === "sound" || detail.kind === "microphone"
            microphone: detail.kind === "microphone"
            width: parent.width
            foreground: detail.foreground; background: detail.background; accent: detail.accent
        }
    }
}
