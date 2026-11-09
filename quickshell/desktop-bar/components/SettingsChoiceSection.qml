import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// A setting chosen from picture cards: its gold title and one-line description, then the
// cards at full width (a ControlRow's side slot is too narrow for them).
Column {
    id: section
    required property string text
    required property string description
    required property color foreground
    default property alias content: cards.data
    width: parent ? parent.width : 0
    spacing: 8
    Column {
        width: parent.width
        spacing: 2
        SettingsText { text: section.text; color: SettingsInk.gold }
        SettingsText {
            width: parent.width
            visible: text !== ""
            text: section.description
            color: section.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }
    }
    Column {
        id: cards
        width: parent.width
    }
}
