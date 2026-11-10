import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
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
    // Each choice is {value|id|key|name, label, glyph?, palette?, available?} or a plain string;
    // a palette is a list of colours shown as small filled circles beside the label.
    property var choices: []
    property string current: ""
    property bool available: true
    property string accessibleName: ""
    // With a label, the closed control is a settings row: the label on the left and the
    // current choice on the right, so the row itself is the selector.
    property string label: ""
    // Outlined field: the label sits inside the empty field and moves into its top border
    // once a choice is shown or the list opens; the helper text describes it underneath.
    property string floatingLabel: ""
    property string helperText: ""
    readonly property bool outlined: floatingLabel !== ""
    readonly property bool labelRaised: expanded || currentIndex >= 0
    // Room above the field for the raised label, so stacked fields never touch.
    readonly property real labelRoom: outlined ? 8 : 0
    // Shown when no choice matches current.
    property string placeholder: Eitr.I18n.tr("Unavailable")
    // An optional per-row action (for example Rename), shown on the hovered or highlighted row.
    property string actionGlyph: ""
    property string actionName: ""
    property bool expanded: false
    property int highlightedIndex: currentIndex
    // True after Up/Down moved the highlight, false after the pointer did.
    property bool keyboardHighlight: false
    property point pointerPosition: Qt.point(-1, -1)
    property string typeBuffer: ""
    property double lastTypedAt: 0
    readonly property var popupHost: control.QsWindow.window
    property var registeredHost: null
    function registerPopup(open) {
        if (registeredHost) {
            registeredHost.choicePopups = registeredHost.choicePopups.filter(item => item !== menu.background);
            registeredHost = null;
        }
        if (open && popupHost && popupHost.choicePopups !== undefined) {
            registeredHost = popupHost;
            registeredHost.choicePopups = registeredHost.choicePopups.concat([menu.background]);
        }
    }
    Component.onDestruction: registerPopup(false)
    function normalized(text) { return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase(); }
    function typeAhead(event) {
        event.accepted = false;
        if (!event.text || event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)
                || !/[^\s\x00-\x1f]/.test(event.text)) return;
        const typed = normalized(event.text);
        const now = Date.now();
        const recent = now - lastTypedAt < 800;
        const cycle = recent && typeBuffer === typed;
        typeBuffer = recent && !cycle ? typeBuffer + typed : typed;
        lastTypedAt = now;
        expanded = true;
        const start = cycle ? highlightedIndex + 1 : 0;
        for (let offset = 0; offset < choices.length; offset++) {
            const index = (start + offset) % choices.length;
            if (choices[index].available !== false && normalized(labelOf(choices[index])).startsWith(typeBuffer)) {
                highlightedIndex = index;
                keyboardHighlight = true;
                list.positionViewAtIndex(index, ListView.Contain);
                break;
            }
        }
        event.accepted = true;
    }
    property int visibleRows: 8
    readonly property int currentIndex: choices.findIndex(choice => valueOf(choice) === current)
    readonly property alias popup: menu
    readonly property bool opensUpward: menu.upward
    signal chosen(string value)
    signal actionTriggered(string value)
    width: parent ? parent.width : 220
    implicitHeight: labelRoom + button.height + (outlined && helperText !== "" ? 4 + helperLine.implicitHeight + 4 : 0)
    height: implicitHeight
    activeFocusOnTab: true
    onActiveFocusChanged: if (activeFocus) button.forceActiveFocus()
    enabled: available && choices.length > 0
    onEnabledChanged: if (!enabled) expanded = false
    onVisibleChanged: if (!visible) expanded = false
    onPopupHostChanged: if (expanded) expanded = false
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
    // List rows receive choices through the list model, which turns arrays into Qt lists.
    function paletteOf(choice) { return choice && choice.palette && choice.palette.length !== undefined ? Array.from(choice.palette) : []; }
    component Swatches: Row {
        id: swatchRow
        property var colors: []
        spacing: 3
        Repeater {
            model: swatchRow.colors
            Rectangle {
                required property string modelData
                width: 10; height: 10; radius: 5
                color: modelData
                border.width: 1
                border.color: Qt.alpha(control.foreground, 0.25)
            }
        }
    }
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
    // Lists use the whole window; bar windows include them in their input region.
    function bounds() { return control.Window.contentItem; }
    PanelButton {
        id: button
        y: control.labelRoom
        width: parent.width
        height: control.outlined ? 48 : PanelStyle.selectionRowHeight
        foreground: control.foreground
        textAlignment: Text.AlignLeft
        flat: control.outlined
        // The value lines up with the floating label above it.
        textInset: control.outlined ? 14 : 8
        // Focus shows as the gold border, so a chosen field is not left filled.
        focusFill: !control.outlined
        selected: control.expanded && !control.outlined
        readonly property var currentChoice: control.currentIndex >= 0 ? control.choices[control.currentIndex] : null
        readonly property string currentText: currentChoice ? control.labelOf(currentChoice) : control.placeholder
        readonly property string currentGlyph: control.glyphOf(currentChoice)
        leadingIcon: control.label === "" ? currentGlyph : ""
        text: control.outlined ? (control.currentIndex >= 0 ? currentText : "") : control.label || currentText
        Accessible.name: control.accessibleName || control.floatingLabel || control.label || text
        Accessible.role: Accessible.ComboBox
        activeFocusOnTab: true
        Keys.onPressed: event => control.typeAhead(event)
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
        // One chevron, centred on its drawn shape, turned over while the list is open; two
        // different glyphs sat at different heights and the arrow jumped.
        Swatches {
            visible: control.outlined
            anchors.right: chevron.left; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
            colors: control.paletteOf(button.currentChoice)
        }
        Item {
            id: chevron
            anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
            width: 14; height: 14
            rotation: control.expanded ? 180 : 0
            Behavior on rotation { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
            TextMetrics { id: chevronInk; text: chevronGlyph.text; font: chevronGlyph.font }
            Text {
                id: chevronGlyph
                x: parent.width / 2 - (chevronInk.tightBoundingRect.x + chevronInk.tightBoundingRect.width / 2)
                y: parent.height / 2 - (baselineOffset + chevronInk.tightBoundingRect.y + chevronInk.tightBoundingRect.height / 2)
                text: "⌄"; color: control.foreground
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            }
        }
        Text {
            visible: control.label !== ""
            anchors.right: chevron.left; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter
            width: Math.max(0, parent.width * 0.6)
            horizontalAlignment: Text.AlignRight; elide: Text.ElideRight
            text: button.currentText; color: control.foreground; opacity: 0.75
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
    }
    // The outlined field's border and floating label; neither takes input.
    OutlinedFrame {
        visible: control.outlined
        y: button.y
        width: button.width; height: button.height
        label: control.floatingLabel
        raised: control.labelRaised
        active: control.expanded || button.activeFocus
        foreground: control.foreground
        accent: control.gold
    }
    Text {
        id: helperLine
        visible: control.outlined && text !== ""
        y: button.y + button.height + 4
        x: 14
        width: parent.width - 28
        text: control.helperText
        color: control.foreground
        opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family
        font.pixelSize: 11
        wrapMode: Text.WordWrap
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
        y: upward ? button.y - height - gap : button.y + button.height + gap
        width: control.width
        height: Math.min(rowsHeight + topPadding + bottomPadding, room)
        padding: 4
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        focus: true
        onOpened: list.forceActiveFocus()
        onAboutToShow: control.registerPopup(true)
        onAboutToHide: control.registerPopup(false)
        onClosed: { control.expanded = false; control.typeBuffer = ""; control.lastTypedAt = 0; }
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
            focus: true
            Keys.onPressed: event => control.typeAhead(event)
            Keys.onDownPressed: control.move(1)
            Keys.onUpPressed: control.move(-1)
            Keys.onReturnPressed: control.commit(control.highlightedIndex)
            Keys.onEnterPressed: control.commit(control.highlightedIndex)
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
                // The selected row is marked by its background alone.
                text: control.labelOf(modelData)
                // Outlined fields line their rows up with the value (list padding 4 + 10).
                textInset: control.outlined ? 10 : 8
                selected: control.currentIndex === index
                available: modelData.available !== false
                activeFocusOnTab: false
                Accessible.role: Accessible.RadioButton
                Accessible.checked: selected
                Keys.onReturnPressed: control.commit(control.highlightedIndex)
                Keys.onEnterPressed: control.commit(control.highlightedIndex)
                Keys.onSpacePressed: control.commit(control.highlightedIndex)
                onClicked: control.commit(index)
                HoverHandler {
                    id: rowHover
                    onHoveredChanged: if (hovered && !control.keyboardHighlight) control.highlightedIndex = row.index
                    // Scrolling under a stationary pointer keeps the keyboard highlight.
                    onPointChanged: {
                        const position = point.scenePosition;
                        if (hovered && control.pointerPosition.x >= 0 && (position.x !== control.pointerPosition.x || position.y !== control.pointerPosition.y)) {
                            control.highlightedIndex = row.index;
                            control.keyboardHighlight = false;
                        }
                        if (hovered) control.pointerPosition = position;
                    }
                }
                Swatches {
                    anchors.right: rowAction.visible ? rowAction.left : parent.right
                    anchors.rightMargin: PanelStyle.selectionInset
                    anchors.verticalCenter: parent.verticalCenter
                    colors: control.paletteOf(row.modelData)
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
