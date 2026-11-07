import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// One choice from a list. The closed control is a single row; its list floats over the
// content below (or above, when there is more room there) at the row's width, so opening
// it never changes the size of the card or panel that holds it.
Item {
    id: control
    required property color foreground
    property color background: "#20242c"
    property color gold: foreground
    // Each choice is {value|id|key|name, label, glyph?, available?} or a plain string.
    property var choices: []
    property string current: ""
    property bool available: true
    property string accessibleName: ""
    // With a label, the closed control is a settings row: the label on the left and the
    // current choice on the right, so the row itself is the selector.
    property string label: ""
    // Shown when no choice matches current.
    property string placeholder: Eitr.I18n.tr("Unavailable")
    // An optional per-row action (for example Rename), shown on the hovered or highlighted row.
    property string actionGlyph: ""
    property string actionName: ""
    property bool expanded: false
    property int highlightedIndex: currentIndex
    // True after Up/Down moved the highlight, false after the pointer did.
    property bool keyboardHighlight: false
    property int visibleRows: 8
    readonly property int currentIndex: choices.findIndex(choice => valueOf(choice) === current)
    readonly property alias popup: menu
    readonly property bool opensUpward: menu.upward
    signal chosen(string value)
    signal actionTriggered(string value)
    width: parent ? parent.width : 220
    implicitHeight: button.height
    height: implicitHeight
    activeFocusOnTab: true
    onActiveFocusChanged: if (activeFocus) button.forceActiveFocus()
    enabled: available && choices.length > 0
    onEnabledChanged: if (!enabled) expanded = false
    onExpandedChanged: {
        if (expanded) {
            highlightedIndex = currentIndex;
            keyboardHighlight = false;
            menu.place();
            menu.open();
            list.positionViewAtIndex(Math.max(0, highlightedIndex), ListView.Contain);
        } else menu.close();
    }
    Keys.onEscapePressed: event => { if (expanded) { expanded = false; button.forceActiveFocus(); event.accepted = true; } else event.accepted = false; }
    function valueOf(choice) { return String(choice.value ?? choice.id ?? choice.key ?? choice.name ?? choice); }
    function labelOf(choice) { return Eitr.I18n.tr(String(choice.label ?? choice.name ?? choice)); }
    function glyphOf(choice) { return choice && choice.glyph ? String(choice.glyph) : ""; }
    function move(delta) {
        expanded = true;
        keyboardHighlight = true;
        for (let step = 0; step < choices.length; step++) {
            highlightedIndex = (highlightedIndex + delta + choices.length) % choices.length;
            if (choices[highlightedIndex].available !== false) break;
        }
        list.positionViewAtIndex(highlightedIndex, ListView.Contain);
    }
    function commit(index) {
        if (index >= 0 && index < choices.length && choices[index].available !== false) {
            if (valueOf(choices[index]) !== current) chosen(valueOf(choices[index]));
            expanded = false;
            button.forceActiveFocus();
        }
    }
    function triggerAction(index) {
        const value = valueOf(choices[index]);
        expanded = false;
        actionTriggered(value);
    }
    // The area the list must stay inside: a bar panel's own surface (its window only takes
    // input there), otherwise the whole window, Settings and panels embedded in it included.
    function bounds() {
        for (let item = control.parent; item; item = item.parent)
            if (item.attachmentTarget !== undefined && item.embedded === false) return item;
        return control.Window.contentItem;
    }
    PanelButton {
        id: button
        width: parent.width
        height: PanelStyle.selectionRowHeight
        foreground: control.foreground
        textAlignment: Text.AlignLeft
        selected: control.expanded
        readonly property var currentChoice: control.currentIndex >= 0 ? control.choices[control.currentIndex] : null
        readonly property string currentText: currentChoice ? control.labelOf(currentChoice) : control.placeholder
        readonly property string currentGlyph: control.glyphOf(currentChoice)
        leadingIcon: control.label === "" ? currentGlyph : ""
        text: control.label || currentText
        Accessible.name: control.accessibleName || control.label || text
        Accessible.role: Accessible.ComboBox
        activeFocusOnTab: true
        Keys.onDownPressed: control.move(1)
        Keys.onUpPressed: control.move(-1)
        Keys.onEscapePressed: event => { if (control.expanded) { control.expanded = false; event.accepted = true; } else event.accepted = false; }
        // Activating the open selector chooses a row only when the keyboard highlighted it;
        // a row the pointer merely passed over is never applied, the list just closes.
        onClicked: {
            if (!control.expanded) control.expanded = true;
            else if (control.keyboardHighlight) control.commit(control.highlightedIndex);
            else control.expanded = false;
        }
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
    Popup {
        id: menu
        objectName: "choiceDropdownMenu"
        readonly property real gap: 4
        readonly property real edgeMargin: 8
        readonly property real rowsHeight: Math.min(control.choices.length, control.visibleRows) * (PanelStyle.selectionRowHeight + PanelStyle.selectionRowGap) - PanelStyle.selectionRowGap
        property bool upward: false
        readonly property bool scrolls: control.choices.length > control.visibleRows || rowsHeight + topPadding + bottomPadding > height + 0.5
        property real room: rowsHeight + topPadding + bottomPadding
        // Below the button when the list fits there or that side has more room, else above it.
        function place() {
            const area = control.bounds();
            const wanted = rowsHeight + topPadding + bottomPadding;
            if (!area) { upward = false; room = wanted; return; }
            const top = button.mapToItem(area, 0, 0).y;
            const below = area.height - top - button.height - gap - edgeMargin;
            const above = top - gap - edgeMargin;
            upward = below < wanted && above > below;
            room = Math.max(PanelStyle.selectionRowHeight + topPadding + bottomPadding, Math.min(wanted, upward ? above : below));
        }
        x: 0
        y: upward ? -height - gap : button.height + gap
        width: control.width
        height: Math.min(rowsHeight + topPadding + bottomPadding, room)
        padding: 4
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        onClosed: control.expanded = false
        enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: DesktopStyle.motionDuration(120) } }
        exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: DesktopStyle.motionDuration(90) } }
        background: Rectangle {
            radius: DesktopStyle.radius(PanelStyle.controlRadius + 4)
            color: Qt.rgba(control.background.r, control.background.g, control.background.b, 1)
            border.width: 1
            border.color: Qt.alpha(control.foreground, PanelStyle.selectionBorderAlpha)
        }
        contentItem: ListView {
            id: list
            clip: true
            model: control.choices
            spacing: PanelStyle.selectionRowGap
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { policy: menu.scrolls ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff }
            delegate: PanelButton {
                id: row
                required property var modelData
                required property int index
                width: list.width - (menu.scrolls ? 10 : 0)
                height: PanelStyle.selectionRowHeight
                foreground: selected ? control.gold : control.foreground
                readonly property bool highlighted: control.highlightedIndex === index || rowHover.hovered
                color: Qt.alpha(control.foreground, PanelStyle.selectionAlpha(selected, highlighted))
                border.width: PanelStyle.selectionBorderWidth(selected)
                border.color: Qt.alpha(control.foreground, PanelStyle.selectionBorderAlpha)
                textAlignment: Text.AlignLeft
                leadingIcon: control.glyphOf(modelData)
                text: (control.glyphOf(modelData) !== "" ? "" : selected ? "✓  " : "    ") + control.labelOf(modelData)
                selected: control.currentIndex === index
                available: modelData.available !== false
                activeFocusOnTab: false
                Accessible.role: Accessible.RadioButton
                Accessible.checked: selected
                onClicked: control.commit(index)
                HoverHandler { id: rowHover; onHoveredChanged: if (hovered) { control.highlightedIndex = row.index; control.keyboardHighlight = false; } }
                Text {
                    visible: row.selected && control.glyphOf(row.modelData) !== ""
                    anchors.right: rowAction.visible ? rowAction.left : parent.right
                    anchors.rightMargin: PanelStyle.selectionInset
                    anchors.verticalCenter: parent.verticalCenter
                    text: "✓"; color: control.gold
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                PanelButton {
                    id: rowAction
                    anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset
                    anchors.verticalCenter: parent.verticalCenter
                    width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight
                    visible: control.actionGlyph !== "" && row.highlighted
                    icon: true; iconSize: 14; text: control.actionGlyph
                    foreground: control.foreground
                    activeFocusOnTab: false
                    Accessible.name: control.actionName
                    onClicked: control.triggerAction(row.index)
                }
            }
        }
    }
}
