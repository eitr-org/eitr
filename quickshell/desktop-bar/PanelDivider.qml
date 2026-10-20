import QtQuick
import QtQuick.Shapes
import "PanelStyle.js" as PanelStyle

Row {
    id: divider
    property string text: ""
    required property color foreground
    spacing: 10
    height: text ? label.implicitHeight : 8

    Text {
        id: label
        visible: divider.text.length > 0
        text: divider.text.toUpperCase()
        color: Qt.alpha(divider.foreground, 0.6)
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
        font.bold: true
    }
    Shape {
        anchors.verticalCenter: parent.verticalCenter
        width: Math.max(0, divider.width - (divider.text ? label.width + divider.spacing : 0))
        height: 8
        visible: width > 24
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: "transparent"
            strokeColor: Qt.alpha(divider.foreground, PanelStyle.dividerAlpha)
            strokeWidth: 1
            PathSvg {
                path: {
                    const middle = (divider.width - (divider.text ? label.width + divider.spacing : 0)) / 2;
                    return "M0 4 H" + (middle - 5) + " L" + middle + " 0 L" + (middle + 5)
                        + " 4 L" + middle + " 8 L" + (middle - 5) + " 4 M" + (middle + 5) + " 4 H" + (middle * 2);
                }
            }
        }
    }
}
