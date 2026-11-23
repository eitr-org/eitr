import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../clock/AlarmModel.js" as AlarmModel

Column {
    id: editor
    required property color foreground
    required property color background
    required property color accent
    required property bool twelveHour
    required property var sounds
    required property var locale
    property string period: "am"
    property var days: []
    property string sound: EventSounds.timerSound
    readonly property string clock: AlarmModel.parseClock(timeField.text, twelveHour, period)
    signal save(var payload)
    signal cancel()
    spacing: 12

    function open(item) {
        const time = AlarmModel.splitClock(item ? item.alarm.clock : "07:00", twelveHour);
        timeField.text = time.text;
        period = time.period;
        nameField.text = item ? item.text : "";
        days = item ? item.alarm.days : [];
        sound = item ? item.alarm.sound : EventSounds.timerSound;
        timeField.forceActiveFocus();
    }

    Row {
        width: parent.width
        spacing: 8
        PanelTextField {
            id: timeField
            width: editor.twelveHour ? (parent.width - 8) * 0.60 : parent.width
            // Match the AM / PM dropdown's outlined box (48 px) and sit level with it under its label.
            height: 48
            anchors.bottom: parent.bottom
            foreground: editor.foreground
            accent: editor.accent
            placeholderText: editor.twelveHour ? "h:mm" : "HH:mm"
            Accessible.name: Eitr.I18n.tr("Time")
            maximumLength: 5
        }
        ChoiceDropdown {
            visible: editor.twelveHour
            width: (parent.width - 8) * 0.40
            foreground: editor.foreground
            background: editor.background
            gold: editor.accent
            floatingLabel: Eitr.I18n.tr("AM / PM")
            choices: [{value: "am", label: editor.locale.amText}, {value: "pm", label: editor.locale.pmText}]
            current: editor.period
            onChosen: value => editor.period = value
        }
    }

    PanelTextField {
        id: nameField
        width: parent.width
        foreground: editor.foreground
        accent: editor.accent
        placeholderText: Eitr.I18n.tr("Alarm name")
        maximumLength: 240
    }

    Text {
        text: Eitr.I18n.tr("Repeat days")
        color: editor.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
    }
    Grid {
        width: parent.width
        columns: 4
        spacing: 6
        Repeater {
            model: 7
            PanelButton {
                required property int index
                width: (editor.width - 18) / 4
                foreground: editor.foreground
                text: editor.locale.standaloneDayName(index + 1, Locale.ShortFormat)
                Accessible.name: editor.locale.standaloneDayName(index + 1)
                selected: editor.days.includes(index)
                onClicked: editor.days = selected ? editor.days.filter(day => day !== index) : editor.days.concat(index)
            }
        }
    }

    ChoiceDropdown {
        width: parent.width
        foreground: editor.foreground
        background: editor.background
        gold: editor.accent
        floatingLabel: Eitr.I18n.tr("Sound")
        current: editor.sound
        choices: editor.sounds.concat(editor.sound.startsWith("/")
                ? [{value: editor.sound, label: editor.sound.split("/").pop()}] : [],
                [{value: "choose", label: Eitr.I18n.tr("Choose a file…")}])
        onChosen: value => {
            if (value === "choose") ClockAlarms.chooseSound();
            else editor.sound = value;
        }
    }

    Row {
        width: parent.width
        spacing: 8
        PanelButton {
            width: (parent.width - 8) / 2
            foreground: editor.foreground
            text: Eitr.I18n.tr("Cancel")
            onClicked: editor.cancel()
        }
        PanelButton {
            width: (parent.width - 8) / 2
            foreground: editor.foreground
            text: Eitr.I18n.tr("Save")
            selected: true
            available: Boolean(editor.clock) && !ClockAlarms.busy && !ClockAlarms.choosingSound
            onClicked: editor.save({clock: editor.clock, name: nameField.text.trim() || Eitr.I18n.tr("Alarm"),
                days: editor.days, sound: editor.sound, enabled: true})
        }
    }

    Connections {
        target: ClockAlarms
        function onSoundChosen(path) {
            if (editor.visible) editor.sound = path;
        }
    }
}
