import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

Text {
    width: parent ? parent.width : 0
    color: SettingsPalette.foreground
    font.family: DesktopFonts.family
    font.pixelSize: PanelStyle.bodySize
    wrapMode: Text.WordWrap
}
