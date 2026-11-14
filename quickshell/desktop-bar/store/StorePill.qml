import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    id: root
    required property var catalog

    property string text: ""
    property bool current: false
    implicitWidth: pillLabel.implicitWidth + 16; height: 22
    radius: 11
    color: Qt.alpha(current ? catalog.accent : catalog.foreground, current ? 0.14 : 0.04)
    border.width: 1; border.color: current ? catalog.accent : catalog.line
    StoreLabel { catalog: root.catalog; id: pillLabel; anchors.centerIn: parent; text: parent.text; font.family: SiteStyle.carved; font.capitalization: Font.AllUppercase; font.letterSpacing: 1; font.pixelSize: 11; color: parent.current ? catalog.foreground : catalog.gold }
}
