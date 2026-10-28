import QtQuick
import "PanelStyle.js" as PanelStyle

Item {
    id: marker
    required property string style
    required property string label
    required property bool active
    required property color accent
    required property color foreground
    required property color selectedForeground
    property int fontSize: 14
    property int textOffsetY: -1
    // Runes: the first ten Elder Futhark runes stand for workspaces 1 to 10.
    readonly property var runes: ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ"]
    readonly property bool runic: style === "Runes"

    implicitWidth: 23
    implicitHeight: 20

    Text {
        visible: marker.style !== "Dots"
        anchors.fill: parent
        y: marker.textOffsetY
        text: marker.style === "Glyph" ? (marker.active ? "✦" : "✧")
            : marker.runic ? (marker.runes[Number(marker.label) - 1] ?? marker.label) : marker.label
        color: marker.active ? marker.accent : marker.foreground
        font.family: marker.runic ? "Noto Sans Runic" : DesktopFonts.family
        font.pixelSize: marker.style === "Glyph" ? 19 : marker.runic ? marker.fontSize + 2 : marker.fontSize
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    Rectangle {
        visible: marker.style === "Dots"
        anchors.centerIn: parent
        width: marker.active ? 22 : 12
        height: 12
        radius: DesktopStyle.radius(6)
        color: marker.active ? "transparent" : Qt.rgba(marker.foreground.r, marker.foreground.g, marker.foreground.b, 0.08)
        Rectangle {
            anchors.centerIn: parent
            width: marker.active ? 17 : 6
            height: 6
            radius: 3
            color: marker.active ? marker.accent : marker.foreground
            Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(140) } }
        }
        Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(140) } }
    }
}
