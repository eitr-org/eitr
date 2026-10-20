pragma ComponentBehavior: Bound
import Eitr as Eitr
import QtQuick
import "CalculatorModel.js" as Model

// The calculator's face: display, carved-stone keys and keyboard input. shell.qml
// places it in a floating window; tests render it offscreen.
Item {
    id: calculator
    property color background: "#0a0b12"
    property color foreground: "#e4dcd2"
    property color accent: "#2bb87a"
    property string font: "JetBrainsMono Nerd Font"
    // Weathered bronze, the colour of the runestone ring on Eitr's wallpapers.
    readonly property color bronze: "#b08d57"
    property string expression: ""
    property string previous: ""
    property string message: ""
    readonly property var live: Model.evaluate(expression)
    readonly property string answer: expression === "" ? "0" : live.error === undefined ? Model.format(live.value) : ""
    signal copyRequested(string text)
    signal closeRequested()

    function press(key) {
        message = "";
        if (key === "AC") { expression = ""; previous = ""; return; }
        if (key === "⌫") { expression = expression.slice(0, -1); return; }
        if (key === "=") { equals(); return; }
        expression += key;
    }
    function equals() {
        if (expression === "") return;
        const result = Model.evaluate(expression);
        if (result.error !== undefined) { message = result.error; return; }
        previous = expression + " =";
        expression = Model.format(result.value).replace(/ /g, "");
    }
    function copy() {
        if (answer === "") return;
        copyRequested(answer.replace(/ /g, ""));
        message = "Copied " + answer;
    }
    Rectangle { anchors.fill: parent; color: calculator.background }

    Item {
        id: keys
        anchors.fill: parent
        focus: true
        Keys.onPressed: event => {
            const text = event.text;
            if (event.key === Qt.Key_Escape) { if (calculator.expression === "") calculator.closeRequested(); else calculator.press("AC"); }
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || text === "=") calculator.press("=");
            else if (event.key === Qt.Key_Backspace) calculator.press("⌫");
            else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_C) calculator.copy();
            else if (text === "*") calculator.press("×");
            else if (text === "/") calculator.press("÷");
            else if (text === "-") calculator.press("−");
            else if (text.length === 1 && "0123456789.,+()^%".includes(text)) calculator.press(text);
            else return;
            event.accepted = true;
        }
    }

    Column {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        // "Reikna", Old Norse for "to calculate", in Elder Futhark.
        Row {
            spacing: 10
            Text { text: "ᚱᛖᛁᚲᚾᚨ"; color: calculator.bronze; font.family: "Noto Sans Runic"; font.pixelSize: 18; font.letterSpacing: 4 }
            Text { text: Eitr.I18n.tr("Calculator"); color: calculator.foreground; opacity: 0.55; font.family: calculator.font; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter }
        }

        Rectangle {
            width: parent.width
            height: 112
            radius: 6
            color: Qt.rgba(1, 1, 1, 0.035)
            border.width: 1
            border.color: Qt.alpha(calculator.bronze, 0.35)
            Column {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 4
                Text {
                    width: parent.width; horizontalAlignment: Text.AlignRight; elide: Text.ElideLeft
                    text: calculator.message !== "" ? calculator.message : calculator.previous
                    color: calculator.message !== "" ? calculator.accent : calculator.foreground
                    opacity: calculator.message !== "" ? 1 : 0.5
                    font.family: calculator.font; font.pixelSize: 13
                }
                Text {
                    width: parent.width; horizontalAlignment: Text.AlignRight; elide: Text.ElideLeft
                    text: calculator.expression === "" ? " " : calculator.expression
                    color: calculator.foreground; opacity: 0.8
                    font.family: calculator.font; font.pixelSize: 16
                }
                Text {
                    width: parent.width; horizontalAlignment: Text.AlignRight; elide: Text.ElideLeft
                    text: calculator.answer === "" ? "…" : calculator.answer
                    color: calculator.foreground
                    font.family: calculator.font; font.pixelSize: 34; font.bold: true
                    fontSizeMode: Text.HorizontalFit; minimumPixelSize: 16
                    height: 42
                }
            }
        }

        Grid {
            id: pad
            columns: 4
            spacing: 8
            readonly property real keyWidth: (parent.width - 3 * spacing) / 4
            Repeater {
                model: ["AC", "⌫", "%", "÷", "7", "8", "9", "×", "4", "5", "6", "−", "1", "2", "3", "+",
                        "(", "0", ".", ")", "√", "^", "Copy", "="]
                // A carved stone: a darker face, a bronze rim and a lighter top edge.
                Rectangle {
                    id: key
                    required property string modelData
                    readonly property bool operator: "÷×−+%^√()".includes(modelData)
                    readonly property bool equals: modelData === "="
                    width: (calculator.width - 36 - 3 * 8) / 4
                    height: 52
                    radius: 5
                    color: key.equals ? calculator.accent
                        : press.pressed ? Qt.alpha(calculator.accent, 0.25)
                        : press.containsMouse ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(1, 1, 1, 0.05)
                    border.width: 1
                    border.color: key.equals ? calculator.accent : Qt.alpha(calculator.bronze, key.operator ? 0.55 : 0.28)
                    Rectangle {
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
                        height: 1
                        color: Qt.rgba(1, 1, 1, 0.08)
                        visible: !key.equals
                    }
                    Text {
                        anchors.centerIn: parent
                        text: key.modelData
                        color: key.equals ? calculator.background
                            : key.operator ? calculator.bronze : calculator.foreground
                        font.family: calculator.font
                        font.pixelSize: key.modelData.length > 2 ? 13 : 20
                        font.bold: key.equals
                    }
                    MouseArea {
                        id: press
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (parent.modelData === "Copy") calculator.copy();
                            else calculator.press(parent.modelData);
                            keys.forceActiveFocus();
                        }
                    }
                }
            }
        }
    }
}
