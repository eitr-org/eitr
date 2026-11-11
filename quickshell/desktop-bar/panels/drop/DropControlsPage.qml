import "../.."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import Quickshell.Services.Pipewire
import "../../PanelStyle.js" as PanelStyle

// Drop's quick controls: round toggles for WiFi, Bluetooth, Airplane, Do Not Disturb, Night
// Light and Idle Lock, then the volume. They act through the Control Center's controllers,
// and observe network and radio state only while this page shows.
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
    property var powerTokens: []
    onWatchingChanged: {
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
        width: page.width / 6; height: 96
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

    Row {
        width: parent.width
        Toggle {
            label: Eitr.I18n.tr("WiFi"); glyph: page.center.wifiGlyph
            detail: page.wifi.connected ? page.wifi.connected.name : page.wifi.device && page.wifi.device.powered ? Eitr.I18n.tr("On") : Eitr.I18n.tr("Off")
            on: !!page.wifi.device && page.wifi.device.powered
            available: !!page.wifi.device && !page.wifi.busy && !page.airplane.enabled
            onActivated: page.wifi.act(page.center, "power", page.wifi.device.path, page.wifi.device.powered ? "false" : "true")
        }
        Toggle {
            readonly property var devices: page.center.bluetoothDevices
            label: Eitr.I18n.tr("Bluetooth"); glyph: "󰂯"
            detail: devices.length === 1 ? devices[0].name : devices.length > 1 ? Eitr.I18n.tr("{count} devices", {count: devices.length}) : on ? Eitr.I18n.tr("On") : Eitr.I18n.tr("Off")
            on: !!page.bluetooth.adapter && page.bluetooth.adapter.enabled
            available: !!page.bluetooth.adapter && !page.airplane.enabled
            onActivated: page.bluetooth.adapter.enabled = !page.bluetooth.adapter.enabled
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
    }
    Rectangle { x: 6; width: parent.width - 12; height: 1; color: Qt.alpha(page.foreground, 0.14) }
    AudioLevelControl {
        x: 6; width: parent.width - 12
        node: Pipewire.defaultAudioSink; showName: false; textSize: 12; iconSize: 16
        foreground: page.foreground; background: page.background; accent: page.accent
    }
}
