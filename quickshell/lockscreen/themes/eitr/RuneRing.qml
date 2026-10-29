import QtQuick
import QtQuick.Effects

Item {
    id: ring
    property color gold: "#c4914f"
    property bool glow: true
    readonly property string futhark: "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
    readonly property real radius: width * 0.43
    readonly property real glyphSize: width * 0.075

    component Runes: Item {
        Repeater {
            model: ring.futhark.length
            Text {
                required property int index
                readonly property real angle: index * 360 / ring.futhark.length - 90
                x: ring.width / 2 + Math.cos(angle * Math.PI / 180) * ring.radius - width / 2
                y: ring.height / 2 + Math.sin(angle * Math.PI / 180) * ring.radius - height / 2
                rotation: angle + 90
                text: ring.futhark[index]
                color: ring.gold
                font.family: "Noto Sans Runic"
                font.pixelSize: ring.glyphSize
            }
        }
    }
    Runes { id: glowSource; anchors.fill: parent; visible: false; layer.enabled: ring.glow }
    MultiEffect {
        anchors.fill: parent
        visible: ring.glow && GraphicsInfo.api !== GraphicsInfo.Software
        source: glowSource
        blurEnabled: true
        blur: 1
        blurMax: 24
        opacity: 0.55
    }
    Runes { anchors.fill: parent }
}
