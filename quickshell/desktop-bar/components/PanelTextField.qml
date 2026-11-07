import ".."
import QtQuick
import QtQuick.Controls.Basic
import "../PanelStyle.js" as PanelStyle

// A text field in the panels' style: a faint foreground fill, the accent outline while
// focused, and the shared font, so no field falls back to the toolkit's white box.
TextField {
    id: field
    required property color foreground
    property color accent: foreground
    color: foreground
    placeholderTextColor: Qt.alpha(foreground, PanelStyle.secondaryTextOpacity)
    selectionColor: accent
    selectedTextColor: foreground
    font.family: DesktopFonts.family
    font.pixelSize: PanelStyle.bodySize
    selectByMouse: true
    Accessible.name: placeholderText
    background: Rectangle {
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(field.foreground, 0.08)
        border.width: 1
        border.color: field.activeFocus ? field.accent : "transparent"
    }
}
