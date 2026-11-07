import ".."
import QtQuick

// A gold rune breadcrumb, a carved title and a one-line description.
Column {
    id: header
    required property color foreground
    property string rune: ""
    property string group: ""
    property string title: ""
    property string description: ""
    width: parent ? parent.width : 0
    spacing: 7
    Text {
        text: header.rune + "  " + header.group.toLocaleUpperCase()
        color: SettingsInk.gold
        font.family: SettingsInk.runes
        font.pixelSize: 11
        font.letterSpacing: 1.6
    }
    Text {
        width: parent.width
        text: header.title
        color: header.foreground
        font.family: SiteStyle.carved
        font.pixelSize: 25
        wrapMode: Text.WordWrap
    }
    Text {
        width: parent.width
        visible: text !== ""
        text: header.description
        color: header.foreground
        opacity: 0.72
        font.family: DesktopFonts.family
        font.pixelSize: 13
        wrapMode: Text.WordWrap
    }
}
