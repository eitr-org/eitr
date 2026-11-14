import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Text {
    id: root
    required property var catalog

    color: catalog.foreground
    font.family: DesktopFonts.family
    font.pixelSize: PanelStyle.bodySize
    wrapMode: Text.Wrap
    textFormat: Text.PlainText
}
