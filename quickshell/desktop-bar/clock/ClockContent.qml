import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The Clock: a chronograph dial with the chosen page around it, and Timers, Stopwatch
// and Focus switched from the row at the bottom.
Rectangle {
    id: content
    required property color foreground
    required property color background
    required property color accent
    property bool opened: false
    property string page: "timers"
    property bool live: true
    signal closeRequested()

    readonly property var pages: [
        {id: "timers", title: Eitr.I18n.tr("Timers")},
        {id: "stopwatch", title: Eitr.I18n.tr("Stopwatch")},
        {id: "focus", title: Eitr.I18n.tr("Focus")}
    ]

    color: Qt.rgba(background.r, background.g, background.b, 1)
    focus: opened

    // Esc first leaves a new timer being set, then closes the window.
    Keys.onEscapePressed: {
        if (content.page === "timers" && timers.leaveSetting()) return;
        closeRequested();
    }
    Keys.onPressed: event => {
        if (content.page === "timers" && timers.setKey(event)) event.accepted = true;
    }

    Item {
        id: body
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: modes.top; margins: 18; bottomMargin: 14 }

        TimersPage {
            id: timers
            objectName: "clock-timers"
            anchors.fill: parent
            visible: content.page === "timers"
            foreground: content.foreground; accent: content.accent
            onKeyboardWanted: content.forceActiveFocus()
        }
        StopwatchPage {
            anchors.fill: parent
            visible: content.page === "stopwatch"
            foreground: content.foreground; accent: content.accent
        }
        FocusPage {
            anchors.fill: parent
            visible: content.page === "focus"
            foreground: content.foreground; accent: content.accent
        }
    }

    Rectangle {
        id: modes
        objectName: "clock-modes"
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 16 }
        width: modeRow.implicitWidth + 8
        height: 40
        radius: height / 2
        color: Qt.alpha(content.foreground, 0.05)
        border.width: 1
        border.color: Qt.alpha(content.foreground, PanelStyle.selectionBorderAlpha)
        Row {
            id: modeRow
            anchors.centerIn: parent
            spacing: 2
            Repeater {
                model: content.pages
                PanelButton {
                    id: modeButton
                    required property var modelData
                    objectName: "clock-mode-" + modelData.id
                    width: Math.ceil(modeMetrics.advanceWidth) + 32
                    height: 32
                    radius: height / 2
                    flat: true
                    selected: content.page === modelData.id
                    foreground: content.foreground
                    text: modelData.title
                    onClicked: { content.page = modelData.id; content.forceActiveFocus(); }
                    TextMetrics { id: modeMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: modeButton.text }
                }
            }
        }
    }
}
