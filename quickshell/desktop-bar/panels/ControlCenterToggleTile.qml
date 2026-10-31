import ".."
pragma ComponentBehavior: Bound
import QtQuick
import "../PanelStyle.js" as PanelStyle

ControlCenterTile {
    id: control
    required property var centerRef
    toggle: true
    tooltipBackground: control.centerRef.background
    foreground: control.centerRef.foreground; accent: control.centerRef.accent; accentInk: PanelStyle.readableInk(control.centerRef.accent, control.centerRef.foreground, control.centerRef.background)
}
