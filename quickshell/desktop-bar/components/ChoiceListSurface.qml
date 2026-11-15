import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// The floating surface behind choice lists: ChoiceDropdown's list and the Store's filter menu.
Rectangle {
    required property color foreground
    required property color surface
    radius: DesktopStyle.radius(PanelStyle.controlRadius + 4)
    color: Qt.rgba(surface.r, surface.g, surface.b, 1)
    border.width: 1
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)
}
