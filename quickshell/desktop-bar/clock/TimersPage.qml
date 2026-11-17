import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Timers: each running timer is a ring on the dial, the chosen one in the centre with its
// controls. A new timer is set by dragging the hand round (an hour a turn), which is also
// what shows while no timer exists.
Item {
    id: page
    required property color foreground
    required property color accent
    property bool adding: false
    property string chosenId: ""
    readonly property var timers: ClockTimers.timers
    readonly property bool setting: adding || timers.length === 0
    readonly property var chosen: timers.find(entry => entry.id === chosenId) || timers[0] || null
    readonly property bool hasEnded: timers.some(entry => entry.ended)
    readonly property color gold: SettingsInk.gold
    signal keyboardWanted()

    function ringColor(entry) {
        if (entry.ended) return gold;
        if (!entry.running) return Qt.alpha(foreground, 0.35);
        return chosen && entry.id === chosen.id ? accent : Qt.alpha(accent, 0.5);
    }
    function start() {
        if (dial.minutes <= 0) return;
        ClockTimers.addTimer(dial.minutes * 60000, name.text);
        name.text = "";
        chosenId = "";
        adding = false;
    }
    function leaveSetting() {
        if (!adding || timers.length === 0) return false;
        adding = false;
        return true;
    }
    // Arrow keys move the hand a minute (Page Up/Down ten); Enter starts.
    function setKey(event) {
        if (!setting) return false;
        const steps = {[Qt.Key_Up]: 1, [Qt.Key_Right]: 1, [Qt.Key_Down]: -1, [Qt.Key_Left]: -1, [Qt.Key_PageUp]: 10, [Qt.Key_PageDown]: -10};
        if (steps[event.key] !== undefined) dial.setMinutes(dial.minutes + steps[event.key]);
        else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) start();
        else return false;
        return true;
    }

    ChronoDial {
        id: dial
        objectName: "clock-dial"
        width: parent.width
        height: Math.min(parent.width, parent.height - 190)
        foreground: page.foreground
        accent: page.accent
        adjustable: page.setting
        rings: page.setting ? [] : page.timers.slice(0, 4).map(entry => ({
            progress: entry.ended ? 1 : ClockTimers.timerProgress(entry), color: page.ringColor(entry)}))

        // Setting a new timer: the length and how to change it.
        Column {
            visible: page.setting
            anchors.centerIn: parent
            spacing: 2
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Eitr.I18n.tr("New timer")
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
            Text {
                objectName: "clock-set-length"
                anchors.horizontalCenter: parent.horizontalCenter
                text: ClockTimers.formatClock(dial.minutes * 60000)
                color: page.foreground
                font.family: DesktopFonts.family; font.pixelSize: 38; font.bold: true
                font.features: PanelStyle.tabularFigures
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Eitr.I18n.tr("Drag the hand")
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
        }

        // The chosen timer: time left, name and its controls.
        Column {
            visible: !page.setting && !!page.chosen
            anchors.centerIn: parent
            spacing: 4
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(implicitWidth, dial.size * 0.5)
                elide: Text.ElideRight
                text: page.chosen ? ClockTimers.timerLabel(page.chosen) : ""
                textFormat: Text.PlainText
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
            Text {
                objectName: "clock-chosen-time"
                anchors.horizontalCenter: parent.horizontalCenter
                text: !page.chosen ? "" : page.chosen.ended ? Eitr.I18n.tr("Ended") : ClockTimers.formatClock(ClockTimers.timerRemaining(page.chosen))
                color: page.chosen && page.chosen.ended ? page.gold : page.foreground
                font.family: DesktopFonts.family; font.pixelSize: 34; font.bold: true
                font.features: PanelStyle.tabularFigures
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 6
                PanelButton {
                    visible: !!page.chosen && !page.chosen.ended
                    width: 32; height: 32; icon: true; iconSize: 14; outlined: true
                    foreground: page.foreground
                    text: page.chosen && page.chosen.running ? "\u{F04C}" : "\u{F04B}"
                    Accessible.name: page.chosen && page.chosen.running ? Eitr.I18n.tr("Pause") : Eitr.I18n.tr("Resume")
                    onClicked: page.chosen.running ? ClockTimers.pauseTimer(page.chosen.id) : ClockTimers.resumeTimer(page.chosen.id)
                }
                PanelButton {
                    width: 32; height: 32; icon: true; iconSize: 14; outlined: true
                    selected: !!page.chosen && page.chosen.ended
                    foreground: page.foreground
                    text: "\u{F01E}"
                    Accessible.name: Eitr.I18n.tr("Restart")
                    onClicked: ClockTimers.restartTimer(page.chosen.id)
                }
                PanelButton {
                    width: 32; height: 32; icon: true; iconSize: 14; outlined: true
                    foreground: page.foreground
                    text: "\u{F00D}"
                    Accessible.name: Eitr.I18n.tr("Remove timer")
                    onClicked: ClockTimers.removeTimer(page.chosen.id)
                }
            }
        }
    }

    Item {
        id: below
        anchors.bottom: parent.bottom
        width: parent.width
        height: parent.height - dial.height - 12

        // Setting: quick lengths, an optional name and Start.
        Column {
            visible: page.setting
            anchors.fill: parent
            spacing: 10
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8
                Repeater {
                    model: [1, 5, 10, 25]
                    PanelButton {
                        required property int modelData
                        width: 64; height: 32
                        outlined: true
                        selected: dial.minutes === modelData
                        foreground: page.foreground
                        text: Eitr.I18n.tr("{minutes} min", {minutes: modelData})
                        onClicked: { dial.setMinutes(modelData); page.keyboardWanted(); }
                    }
                }
            }
            PanelTextField {
                id: name
                width: parent.width
                height: 36
                foreground: page.foreground
                accent: page.accent
                placeholderText: Eitr.I18n.tr("Name (optional)")
                onAccepted: page.start()
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8
                PanelButton {
                    visible: page.timers.length > 0
                    width: 96; height: 36
                    outlined: true
                    foreground: page.foreground
                    text: Eitr.I18n.tr("Back")
                    onClicked: page.adding = false
                }
                PanelButton {
                    objectName: "clock-start-timer"
                    width: 120; height: 36
                    selected: true
                    available: dial.minutes > 0
                    foreground: page.foreground
                    text: Eitr.I18n.tr("Start")
                    onClicked: page.start()
                }
            }
        }

        // Watching: every timer as a row (choosing one puts it in the centre), New timer.
        Item {
            visible: !page.setting
            anchors.fill: parent
            Flickable {
                anchors { left: parent.left; right: parent.right; top: parent.top; bottom: actions.top; bottomMargin: 8 }
                contentHeight: rows.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                Column {
                    id: rows
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: page.timers
                        TimerRow {
                            required property var modelData
                            width: rows.width
                            timerEntry: modelData
                            chosen: !!page.chosen && page.chosen.id === modelData.id
                            mark: page.ringColor(modelData)
                            foreground: page.foreground
                            onClicked: page.chosenId = modelData.id
                        }
                    }
                }
            }
            Row {
                id: actions
                anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom }
                spacing: 8
                PanelButton {
                    visible: page.hasEnded
                    width: 120; height: 36
                    outlined: true
                    foreground: page.foreground
                    text: Eitr.I18n.tr("Clear ended")
                    onClicked: ClockTimers.clearEndedTimers()
                }
                PanelButton {
                    objectName: "clock-new-timer"
                    width: 120; height: 36
                    selected: true
                    foreground: page.foreground
                    text: Eitr.I18n.tr("New timer")
                    onClicked: { page.adding = true; page.keyboardWanted(); }
                }
            }
        }
    }
}
