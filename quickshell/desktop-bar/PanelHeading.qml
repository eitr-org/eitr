import QtQuick
import QtQuick.Shapes
import "PanelStyle.js" as PanelStyle

// A panel title beside the theme-accent rune seal. The optional subtitle is a
// caption under the title; seal: false leaves room for a panel's own emblem.
Item {
    id: heading
    required property string text
    required property color foreground
    required property color accent
    property string rune: "general"
    property string subtitle: ""
    property bool seal: true
    property int elide: Text.ElideRight
    property int textFormat: Text.PlainText
    readonly property real textX: seal ? 38 : 0
    implicitWidth: textX + Math.max(title.implicitWidth, caption.visible ? caption.implicitWidth : 0)
    implicitHeight: Math.max(seal ? 32 : 0, lines.implicitHeight)
    width: implicitWidth
    height: implicitHeight

    Shape {
        visible: heading.seal
        anchors.verticalCenter: parent.verticalCenter
        width: 28; height: 32
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: "transparent"
            strokeColor: Qt.alpha(heading.foreground, 0.18)
            strokeWidth: 1
            PathSvg { path: "M14 1 L27 8 L27 24 L14 31 L1 24 L1 8 Z" }
        }
        ShapePath {
            fillColor: "transparent"
            strokeColor: Qt.alpha(heading.accent, 0.75)
            strokeWidth: 1.5
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.MiterJoin
            PathSvg {
                path: ["style", "display", "weather", "calendar"].indexOf(heading.rune) >= 0 ? "M14 7 L7 16 L14 25 L21 16 Z M14 7 L14 25"
                    : ["settings", "system", "hardware", "keyboard", "audio"].indexOf(heading.rune) >= 0 ? "M14 6 L14 26 M7 10 L21 22 M21 10 L7 22"
                    : ["capture", "tools", "media", "recording"].indexOf(heading.rune) >= 0 ? "M9 26 L9 6 L20 13 L9 20"
                    : "M14 26 L14 6 M14 15 L6 8 M14 15 L22 8"
            }
        }
    }
    Column {
        id: lines
        x: heading.textX
        width: Math.max(0, heading.width - x)
        anchors.verticalCenter: parent.verticalCenter
        spacing: 4
        Text {
            id: title
            width: parent.width
            elide: heading.elide
            textFormat: heading.textFormat
            text: heading.text
            color: heading.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.headingSize
            font.bold: true
        }
        Text {
            id: caption
            visible: heading.subtitle !== ""
            width: parent.width
            elide: Text.ElideRight
            textFormat: Text.PlainText
            text: heading.subtitle
            color: heading.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
    }
}
