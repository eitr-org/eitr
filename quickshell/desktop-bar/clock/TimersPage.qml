import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../ClockModel.js" as ClockModel

// Timers page: quick preset lengths, custom H/M/S + optional name creation,
// and live cards sorted by time left.
Flickable {
    id: timersPage
    required property color foreground
    required property color background
    required property color accent
    contentHeight: contentColumn.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    readonly property int customHours: Number(hoursField.text) || 0
    readonly property int customMinutes: Number(minutesField.text) || 0
    readonly property int customSeconds: Number(secondsField.text) || 0
    readonly property real customDurationMs: ClockModel.parseCustomDurationMs(customHours, customMinutes, customSeconds)
    readonly property bool hasEnded: {
        const list = ClockTimers.timers || [];
        for (let index = 0; index < list.length; index += 1) {
            if (list[index].ended) return true;
        }
        return false;
    }

    function startQuick(minutes) {
        ClockTimers.addQuickTimer(minutes, nameField.text);
        nameField.text = "";
    }

    function startCustom() {
        if (customDurationMs <= 0) return;
        ClockTimers.addTimer(customDurationMs, nameField.text);
        nameField.text = "";
    }

    component TimeUnitField: Column {
        id: unitColumn
        property alias text: inputField.text
        property string labelText: ""
        property int maxVal: 59
        signal accepted()
        width: 56
        spacing: 4

        PanelTextField {
            id: inputField
            width: parent.width
            height: 36
            foreground: timersPage.foreground
            accent: timersPage.accent
            horizontalAlignment: Text.AlignHCenter
            maximumLength: 2
            inputMethodHints: Qt.ImhDigitsOnly
            validator: IntValidator { bottom: 0; top: unitColumn.maxVal }
            font.features: PanelStyle.tabularFigures
            onAccepted: unitColumn.accepted()
            onActiveFocusChanged: if (!activeFocus && text === "") text = "00"
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: unitColumn.labelText
            color: timersPage.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
    }

    Column {
        id: contentColumn
        width: timersPage.width
        spacing: 18

        FamilyPageHeader {
            foreground: timersPage.foreground
            rune: "ᛉ"
            group: Eitr.I18n.tr("Clock")
            title: Eitr.I18n.tr("Timers")
            description: Eitr.I18n.tr("Run multiple countdowns at once. Running timers stay sorted by time left.")
        }

        ControlCard {
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            carved: true
            foreground: timersPage.foreground
            title: Eitr.I18n.tr("New timer")

            Flow {
                width: parent.width
                spacing: 8

                Repeater {
                    model: [1, 5, 10, 25]
                    PanelButton {
                        id: presetBtn
                        required property int modelData
                        width: Math.max(76, Math.ceil(presetMetrics.advanceWidth) + 24)
                        height: 34
                        outlined: true
                        foreground: timersPage.foreground
                        text: Eitr.I18n.tr("{minutes} min", {minutes: modelData})
                        onClicked: timersPage.startQuick(modelData)
                        TextMetrics { id: presetMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: presetBtn.text }
                    }
                }
            }

            Rectangle {
                width: parent.width
                height: 1
                color: Qt.alpha(timersPage.foreground, PanelStyle.dividerAlpha)
            }

            Flow {
                width: parent.width
                spacing: 10

                PanelTextField {
                    id: nameField
                    width: Math.max(180, Math.min(280, parent.width - 280))
                    height: 36
                    foreground: timersPage.foreground
                    accent: timersPage.accent
                    placeholderText: Eitr.I18n.tr("Timer name (optional)")
                    onAccepted: timersPage.startCustom()
                }

                Row {
                    spacing: 6

                    TimeUnitField { id: hoursField; text: "00"; maxVal: 99; labelText: Eitr.I18n.tr("hr"); onAccepted: timersPage.startCustom() }
                    Text { y: 8; text: ":"; color: timersPage.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize }
                    TimeUnitField { id: minutesField; text: "05"; maxVal: 59; labelText: Eitr.I18n.tr("min"); onAccepted: timersPage.startCustom() }
                    Text { y: 8; text: ":"; color: timersPage.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize }
                    TimeUnitField { id: secondsField; text: "00"; maxVal: 59; labelText: Eitr.I18n.tr("sec"); onAccepted: timersPage.startCustom() }
                }

                PanelButton {
                    id: customStartBtn
                    width: Math.max(92, Math.ceil(startMetrics.advanceWidth) + 28)
                    height: 36
                    selected: true
                    available: timersPage.customDurationMs > 0
                    foreground: timersPage.foreground
                    text: Eitr.I18n.tr("Start")
                    onClicked: timersPage.startCustom()
                    TextMetrics { id: startMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: customStartBtn.text }
                }
            }
        }

        Item {
            visible: ClockTimers.timers.length > 0
            width: parent.width
            height: Math.max(activeHeading.implicitHeight, clearBtn.visible ? clearBtn.height : 0)

            Text {
                id: activeHeading
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                text: Eitr.I18n.tr("Active & recent timers")
                color: timersPage.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
                font.weight: Font.Medium
            }

            PanelButton {
                id: clearBtn
                visible: timersPage.hasEnded
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: Math.max(96, Math.ceil(clearMetrics.advanceWidth) + 24)
                height: 28
                outlined: true
                foreground: timersPage.foreground
                text: Eitr.I18n.tr("Clear ended")
                onClicked: ClockTimers.clearEndedTimers()
                TextMetrics { id: clearMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: clearBtn.text }
            }
        }

        ControlCard {
            visible: ClockTimers.timers.length === 0
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            carved: true
            foreground: timersPage.foreground
            title: Eitr.I18n.tr("Active timers")

            Text {
                width: parent.width
                wrapMode: Text.Wrap
                text: Eitr.I18n.tr("No timers running. Pick a quick length above or set a custom duration.")
                color: timersPage.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }
        }

        Repeater {
            model: ClockTimers.timers
            TimerCard {
                required property var modelData
                width: contentColumn.width
                timerEntry: modelData
                foreground: timersPage.foreground
                accent: timersPage.accent
            }
        }
    }
}
