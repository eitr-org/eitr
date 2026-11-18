import QtQuick
import Eitr as Eitr

// Shared password field helpers and keyboard layout switcher for every lockscreen
// and SDDM login design. Provides the show-password eye button inside the field,
// Ctrl+U to clear, Ctrl+Backspace to delete the previous word, and the keyboard
// layout chip next to the field (click or Ctrl+Alt+Space) when multiple layouts exist.
Item {
    id: controls
    objectName: "passwordControls"

    required property var controller
    required property Item input
    property real unit: 1
    property color ink: "#ffffff"
    property color surface: "transparent"
    property color borderColor: Qt.alpha(ink, 0.22)
    property real borderWidth: 1 * unit
    property string fontFamily: "JetBrainsMono Nerd Font"
    property real cornerRadius: chipHeight / 2
    property real rightOffset: 8 * unit
    property bool underlineChip: false
    property bool revealed: false

    readonly property bool eyeVisible: true
    readonly property bool chipVisible: !!controller && controller.canSwitchLayout
    readonly property string layoutCode: controller ? controller.layoutCode : ""
    readonly property string layoutLabel: controller ? controller.layoutLabel : ""
    readonly property real chipGap: 8 * unit
    readonly property real chipHeight: parent ? parent.height : 40 * unit
    readonly property real chipWidth: chipVisible ? Math.max(chipHeight, chipText.implicitWidth + 20 * unit) : 0
    readonly property real outerWidth: chipVisible ? chipWidth + chipGap : 0
    readonly property real eyeSize: Math.min(chipHeight, 30 * unit)
    readonly property real rightReserve: rightOffset + eyeSize + 6 * unit

    x: 0
    y: 0
    width: (parent ? parent.width : 0) + outerWidth
    height: chipHeight
    z: 10

    onRevealedChanged: syncEchoMode()
    onInputChanged: syncEchoMode()
    Component.onCompleted: syncEchoMode()

    function syncEchoMode() {
        if (!input) return;
        input.echoMode = revealed ? TextInput.Normal : TextInput.Password;
    }

    function toggleReveal() {
        revealed = !revealed;
        if (input) input.forceActiveFocus();
    }

    function resetReveal() {
        revealed = false;
    }

    function switchLayout() {
        if (controller) controller.nextLayout();
        if (input) input.forceActiveFocus();
    }

    function clearInput() {
        if (!input) return;
        input.text = "";
    }

    function isWordCharacter(character) {
        if (!character || /\s/.test(character)) return false;
        return /[A-Za-z0-9_]/.test(character)
            || character.toLowerCase() !== character.toUpperCase()
            || character.charCodeAt(0) > 127;
    }

    function previousWordStart(text, cursor) {
        const limit = Math.max(0, Math.min(Number(cursor) || 0, text.length));
        let index = limit;
        while (index > 0 && !isWordCharacter(text.charAt(index - 1)))
            index--;
        while (index > 0 && isWordCharacter(text.charAt(index - 1)))
            index--;
        return index;
    }

    function deletePreviousWord() {
        if (!input) return;
        const text = String(input.text || "");
        if (text.length === 0) return;
        const cursor = typeof input.cursorPosition === "number"
            ? Math.max(0, Math.min(input.cursorPosition, text.length)) : text.length;
        if (cursor <= 0) return;
        const start = previousWordStart(text, cursor);
        if (typeof input.remove === "function") {
            input.remove(start, cursor);
        } else {
            input.text = text.slice(0, start) + text.slice(cursor);
            input.cursorPosition = start;
        }
    }

    function handleKey(event) {
        if (!event) return false;
        const modifiers = event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier | Qt.MetaModifier);
        if (event.key === Qt.Key_Space && modifiers === (Qt.ControlModifier | Qt.AltModifier)) {
            switchLayout();
            event.accepted = true;
            return true;
        }
        if (event.key === Qt.Key_U && modifiers === Qt.ControlModifier) {
            clearInput();
            event.accepted = true;
            return true;
        }
        if (event.key === Qt.Key_Backspace && modifiers === Qt.ControlModifier) {
            deletePreviousWord();
            event.accepted = true;
            return true;
        }
        return false;
    }

    Keys.onPressed: event => handleKey(event)

    Shortcut {
        sequence: "Ctrl+Alt+Space"
        enabled: controls.chipVisible && (!controls.input || !controls.input.activeFocus)
        onActivated: controls.switchLayout()
    }

    Connections {
        target: controls.controller
        function onLoginSubmitted() { controls.resetReveal(); }
        function onLoginFailed() { controls.resetReveal(); }
        function onLoginSucceeded() { controls.resetReveal(); }
        function onUserIndexChanged() { controls.resetReveal(); }
    }

    Connections {
        target: controls.input
        function onAccepted() { controls.resetReveal(); }
    }

    Item {
        id: eyeButton
        objectName: "passwordEyeButton"
        width: controls.eyeSize
        height: controls.eyeSize
        x: (controls.parent ? controls.parent.width : 0) - controls.rightOffset - width
        anchors.verticalCenter: parent.verticalCenter
        Accessible.role: Accessible.Button
        Accessible.name: controls.revealed ? Eitr.I18n.tr("Hide password") : Eitr.I18n.tr("Show password")

        Text {
            anchors.centerIn: parent
            text: controls.revealed ? "\uf070" : "\uf06e"
            color: controls.ink
            opacity: controls.revealed || eyeMouse.containsMouse ? 1.0 : 0.62
            font.family: controls.fontFamily
            font.pixelSize: Math.round(14 * controls.unit)
        }

        MouseArea {
            id: eyeMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: controls.toggleReveal()
        }
    }

    Rectangle {
        id: layoutChip
        objectName: "keyboardLayoutChip"
        visible: controls.chipVisible
        x: (controls.parent ? controls.parent.width : 0) + controls.chipGap
        y: 0
        width: controls.chipWidth
        height: controls.chipHeight
        radius: controls.underlineChip ? 0 : controls.cornerRadius
        color: controls.underlineChip ? "transparent" : (chipMouse.containsMouse ? Qt.alpha(controls.ink, 0.14) : controls.surface)
        border.color: controls.underlineChip ? "transparent" : controls.borderColor
        border.width: controls.underlineChip ? 0 : controls.borderWidth
        Accessible.role: Accessible.Button
        Accessible.name: Eitr.I18n.tr("Keyboard · {layout}", {layout: controls.layoutLabel || controls.layoutCode})

        Rectangle {
            visible: controls.underlineChip
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1 * controls.unit
            color: controls.borderColor
        }

        Text {
            id: chipText
            anchors.centerIn: parent
            text: controls.layoutCode
            color: controls.ink
            opacity: chipMouse.containsMouse ? 1.0 : 0.85
            font.family: controls.fontFamily
            font.pixelSize: Math.round(12 * controls.unit)
            font.bold: true
            font.letterSpacing: 1 * controls.unit
        }

        MouseArea {
            id: chipMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: controls.switchLayout()
        }
    }
}
