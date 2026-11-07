import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: control
    required property color foreground
    property color background: "#20242c"
    property color gold: foreground
    property var choices: []
    property string current: ""
    property bool available: true
    property string accessibleName: ""
    // With a label, the closed control is a settings row: the label on the left and the
    // current choice on the right, so the row itself is the selector.
    property string label: ""
    property bool expanded: false
    property int highlightedIndex: currentIndex
    onExpandedChanged: if (expanded) highlightedIndex = currentIndex
    Keys.onEscapePressed: event => { if (expanded) { expanded = false; button.forceActiveFocus(); event.accepted = true; } else event.accepted = false; }
    readonly property int currentIndex: choices.findIndex(choice => valueOf(choice) === current)
    property int maximumListHeight: 216
    signal chosen(string value)
    width: parent ? parent.width : 220
    activeFocusOnTab: true
    onActiveFocusChanged: if (activeFocus) button.forceActiveFocus()
    spacing: 4
    enabled: available && choices.length > 0
    function valueOf(choice) { return String(choice.value ?? choice.id ?? choice.key ?? choice.name ?? choice); }
    function labelOf(choice) { return Eitr.I18n.tr(String(choice.label ?? choice.name ?? choice)); }
    function move(delta) {
        expanded = true;
        for (let step = 0; step < choices.length; step++) {
            highlightedIndex = (highlightedIndex + delta + choices.length) % choices.length;
            if (choices[highlightedIndex].available !== false) break;
        }
        list.positionViewAtIndex(highlightedIndex, ListView.Contain);
    }
    function commit(index) {
        if (index >= 0 && choices[index].available !== false) {
            if (valueOf(choices[index]) !== current) chosen(valueOf(choices[index]));
            expanded = false;
            button.forceActiveFocus();
        }
    }
    PanelButton {
        id: button
        width: parent.width
        height: PanelStyle.selectionRowHeight
        foreground: control.foreground
        textAlignment: Text.AlignLeft
        readonly property string currentText: control.currentIndex >= 0 ? control.labelOf(control.choices[control.currentIndex]) : Eitr.I18n.tr("Unavailable")
        text: control.label || currentText
        Accessible.name: control.accessibleName || control.label || text
        Accessible.role: Accessible.ComboBox
        activeFocusOnTab: true
        Keys.onDownPressed: control.move(1)
        Keys.onUpPressed: control.move(-1)
        Keys.onEscapePressed: event => { if (control.expanded) { control.expanded = false; event.accepted = true; } else event.accepted = false; }
        onClicked: { if (control.expanded) control.commit(control.highlightedIndex); else control.expanded = true; }
        Text { id: chevron; anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: control.expanded ? "⌃" : "⌄"; color: control.foreground }
        Text {
            visible: control.label !== ""
            anchors.right: chevron.left; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter
            width: Math.max(0, parent.width * 0.6)
            horizontalAlignment: Text.AlignRight; elide: Text.ElideRight
            text: button.currentText; color: control.foreground; opacity: 0.75
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
    }
    // The list participates in its host's layout and scrolling, including layer-shell panels.
    ListView {
        id: list
        width: parent.width
        height: visible ? Math.min(contentHeight, control.maximumListHeight) : 0
        visible: control.expanded
        clip: true
        model: control.choices
        spacing: PanelStyle.selectionRowGap
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        delegate: PanelButton {
            required property var modelData
            required property int index
            width: list.width
            height: PanelStyle.selectionRowHeight
            foreground: selected ? control.gold : control.foreground
            color: Qt.alpha(control.foreground, PanelStyle.selectionAlpha(selected, activeFocus || control.highlightedIndex === index))
            border.width: PanelStyle.selectionBorderWidth(selected)
            border.color: Qt.alpha(control.foreground, PanelStyle.selectionBorderAlpha)
            textAlignment: Text.AlignLeft
            text: (control.currentIndex === index ? "✓  " : "    ") + control.labelOf(modelData)
            selected: control.currentIndex === index
            available: modelData.available !== false
            activeFocusOnTab: true
            Accessible.role: Accessible.RadioButton
            Accessible.checked: selected
            Keys.onDownPressed: { button.forceActiveFocus(); control.move(1); }
            Keys.onUpPressed: { button.forceActiveFocus(); control.move(-1); }
            onClicked: control.commit(index)
        }
    }
}
