import ".."
import QtQuick
import QtQuick.Controls.Basic as Controls
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
    // The choice just made, held until the saved value catches up, so the handle never
    // springs back to the old stop while the change is applied.
    property string pending: ""
    function indexOf(value) {
        return Math.max(0, choices.findIndex(choice => valueOf(choice) === value));
    }
    function commit() {
        if (!choices.length)
            return;
        const value = valueOf(choices[Math.round(slider.value)]);
        if (value === (pending || current))
            return;
        pending = value;
        settle.restart();
        chosen(value);
    }
    onCurrentChanged: pending = ""
    Timer {
        id: settle
        interval: 5000
        onTriggered: level.pending = ""
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
        snapMode: Controls.Slider.SnapAlways
        ticks: level.choices.length
        enabled: level.available && level.choices.length > 0
        foreground: level.foreground
        accent: level.accent
        Accessible.name: level.accessibleName
        Binding {
            target: slider
            property: "value"
            value: level.indexOf(level.pending || level.current)
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
