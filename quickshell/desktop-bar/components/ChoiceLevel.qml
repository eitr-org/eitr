import ".."
import QtQuick
import Eitr as Eitr

Item {
    id: level
    required property color foreground
    required property color accent
    property var choices: []
    property string current: ""
    property string accessibleName: ""
    property bool available: true
    signal chosen(string value)
    function valueOf(choice) {
        return String(choice.value ?? choice.id);
    }
    function commit() {
        if (choices.length)
            chosen(valueOf(choices[Math.round(slider.value)]));
    }
    width: parent ? parent.width : 240
    implicitHeight: 36
    height: implicitHeight
    PanelSlider {
        id: slider
        anchors.verticalCenter: parent.verticalCenter
        width: Math.max(0, parent.width - valueLabel.width - 8)
        from: 0
        to: Math.max(0, level.choices.length - 1)
        stepSize: 1
        enabled: level.available && level.choices.length > 0
        foreground: level.foreground
        accent: level.accent
        Accessible.name: level.accessibleName
        Binding {
            target: slider
            property: "value"
            value: Math.max(0, level.choices.findIndex(choice => level.valueOf(choice) === level.current))
            when: !slider.pressed
        }
        onMoved: if (!pressed)
            level.commit()
        onPressedChanged: if (!pressed)
            level.commit()
    }
    // The value column fits the longest choice ("Default (75%)"), so no label is cut off.
    Column {
        id: labelSizes
        visible: false
        Repeater {
            model: level.choices
            Text {
                required property var modelData
                text: Eitr.I18n.tr(String(modelData.label))
                font.family: DesktopFonts.family
                font.pixelSize: 11
            }
        }
    }
    Text {
        id: valueLabel
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: Math.min(level.width * 0.4, Math.max(78, labelSizes.implicitWidth))
        horizontalAlignment: Text.AlignRight
        text: level.choices.length ? Eitr.I18n.tr(level.choices[Math.round(slider.value)].label) : "—"
        color: level.foreground
        font.family: DesktopFonts.family
        font.pixelSize: 11
        elide: Text.ElideRight
    }
}
