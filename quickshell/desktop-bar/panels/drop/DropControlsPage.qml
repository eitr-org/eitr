import "../.."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import Quickshell.Services.Pipewire
import Quickshell.Bluetooth
import "../../PanelStyle.js" as PanelStyle

// Drop's quick controls: round buttons for WiFi, Bluetooth, Sound and Microphone, which open
// in place (networks, devices and audio devices, with a back arrow and their own switch),
// and toggles for Airplane, Silence, Night Light, Idle Lock and OBS recording; then the volume. They act
// through the Control Center's controllers and observe network and radio state only while
// this page shows.
Column {
    id: page
    required property var barHost
    required property color foreground
    required property color accent
    required property color background
    required property bool watching
    readonly property var center: barHost.controlCenter
    readonly property var wifi: center.wifiControl
    readonly property var bluetooth: center.bluetoothControl
    readonly property var airplane: PowerService.radios
    readonly property var nightlight: center.displayControl.nightlight
    property string networkToken: ""
    // The control opened in place ("wifi", "bluetooth", "sound", "microphone") or "".
    property string opened: ""
    readonly property PwNode sink: Pipewire.defaultAudioSink
    readonly property PwNode source: Pipewire.defaultAudioSource
    PwObjectTracker { objects: [page.sink, page.source] }
    property var powerTokens: []
    onWatchingChanged: {
        if (!watching) opened = "";
        PowerService.release(powerTokens);
        powerTokens = watching ? PowerService.observe(page, 5, true) : [];
        if (watching) {
            networkToken = wifi.observe(page);
            DisplayService.open(page, 5);
            return;
        }
        DisplayService.close(page);
        if (networkToken) { wifi.release(networkToken); networkToken = ""; }
    }
    Component.onDestruction: { DisplayService.close(page); PowerService.release(powerTokens); if (networkToken) wifi.release(networkToken); }
    spacing: 18
    topPadding: 10
    bottomPadding: 6

    // One round toggle with its name and current state below.
    component Toggle: Item {
        id: toggle
        required property string label
        required property string glyph
        property string detail: ""
        property bool on: false
        property bool available: true
        signal activated()
        width: page.width / 5; height: 92
        opacity: available ? 1 : 0.45
        Rectangle {
            id: disc
            anchors.horizontalCenter: parent.horizontalCenter
            width: 52; height: 52; radius: 26
            color: toggle.on ? page.accent : Qt.alpha(page.foreground, mouse.containsMouse ? 0.14 : 0.08)
            border.width: toggle.on ? 0 : 1
            border.color: Qt.alpha(page.foreground, PanelStyle.selectionBorderAlpha)
            scale: mouse.pressed ? 0.92 : 1
            Behavior on color { ColorAnimation { duration: DesktopStyle.motionDuration(160) } }
            Behavior on scale { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
            Text {
                anchors.centerIn: parent
                text: toggle.glyph
                color: toggle.on ? PanelStyle.readableInk(page.accent, page.foreground, page.background) : page.foreground
                font.family: DesktopFonts.family; font.pixelSize: 20
            }
        }
        Text {
            id: name
            y: disc.height + 8; width: parent.width
            horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
            text: toggle.label
            color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.weight: Font.DemiBold
        }
        Text {
            y: name.y + name.height + 1; width: parent.width - 6; x: 3
            horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; textFormat: Text.PlainText
            text: toggle.detail
            color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: 11
        }
        MouseArea {
            id: mouse
            anchors.fill: disc
            enabled: toggle.available; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onClicked: toggle.activated()
        }
    }

    Grid {
        visible: page.opened === ""
        width: parent.width
        columns: 5
        rowSpacing: 4
        Toggle {
            label: Eitr.I18n.tr("WiFi"); glyph: page.center.wifiGlyph
            detail: page.wifi.connected ? page.wifi.connected.name : page.wifi.device && page.wifi.device.powered ? Eitr.I18n.tr("On") : Eitr.I18n.tr("Off")
            on: !!page.wifi.device && page.wifi.device.powered
            available: !!page.wifi.device
            onActivated: page.opened = "wifi"
        }
        Toggle {
            readonly property var devices: page.center.bluetoothDevices
            label: Eitr.I18n.tr("Bluetooth"); glyph: "󰂯"
            detail: devices.length === 1 ? devices[0].name : devices.length > 1 ? Eitr.I18n.tr("{count} devices", {count: devices.length}) : on ? Eitr.I18n.tr("On") : Eitr.I18n.tr("Off")
            on: !!page.bluetooth.adapter && page.bluetooth.adapter.enabled
            available: !!page.bluetooth.adapter
            onActivated: page.opened = "bluetooth"
        }
        Toggle {
            label: Eitr.I18n.tr("Sound"); glyph: page.sink && page.sink.audio && page.sink.audio.muted ? "󰖁" : "󰕾"
            detail: page.sink ? AudioDevices.label(page.sink) : ""
            on: !!page.sink && !!page.sink.audio && !page.sink.audio.muted
            onActivated: page.opened = "sound"
        }
        Toggle {
            label: Eitr.I18n.tr("Microphone"); glyph: page.source && page.source.audio && page.source.audio.muted ? "󰍭" : "󰍬"
            detail: page.source ? AudioDevices.label(page.source) : ""
            on: !!page.source && !!page.source.audio && !page.source.audio.muted
            onActivated: page.opened = "microphone"
        }
        Toggle {
            label: Eitr.I18n.tr("Airplane"); glyph: "󰀝"
            on: !!page.airplane.enabled
            available: !!page.airplane.available && !PowerService.busy
            onActivated: PowerService.act("airplane", page.airplane.enabled ? "false" : "true", function() {})
        }
        Toggle {
            label: Eitr.I18n.tr("Silence"); glyph: "󰂛"
            on: page.center.service.doNotDisturb
            onActivated: page.center.service.toggleDnd()
        }
        Toggle {
            label: Eitr.I18n.tr("Night Light"); glyph: "󰖔"
            detail: page.nightlight.mode === "auto" ? Eitr.I18n.tr("Scheduled") : ""
            on: page.nightlight.mode === "on" || !!page.nightlight.active
            available: !!page.nightlight.available
            onActivated: page.center.displayControl.setNightlight(page.nightlight.mode === "on" ? "off" : "on")
        }
        Toggle {
            label: Eitr.I18n.tr("Idle Lock"); glyph: "󱫖"
            on: page.center.idleEnabled
            available: !page.center.idleBusy
            onActivated: page.center.idleToggleRequested()
        }
        // Starts and stops an OBS recording through the OBS panel's own actions.
        Toggle {
            readonly property var obs: page.barHost.obsMenu
            label: Eitr.I18n.tr("Record"); glyph: on ? "󰻃" : "󰑊"
            detail: obs.obsState.paused ? Eitr.I18n.tr("Paused") : on ? Eitr.I18n.tr("Recording") : ""
            on: !!obs.obsState.recording
            available: !obs.busy
            onActivated: obs.run(on ? "stop" : "record")
        }
    }

    // A control opened in place: back, its name, its own switch, then its list.
    Item {
        visible: page.opened !== ""
        x: 6; width: parent.width - 12; height: 32
        PanelButton {
            id: back
            width: 28; height: 28; icon: true; anchors.verticalCenter: parent.verticalCenter
            text: "󰅁"; foreground: page.foreground
            Accessible.name: Eitr.I18n.tr("Back")
            onClicked: page.opened = ""
        }
        Text {
            x: back.width + 8; anchors.verticalCenter: parent.verticalCenter
            text: ({wifi: Eitr.I18n.tr("WiFi"), bluetooth: Eitr.I18n.tr("Bluetooth"), sound: Eitr.I18n.tr("Sound"), microphone: Eitr.I18n.tr("Microphone")})[page.opened] || ""
            color: page.accent; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
            font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2
        }
        Row {
            anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
            spacing: 10
            PanelLoadingIndicator {
                width: 24; height: 24; anchors.verticalCenter: parent.verticalCenter
                visible: page.opened === "wifi" || page.opened === "bluetooth"
                busy: page.opened === "wifi" ? !!page.wifi.device && page.wifi.device.scanning : bluetoothDetail.scanning
                foreground: page.foreground; background: page.background
            }
            PanelSwitch {
                anchors.verticalCenter: parent.verticalCenter
                foreground: page.foreground; accent: page.accent
                readonly property var node: page.opened === "sound" ? page.sink : page.opened === "microphone" ? page.source : null
                checked: page.opened === "wifi" ? !!page.wifi.device && page.wifi.device.powered
                    : page.opened === "bluetooth" ? !!page.bluetooth.adapter && page.bluetooth.adapter.enabled
                    : !!node && !!node.audio && !node.audio.muted
                enabled: page.opened === "wifi" ? !!page.wifi.device && !page.wifi.busy && !page.airplane.enabled
                    : page.opened === "bluetooth" ? !!page.bluetooth.adapter && !page.airplane.enabled : !!node && !!node.audio
                onClicked: {
                    if (page.opened === "wifi") page.wifi.act(page.center, "power", page.wifi.device.path, checked ? "true" : "false");
                    else if (page.opened === "bluetooth") page.bluetooth.adapter.enabled = checked;
                    else node.audio.muted = !checked;
                }
            }
        }
    }
    Flickable {
        visible: page.opened !== ""
        x: 6; width: parent.width - 12
        height: Math.min(300, contentHeight)
        contentHeight: Math.max(wifiDetail.visible ? wifiDetail.implicitHeight : 0, bluetoothDetail.visible ? bluetoothDetail.implicitHeight : 0,
            soundDetail.visible ? soundDetail.implicitHeight : 0)
        clip: true; boundsBehavior: Flickable.StopAtBounds
        DropWifiDetail {
            id: wifiDetail
            visible: page.opened === "wifi"; shown: visible && page.watching
            width: parent.width
            barHost: page.barHost; wifi: page.wifi
            foreground: page.foreground; background: page.background; accent: page.accent
        }
        DropBluetoothDetail {
            id: bluetoothDetail
            visible: page.opened === "bluetooth"; shown: visible && page.watching
            width: parent.width
            adapter: page.bluetooth.adapter || Bluetooth.defaultAdapter
            foreground: page.foreground
        }
        DropAudioDetail {
            id: soundDetail
            visible: page.opened === "sound" || page.opened === "microphone"
            microphone: page.opened === "microphone"
            width: parent.width
            foreground: page.foreground; background: page.background; accent: page.accent
        }
    }

    Rectangle { visible: page.opened === ""; x: 6; width: parent.width - 12; height: 1; color: Qt.alpha(page.foreground, 0.14) }
    AudioLevelControl {
        visible: page.opened === ""
        x: 6; width: parent.width - 12
        node: Pipewire.defaultAudioSink; showName: false; textSize: 12; iconSize: 16
        foreground: page.foreground; background: page.background; accent: page.accent
    }
}
