import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle
import Eitr as Eitr

FocusScope {
    property color muted: Qt.alpha(foreground, 0.72)
    property color line: Qt.alpha(foreground, 0.15)
    property color gold: foreground
    id: tabs
    property color foreground: "#eeeeee"
    property bool carved: false
    property var choices: []
    property string current: ""
    signal chosen(string value)
    implicitHeight: 42
    function move(delta) {
        if (!choices.length) return;
        const index = choices.findIndex(choice => choice.id === current);
        chosen(choices[(index + delta + choices.length) % choices.length].id);
    }
    Keys.onLeftPressed: move(-1)
    Keys.onRightPressed: move(1)
    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: tabs.line }
    Row {
        anchors.fill: parent
        spacing: 12
        Repeater {
            model: tabs.choices
            Item {
                required property var modelData
                readonly property bool selected: modelData.id === tabs.current
                width: Math.min(Math.max(90, label.implicitWidth + 24), (tabs.width - 12 * (tabs.choices.length - 1)) / tabs.choices.length)
                height: tabs.height
                activeFocusOnTab: true
                Accessible.role: Accessible.PageTab
                Accessible.name: label.text
                Accessible.selected: selected
                Keys.onReturnPressed: tabs.chosen(modelData.id)
                Keys.onSpacePressed: tabs.chosen(modelData.id)
                Rectangle { anchors.fill: parent; color: Qt.alpha(tabs.gold, parent.activeFocus ? 0.12 : 0) }
                Text {
                    id: label
                    anchors.centerIn: parent
                    width: parent.width - 16
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    text: Eitr.I18n.tr(parent.modelData.label)
                    color: parent.selected ? tabs.gold : tabs.muted
                    font.family: tabs.carved ? SiteStyle.carved : DesktopFonts.family
                    font.pixelSize: tabs.carved ? 11 : PanelStyle.bodySize
                    font.letterSpacing: tabs.carved ? 0.8 : 0
                    font.capitalization: tabs.carved ? Font.AllUppercase : Font.MixedCase
                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 2; visible: parent.selected; color: tabs.gold }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { parent.forceActiveFocus(); tabs.chosen(parent.modelData.id); } }
            }
        }
    }
}
