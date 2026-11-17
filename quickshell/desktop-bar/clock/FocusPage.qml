import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Focus sessions page: focus and break intervals configured in Settings > Focus,
// shared progress ring, round counter, pause/resume, skip break, and stop.
Flickable {
    id: focusPage
    required property color foreground
    required property color background
    required property color accent
    contentHeight: contentColumn.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    component FocusButton: PanelButton {
        id: focusBtn
        property real minWidth: 96
        width: Math.max(minWidth, Math.ceil(metrics.advanceWidth) + 28)
        height: 36
        foreground: focusPage.foreground
        TextMetrics {
            id: metrics
            font.family: DesktopFonts.family
            font.pixelSize: focusBtn.textSize
            text: focusBtn.text
        }
    }

    Column {
        id: contentColumn
        width: focusPage.width
        spacing: 18

        FamilyPageHeader {
            foreground: focusPage.foreground
            rune: "ᚠ"
            group: Eitr.I18n.tr("Clock")
            title: Eitr.I18n.tr("Focus")
            description: Eitr.I18n.tr("{focus} minutes of focus, then a {rest}-minute break. Lengths follow Settings › Focus.", {focus: FocusTimer.focusMinutes, rest: FocusTimer.breakMinutes})
        }

        ControlCard {
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            carved: true
            foreground: focusPage.foreground
            title: Eitr.I18n.tr("Focus session")

            Column {
                width: parent.width
                spacing: 18

                Item {
                    width: parent.width
                    height: 228

                    ProgressRing {
                        anchors.centerIn: parent
                        width: 220; height: 220
                        progress: FocusTimer.active ? FocusTimer.progress : 0
                        trackColor: Qt.alpha(focusPage.foreground, 0.12)
                        accentColor: FocusTimer.active && FocusTimer.phase === "break"
                            ? Qt.lighter(focusPage.accent, 1.3)
                            : focusPage.accent
                        lineWidth: 10
                        ringPadding: 12
                        minimumArc: FocusTimer.active ? 0.015 : 0
                    }

                    Column {
                        anchors.centerIn: parent
                        spacing: 4

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: FocusTimer.active
                                ? FocusTimer.clock(FocusTimer.remaining)
                                : FocusTimer.clock(FocusTimer.focusMinutes * 60000)
                            color: focusPage.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: 40
                            font.weight: Font.Bold
                            font.features: PanelStyle.tabularFigures
                        }

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: !FocusTimer.active
                                ? Eitr.I18n.tr("Ready")
                                : FocusTimer.paused
                                    ? Eitr.I18n.tr("Paused")
                                    : FocusTimer.phase === "break"
                                        ? Eitr.I18n.tr("Break")
                                        : Eitr.I18n.tr("Focus · round {round}", {round: FocusTimer.rounds + 1})
                            color: focusPage.foreground
                            opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                        }
                    }
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: FocusTimer.rounds > 0
                        ? Eitr.I18n.tr("Completed rounds: {rounds}", {rounds: FocusTimer.rounds})
                        : Eitr.I18n.tr("Notifications chime at each transition unless Do Not Disturb is on.")
                    color: focusPage.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    wrapMode: Text.Wrap
                    width: Math.min(parent.width, 460)
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10

                    FocusButton {
                        selected: true
                        text: !FocusTimer.active ? Eitr.I18n.tr("Start")
                            : FocusTimer.paused ? Eitr.I18n.tr("Resume")
                            : Eitr.I18n.tr("Pause")
                        onClicked: {
                            if (FocusTimer.paused) FocusTimer.resume();
                            else if (FocusTimer.running) FocusTimer.pause();
                            else FocusTimer.startFocus();
                        }
                    }

                    FocusButton {
                        visible: FocusTimer.active && FocusTimer.phase === "break"
                        outlined: true
                        text: Eitr.I18n.tr("Skip break")
                        onClicked: FocusTimer.skipBreak()
                    }

                    FocusButton {
                        visible: FocusTimer.active
                        outlined: true
                        text: Eitr.I18n.tr("Stop")
                        onClicked: FocusTimer.stop()
                    }
                }
            }
        }
    }
}
