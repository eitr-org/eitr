pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

FocusScope {
    id: chat
    required property color foreground
    required property color background
    property var assistant: ({})
    property alias draft: input.text
    property var helperCommand: ["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/assistant-chat.py")]
    property var turns: []
    property string error: ""
    property bool accepting: false
    property bool requestPending: false
    property var response: ({})
    readonly property bool thinking: requestPending && accepting
    signal closed()
    function reset() {
        accepting = false;
        request.running = false;
        turns = [];
        response = ({});
        error = "";
        input.text = "";
    }
    function focusInput() { input.forceActiveFocus(); }
    function send() {
        if (requestPending || !input.text.trim()) return;
        error = "";
        turns = turns.concat([{role: "user", text: input.text.trim()}]);
        input.text = "";
        accepting = true;
        requestPending = true;
        request.running = true;
    }
    function scrollToEnd() { Qt.callLater(function() { messages.positionViewAtEnd(); }); }
    onTurnsChanged: scrollToEnd()
    onThinkingChanged: scrollToEnd()
    Keys.onEscapePressed: { reset(); closed(); }
    Component.onDestruction: { accepting = false; request.running = false; }
    Process {
        id: request
        command: chat.helperCommand
        stdinEnabled: true
        onStarted: { write(JSON.stringify({identifier: chat.assistant.identifier, turns: chat.turns}) + "\n"); stdinEnabled = false; }
        stdout: SplitParser {
            onRead: function(data) {
                if (!chat.accepting) return;
                try { chat.response = JSON.parse(data); }
                catch (error) { chat.response = {error: Eitr.I18n.tr("Invalid assistant response.")}; }
            }
        }
        onExited: function(exitCode) {
            chat.requestPending = false;
            stdinEnabled = true;
            if (!chat.accepting) return;
            chat.accepting = false;
            try {
                const result = chat.response;
                chat.response = ({});
                if (result.error) chat.error = result.error;
                else if (exitCode === 0 && typeof result.answer === "string")
                    chat.turns = chat.turns.concat([{role: "assistant", text: result.answer}]);
                else chat.error = Eitr.I18n.tr("Invalid assistant response.");
            } catch (error) { chat.error = Eitr.I18n.tr("Invalid assistant response."); }
            // A failed request remains editable; the next send still has alternating turns.
            if (chat.error && chat.turns.length && chat.turns[chat.turns.length - 1].role === "user") {
                input.text = chat.turns[chat.turns.length - 1].text;
                chat.turns = chat.turns.slice(0, -1);
            }
        }
    }
    ColumnLayout {
        anchors.fill: parent; spacing: 10
        RowLayout {
            Layout.fillWidth: true
            PanelButton { foreground: chat.foreground; icon: true; text: "󰁍"; Accessible.name: Eitr.I18n.tr("Back"); onClicked: { chat.reset(); chat.closed(); } }
            Text { Layout.fillWidth: true; text: chat.assistant.name || ""; color: chat.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize; elide: Text.ElideRight }
            PanelButton {
                id: newChat
                objectName: "newChatButton"
                Layout.preferredWidth: Math.min(chat.width * 0.6, newChatMetrics.advanceWidth + 16)
                foreground: chat.foreground; text: Eitr.I18n.tr("New chat")
                TextMetrics { id: newChatMetrics; text: newChat.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                onClicked: { chat.reset(); input.forceActiveFocus(); }
            }
        }
        ListView {
            id: messages
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true; spacing: 10
            model: chat.turns
            onContentHeightChanged: chat.scrollToEnd()
            delegate: Item {
                id: message
                required property var modelData
                width: messages.width
                height: bubble.height
                HoverHandler { id: messageHover }
                Rectangle {
                    id: bubble
                    x: message.modelData.role === "user" ? message.width - width : 0
                    width: message.width * 0.94
                    height: messageBody.implicitHeight + 16
                    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                    color: Qt.alpha(chat.foreground, message.modelData.role === "user" ? 0.1 : 0.04)
                    Column {
                        id: messageBody
                        x: 8; y: 8; width: parent.width - 16; spacing: 4
                        TextEdit {
                            // Replies leave room for the copy icon in the top-right corner.
                            width: parent.width - (message.modelData.role === "assistant" ? copyReply.width : 0); height: contentHeight
                            text: message.modelData.role === "assistant" ? message.modelData.text.replace(/!\[/g, "[").replace(/</g, "&lt;") : message.modelData.text
                            textFormat: message.modelData.role === "assistant" ? Text.MarkdownText : Text.PlainText
                            readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap
                            color: chat.foreground; selectedTextColor: chat.background; selectionColor: chat.foreground
                            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                        }
                    }
                    PanelButton {
                        id: copyReply
                        property bool copied: false
                        visible: message.modelData.role === "assistant" && (messageHover.hovered || copied)
                        anchors.top: parent.top; anchors.right: parent.right; anchors.margins: 4
                        icon: true; width: 24; height: 24; iconSize: 14; foreground: chat.foreground
                        text: copied ? "\u{F012C}" : "\u{F018F}"
                        Accessible.name: Eitr.I18n.tr("Copy reply")
                        onClicked: { Quickshell.clipboardText = message.modelData.text; copied = true; copiedTimer.restart(); }
                        Timer { id: copiedTimer; interval: 1500; onTriggered: copyReply.copied = false }
                        HoverHandler { id: copyHover }
                        BarTooltip { target: copyReply; hovered: copyHover.hovered; text: copyReply.copied ? Eitr.I18n.tr("Copied") : Eitr.I18n.tr("Copy reply"); foreground: chat.foreground; background: chat.background }
                    }
                }
            }
            ScrollBar.vertical: ScrollBar {}
        }
        Text {
            visible: chat.thinking || chat.error !== ""
            Layout.fillWidth: true; wrapMode: Text.Wrap
            text: chat.thinking ? Eitr.I18n.tr("Thinking…") : chat.error
            color: chat.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        RowLayout {
            Layout.fillWidth: true
            // Starts as tall as Send and grows with the text up to five lines, then scrolls.
            ScrollView {
                Layout.fillWidth: true; Layout.alignment: Qt.AlignBottom
                Layout.preferredHeight: Math.min(input.lineHeight * 5 + input.topPadding + input.bottomPadding,
                                                 Math.max(sendButton.height, input.implicitHeight))
                TextArea {
                    id: input
                    readonly property real lineHeight: Math.ceil(fontMetrics.height)
                    FontMetrics { id: fontMetrics; font: input.font }
                    topPadding: Math.max(0, Math.floor((sendButton.height - lineHeight) / 2)); bottomPadding: topPadding
                    leftPadding: 10; rightPadding: 10
                    readOnly: chat.requestPending
                    placeholderText: Eitr.I18n.tr("Ask anything…")
                    color: chat.foreground; placeholderTextColor: Qt.alpha(chat.foreground, PanelStyle.secondaryTextOpacity)
                    wrapMode: TextEdit.Wrap; selectByMouse: true
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    background: Rectangle { color: Qt.alpha(chat.foreground, 0.06); radius: DesktopStyle.radius(PanelStyle.controlRadius) }
                    Keys.onPressed: function(event) {
                        if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && !(event.modifiers & Qt.ShiftModifier)) {
                            event.accepted = true; chat.send();
                        }
                    }
                }
            }
            PanelButton { id: sendButton; Layout.alignment: Qt.AlignBottom; foreground: chat.foreground; text: Eitr.I18n.tr("Send"); available: !chat.requestPending && input.text.trim() !== ""; onClicked: chat.send() }
        }
        Text {
            Layout.fillWidth: true; wrapMode: Text.Wrap
            text: chat.assistant.local ? Eitr.I18n.tr("Runs on this PC; nothing is saved") : Eitr.I18n.tr("Messages go to %1; nothing is saved", [chat.assistant.provider || ""])
            color: chat.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
    }
}
