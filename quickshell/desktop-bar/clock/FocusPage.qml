import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Focus sessions on the dial: the focus stretch and the break that follows are arcs
// on the face (lengths from Settings > Focus) and the hand shows where the session is.
Item {
    id: page
    required property color foreground
    required property color accent
    readonly property bool onBreak: FocusTimer.active && FocusTimer.phase === "break"
    readonly property real focusLength: FocusTimer.focusMinutes
    readonly property real breakLength: FocusTimer.breakMinutes
    // A cycle longer than an hour is drawn to fit one turn.
    readonly property real turn: Math.max(60, focusLength + breakLength)
    readonly property real position: !FocusTimer.active ? 0
        : onBreak ? (focusLength + FocusTimer.progress * breakLength) / turn
        : FocusTimer.progress * focusLength / turn
    readonly property color gold: SettingsInk.gold

    ChronoDial {
        id: dial
        width: parent.width
        height: Math.min(parent.width, parent.height - 190)
        foreground: page.foreground
        accent: page.accent
        showHand: FocusTimer.active
        hand: page.position
        arcs: [
            {from: 0, to: page.focusLength / page.turn, color: Qt.alpha(page.accent, page.onBreak ? 0.25 : 0.55)},
            {from: page.focusLength / page.turn, to: (page.focusLength + page.breakLength) / page.turn, color: Qt.alpha(page.gold, page.onBreak ? 0.8 : 0.35)}
        ]

        Column {
            anchors.centerIn: parent
            spacing: 2
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: !FocusTimer.active ? Eitr.I18n.tr("Ready")
                    : FocusTimer.paused ? Eitr.I18n.tr("Paused")
                    : page.onBreak ? Eitr.I18n.tr("Break")
                    : Eitr.I18n.tr("Focus · round {round}", {round: FocusTimer.rounds + 1})
                color: page.onBreak ? page.gold : page.foreground
                opacity: page.onBreak ? 1 : PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
            Text {
                objectName: "clock-focus-time"
                anchors.horizontalCenter: parent.horizontalCenter
                text: FocusTimer.clock(FocusTimer.active ? FocusTimer.remaining : FocusTimer.focusMinutes * 60000)
                color: page.foreground
                font.family: DesktopFonts.family; font.pixelSize: 34; font.bold: true
                font.features: PanelStyle.tabularFigures
            }
        }
    }

    Item {
        id: below
        anchors.bottom: parent.bottom
        width: parent.width
        height: parent.height - dial.height - 12

        Column {
            anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 14 }
            spacing: 6
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Eitr.I18n.tr("{focus} min focus · {rest} min break", {focus: FocusTimer.focusMinutes, rest: FocusTimer.breakMinutes})
                color: page.foreground
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: FocusTimer.rounds > 0
                    ? Eitr.I18n.tr("Completed rounds: {rounds}", {rounds: FocusTimer.rounds})
                    : Eitr.I18n.tr("Lengths follow Settings › Focus.")
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
        }

        Row {
            anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom }
            spacing: 8
            PanelButton {
                visible: FocusTimer.active
                width: 96; height: 36
                outlined: true
                foreground: page.foreground
                text: Eitr.I18n.tr("Stop")
                onClicked: FocusTimer.stop()
            }
            PanelButton {
                visible: page.onBreak
                width: 110; height: 36
                outlined: true
                foreground: page.foreground
                text: Eitr.I18n.tr("Skip break")
                onClicked: FocusTimer.skipBreak()
            }
            PanelButton {
                objectName: "clock-focus-toggle"
                width: 110; height: 36
                selected: true
                foreground: page.foreground
                text: !FocusTimer.active ? Eitr.I18n.tr("Start") : FocusTimer.paused ? Eitr.I18n.tr("Resume") : Eitr.I18n.tr("Pause")
                onClicked: {
                    if (FocusTimer.paused) FocusTimer.resume();
                    else if (FocusTimer.running) FocusTimer.pause();
                    else FocusTimer.startFocus();
                }
            }
        }
    }
}
