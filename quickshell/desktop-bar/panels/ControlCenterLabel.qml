import ".."
pragma ComponentBehavior: Bound
import QtQuick
import "../PanelStyle.js" as PanelStyle

Text {
    id: control
    required property var centerRef
    color: control.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
}
