import "../.."
import QtQuick
import "../../PanelStyle.js" as PanelStyle

// A soft tile on Drop's dashboard pages.
Rectangle {
    required property color foreground
    radius: DesktopStyle.radius(PanelStyle.controlRadius + 6)
    color: Qt.alpha(foreground, 0.06)
    border.width: 1
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha * 0.7)
}
