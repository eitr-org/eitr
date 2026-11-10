import ".."
import QtQuick
import QtQuick.Controls.Basic
import "../PanelStyle.js" as PanelStyle

// A text field in the outlined field style, with its floating label and helper text.
Item {
    id: field
    required property color foreground
    property color accent: foreground
    property string label: ""
    property string helperText: ""
    property alias text: input.text
    property alias input: input
    signal accepted()
    signal cancelled()
    // Room above the field for the raised label, as for outlined dropdowns.
    readonly property real labelRoom: 8
    implicitHeight: labelRoom + input.height + (helperText !== "" ? 4 + helper.implicitHeight + 4 : 0)
    height: implicitHeight
    function forceActiveFocus() { input.forceActiveFocus(); }
    function selectAll() { input.selectAll(); }
    TextField {
        id: input
        y: field.labelRoom
        width: parent.width
        height: 48
        leftPadding: 14; rightPadding: 14
        color: field.foreground
        selectionColor: Qt.alpha(field.accent, 0.35)
        selectedTextColor: field.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
        verticalAlignment: TextInput.AlignVCenter
        Accessible.name: field.label
        background: Item {}
        onAccepted: field.accepted()
        Keys.onEscapePressed: field.cancelled()
    }
    OutlinedFrame {
        y: input.y
        width: input.width; height: input.height
        label: field.label
        raised: input.activeFocus || input.text !== ""
        active: input.activeFocus
        foreground: field.foreground
        accent: field.accent
    }
    Text {
        id: helper
        visible: text !== ""
        y: input.y + input.height + 4
        x: 14
        width: parent.width - 28
        text: field.helperText
        color: field.foreground
        opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family
        font.pixelSize: 11
        wrapMode: Text.WordWrap
    }
}
