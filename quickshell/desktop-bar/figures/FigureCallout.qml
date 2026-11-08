import ".."
import QtQuick
import QtQuick.Shapes
import "../PanelStyle.js" as PanelStyle

// A labelled callout on a handbook figure: a thin gold leader line from a point on the
// drawing to a short label. `side` places the label above, below, left or right of
// the line's end; labels stay inside the figure.
Item {
    id: callout
    required property real targetX
    required property real targetY
    required property real labelX
    required property real labelY
    required property string text
    property string side: "top"
    property color foreground: SettingsPalette.foreground
    property color background: SettingsPalette.background
    property color gold: SettingsInk.gold
    anchors.fill: parent
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: Qt.alpha(callout.gold, 0.9)
            strokeWidth: 1
            fillColor: "transparent"
            startX: callout.targetX; startY: callout.targetY
            PathLine { x: callout.labelX; y: callout.labelY }
        }
    }
    Rectangle {
        x: callout.targetX - 2.5; y: callout.targetY - 2.5
        width: 5; height: 5; radius: 2.5
        color: callout.gold
    }
    Rectangle {
        id: tag
        width: label.implicitWidth + 10; height: label.implicitHeight + 4
        x: Math.max(0, Math.min(callout.width - width,
            callout.side === "left" ? callout.labelX - width : callout.side === "right" ? callout.labelX : callout.labelX - width / 2))
        y: callout.side === "top" ? callout.labelY - height : callout.side === "bottom" ? callout.labelY : callout.labelY - height / 2
        radius: DesktopStyle.radius(4)
        color: Qt.alpha(callout.background, 0.88)
        border.width: 1; border.color: Qt.alpha(callout.gold, 0.45)
        Text {
            id: label
            anchors.centerIn: parent
            text: callout.text
            horizontalAlignment: Text.AlignHCenter
            color: callout.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
    }
}
