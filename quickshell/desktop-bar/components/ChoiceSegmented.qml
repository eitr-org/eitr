import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle
import Eitr as Eitr

Rectangle {
    property color gold: foreground
    id: control
    property color background: "#20242c"
    required property color foreground
    property var choices: []
    property string current: ""
    property bool available: true
    signal chosen(string value)
    width: parent ? parent.width : 240
    height: PanelStyle.selectionRowHeight
    radius: DesktopStyle.radius(5)
    color: Qt.alpha(foreground, 0.04)
    border.width: 1
    border.color: Qt.alpha(foreground, 0.15)
    Row {
        anchors.fill: parent
        anchors.margins: 3
        spacing: 2
        Repeater {
            model: control.choices
            Rectangle {
                id: segment
                required property var modelData
                readonly property string value: String(modelData.id ?? modelData.value ?? modelData.key ?? modelData)
                readonly property bool selected: value === control.current
                width: (control.width - 6 - 2 * (control.choices.length - 1)) / control.choices.length
                height: control.height - 6
                radius: DesktopStyle.radius(3)
                color: Qt.alpha(control.foreground, selected ? 0.17 : pointer.containsMouse ? 0.08 : 0)
                activeFocusOnTab: true
                enabled: control.available && modelData.available !== false
                opacity: enabled ? 1 : 0.45
                Accessible.role: Accessible.RadioButton
                Accessible.name: label.text
                Accessible.checked: selected
                Keys.onSpacePressed: control.chosen(value)
                Keys.onReturnPressed: control.chosen(value)
                Text {
                    id: label
                    anchors.fill: parent
                    anchors.margins: 3
                    text: Eitr.I18n.tr(String(segment.modelData.label ?? segment.modelData))
                    color: segment.selected ? control.gold : control.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                MouseArea {
                    id: pointer
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: control.chosen(segment.value)
                }
            }
        }
    }
}
