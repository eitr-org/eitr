import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// Large setup cards from the welcome chapter; each asks the reader to open its
// Settings page (`route`, such as "connections/wifi"). Nothing runs from here.
Column {
    id: setup
    required property var section
    required property color foreground
    required property color accent
    signal chosen(string route)
    readonly property var items: section ? section.items || [] : []
    readonly property int columns: width >= 760 ? 3 : width >= 440 ? 2 : 1
    width: parent ? parent.width : 0
    spacing: 8
    Text {
        width: parent.width
        text: setup.section ? setup.section.title : ""
        textFormat: Text.StyledText
        color: setup.foreground
        font.family: SiteStyle.carved; font.pixelSize: 19
        wrapMode: Text.WordWrap
    }
    Text {
        width: parent.width
        visible: text !== ""
        text: setup.section ? setup.section.intro || "" : ""
        textFormat: Text.StyledText
        color: SettingsPalette.muted
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        wrapMode: Text.WordWrap
    }
    Item { width: 1; height: 6 }
    Flow {
        width: parent.width
        spacing: 12
        Repeater {
            model: setup.items
            Rectangle {
                id: card
                required property var modelData
                required property int index
                readonly property bool lit: pointer.containsMouse || activeFocus
                // A shorter last row shares the full width instead of leaving a gap.
                readonly property int rowSize: index >= setup.items.length - setup.items.length % setup.columns ? setup.items.length % setup.columns : setup.columns
                width: Math.floor((setup.width - 12 * (rowSize - 1)) / rowSize)
                height: Math.max(92, words.implicitHeight + 28)
                radius: DesktopStyle.radius(12)
                color: lit ? SettingsPalette.raised : SettingsPalette.surface
                border.width: 1
                border.color: lit ? Qt.alpha(SettingsInk.gold, 0.8) : SettingsPalette.line
                activeFocusOnTab: true
                Accessible.role: Accessible.Button
                Accessible.name: title.text.replace(/<[^>]*>/g, "").replace(/&amp;/g, "&")
                Accessible.description: detail.text
                Keys.onReturnPressed: setup.chosen(modelData.route)
                Keys.onEnterPressed: setup.chosen(modelData.route)
                Keys.onSpacePressed: setup.chosen(modelData.route)
                Behavior on color { ColorAnimation { duration: DesktopStyle.motionDuration(120) } }
                Rectangle {
                    id: disc
                    x: 16; anchors.verticalCenter: parent.verticalCenter
                    width: 46; height: 46; radius: 23
                    color: Qt.alpha(setup.accent, card.lit ? 0.3 : 0.18)
                    border.width: 1; border.color: Qt.alpha(SettingsInk.gold, 0.45)
                    Text {
                        anchors.centerIn: parent
                        text: card.modelData.icon || ""
                        color: setup.foreground
                        font.family: PanelStyle.fontFamily; font.pixelSize: 22
                    }
                }
                Column {
                    id: words
                    x: disc.x + disc.width + 14
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width - x - 42
                    spacing: 4
                    Text {
                        id: title
                        width: parent.width
                        text: card.modelData.title || ""
                        textFormat: Text.StyledText
                        color: setup.foreground
                        font.family: SiteStyle.carved; font.pixelSize: 15
                        elide: Text.ElideRight
                    }
                    Text {
                        id: detail
                        width: parent.width
                        text: card.modelData.text || ""
                        textFormat: Text.StyledText
                        color: SettingsPalette.muted
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                        wrapMode: Text.WordWrap
                        maximumLineCount: 3
                        elide: Text.ElideRight
                    }
                }
                Text {
                    anchors.right: parent.right; anchors.rightMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    text: "›"
                    color: card.lit ? SettingsInk.gold : SettingsPalette.muted
                    font.family: DesktopFonts.family; font.pixelSize: 22
                }
                MouseArea {
                    id: pointer
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: { card.forceActiveFocus(); setup.chosen(card.modelData.route); }
                }
            }
        }
    }
}
