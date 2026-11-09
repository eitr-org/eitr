import ".."
import QtQuick

// A gold rune breadcrumb, a carved title and a one-line description. Items placed inside
// (a page's own action, such as Create User…) sit at the top right, beside the title.
Item {
    id: header
    required property color foreground
    property string rune: ""
    property string group: ""
    property string title: ""
    property string description: ""
    default property alias actions: actionRow.data
    readonly property real actionsWidth: actionRow.implicitWidth > 0 ? actionRow.implicitWidth + 16 : 0
    width: parent ? parent.width : 0
    implicitHeight: column.implicitHeight
    height: implicitHeight
    Column {
        id: column
        width: parent.width
        spacing: 7
        Text {
            text: header.rune + "  " + header.group.toLocaleUpperCase()
            color: SettingsInk.gold
            font.family: SettingsInk.runes
            font.pixelSize: 11
            font.letterSpacing: 1.6
        }
        Text {
            width: parent.width - header.actionsWidth
            text: header.title
            color: header.foreground
            font.family: SiteStyle.carved
            font.pixelSize: 25
            wrapMode: Text.WordWrap
        }
        Text {
            width: parent.width - header.actionsWidth
            visible: text !== ""
            text: header.description
            color: header.foreground
            opacity: 0.72
            font.family: DesktopFonts.family
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
    }
    Row {
        id: actionRow
        anchors.right: parent.right
        anchors.bottom: column.bottom
        spacing: 8
    }
}
