import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import Quickshell.Io
import Quickshell.Services.Pipewire

Column {
    id: control
    property PwNode node: null
    required property color accent
    required property color foreground
    required property color background
    property bool microphone: false
    property bool showName: true
    property int textSize: PanelStyle.bodySize
    property int iconSize: 18
    property string name: node ? (node.properties["application.name"] || AudioDevices.label(node)) : Eitr.I18n.tr("No device available")
    spacing: 6
    PwObjectTracker { objects: [control.node] }
    Process { id: volumeOsd; command: ["swayosd-client", "--custom-icon", "audio-volume-high-symbolic", "--custom-progress", "0"] }
    function showVolumeOsd(value) {
        if (volumeOsd.running) return;
        volumeOsd.command = ["swayosd-client", "--custom-icon", control.microphone ? "microphone-sensitivity-high-symbolic" : "audio-volume-high-symbolic", "--custom-progress", String(value)];
        volumeOsd.running = true;
    }

    Text {
        visible: control.showName
        width: parent.width
        text: control.name
        elide: Text.ElideRight
        color: control.foreground
        font.family: DesktopFonts.family
        font.pixelSize: control.textSize
    }
    Row {
        width: parent.width
        spacing: 10
        Rectangle {
            width: 30
            height: 30
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: muteMouse.containsMouse ? Qt.rgba(control.foreground.r, control.foreground.g, control.foreground.b, 0.1) : "transparent"
            Text {
                anchors.centerIn: parent
                text: control.microphone ? (control.node && control.node.audio.muted ? "󰍭" : "󰍬") : (control.node && control.node.audio.muted ? "󰖁" : "")
                font.family: DesktopFonts.family
                font.pixelSize: control.iconSize
                color: control.foreground
            }
            MouseArea {
                id: muteMouse
                anchors.fill: parent
                enabled: control.node !== null && control.node.ready
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: control.node.audio.muted = !control.node.audio.muted
            }
            BarTooltip {
                target: parent
                hovered: muteMouse.containsMouse
                text: control.node && control.node.audio.muted ? Eitr.I18n.tr("Unmute") : Eitr.I18n.tr("Mute")
                background: control.background
                foreground: control.foreground
            }
        }
        PanelSlider {
            id: slider
            accent: control.accent
            foreground: control.foreground
            width: control.width - 100
            from: 0
            to: 1
            stepSize: 0.01
            enabled: control.node !== null && control.node.ready
            Binding {
                target: slider
                property: "value"
                value: control.node ? control.node.audio.volume : 0
                when: !slider.pressed
            }
            onMoved: {
                if (control.node) {
                    control.node.audio.volume = value;
                    control.showVolumeOsd(value);
                }
            }
        }
        Text {
            width: 50
            height: 30
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: control.node ? Math.round(control.node.audio.volume * 100) + "%" : "--"
            color: control.foreground
            font.family: DesktopFonts.family
            font.pixelSize: control.textSize
            font.features: PanelStyle.tabularFigures
        }
    }
}
