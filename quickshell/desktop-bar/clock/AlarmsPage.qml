import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../ChoiceLists.js" as ChoiceLists
import "../PanelStyle.js" as PanelStyle
import "../clock/AlarmModel.js" as AlarmModel

Item {
    id: page
    required property color foreground
    required property color background
    required property color accent
    property var alarms: ClockAlarms.items
    property bool twelveHour: PluginRegistry.clockFormat === "12h"
    readonly property var locale: Qt.locale(Eitr.I18n.locale)
    property bool editing: false
    property string editId: ""
    property string deleteId: ""
    property bool submitted: false
    property string error: ""
    readonly property var sounds: ChoiceLists.alarmSounds.map(choice =>
        ({value: choice.id, label: Eitr.I18n.tr(choice.label)}))

    function edit(item) {
        error = "";
        editId = item ? item.id : "";
        editing = true;
        editor.open(item);
    }

    function leaveSetting() {
        if (ClockAlarms.busy && submitted) return true;
        if (!editing && !deleteId) return false;
        editing = false;
        deleteId = "";
        error = "";
        return true;
    }

    function confirmDelete() {
        if (!deleteId || ClockAlarms.busy) return;
        submitted = true;
        ClockAlarms.run("alarm-delete", deleteId);
    }

    Connections {
        target: ClockAlarms
        function onFinished(success) {
            if (!page.submitted) return;
            page.submitted = false;
            page.error = success ? "" : Eitr.I18n.tr("Could not update the alarm.");
            if (success) page.leaveSetting();
        }
    }

    Column {
        anchors.fill: parent
        spacing: 12
        Text {
            text: Eitr.I18n.tr("Alarms")
            color: page.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.headingSize
        }
        Text {
            width: parent.width
            visible: page.error !== ""
            text: page.error
            color: page.foreground
            wrapMode: Text.Wrap
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
        }

        AlarmEditor {
            id: editor
            width: parent.width
            visible: page.editing
            foreground: page.foreground
            background: page.background
            accent: page.accent
            twelveHour: page.twelveHour
            sounds: page.sounds
            locale: page.locale
            onCancel: page.leaveSetting()
            onSave: payload => {
                page.submitted = true;
                ClockAlarms.run("alarm-save", page.editId, payload);
            }
        }

        FocusScope {
            id: confirmation
            visible: page.deleteId !== ""
            width: parent.width
            height: deleteContent.implicitHeight
            Keys.onReturnPressed: page.confirmDelete()
            Keys.onEnterPressed: page.confirmDelete()
            Keys.onEscapePressed: page.leaveSetting()
            Column {
                id: deleteContent
                width: parent.width
                spacing: 8
                Text {
                    width: parent.width
                    text: Eitr.I18n.tr("Delete this alarm?")
                    color: page.foreground
                    wrapMode: Text.Wrap
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
                Row {
                    width: parent.width
                    spacing: 8
                    PanelButton {
                        width: (parent.width - 8) / 2
                        foreground: page.foreground
                        text: Eitr.I18n.tr("Cancel")
                        onClicked: page.leaveSetting()
                    }
                    PanelButton {
                        width: (parent.width - 8) / 2
                        foreground: page.foreground
                        text: Eitr.I18n.tr("Delete")
                        onClicked: page.confirmDelete()
                    }
                }
            }
        }

        PanelButton {
            visible: !page.editing && !page.deleteId
            width: parent.width
            foreground: page.foreground
            text: Eitr.I18n.tr("Add alarm")
            onClicked: page.edit(null)
        }
        Text {
            width: parent.width
            visible: !page.editing && !page.deleteId && page.alarms.length === 0
            text: Eitr.I18n.tr("No alarms yet.")
            color: Qt.alpha(page.foreground, 0.6)
            horizontalAlignment: Text.AlignHCenter
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
        }
        ListView {
            id: list
            visible: !page.editing && !page.deleteId
            width: parent.width
            height: Math.max(0, page.height - y)
            clip: true
            spacing: 8
            model: page.alarms
            delegate: Rectangle {
                id: card
                required property var modelData
                width: list.width
                height: details.implicitHeight + 20
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: Qt.alpha(page.foreground, 0.05)
                border.color: Qt.alpha(page.foreground, PanelStyle.selectionBorderAlpha)
                Column {
                    id: details
                    x: 10; y: 10
                    width: parent.width - 20
                    spacing: 5
                    Row {
                        width: parent.width
                        spacing: 8
                        Text {
                            width: parent.width - toggle.width - parent.spacing
                            anchors.verticalCenter: parent.verticalCenter
                            text: AlarmModel.displayTime(card.modelData.alarm.clock, page.twelveHour, page.locale)
                            color: page.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.figureSize
                        }
                        PanelSwitch {
                            id: toggle
                            foreground: page.foreground
                            accent: page.accent
                            checked: card.modelData.alarm.enabled
                            enabled: !ClockAlarms.busy
                            Accessible.name: card.modelData.text
                            onToggled: {
                                page.error = "";
                                page.submitted = true;
                                ClockAlarms.run("alarm-save", card.modelData.id, {
                                    clock: card.modelData.alarm.clock, name: card.modelData.text,
                                    days: card.modelData.alarm.days, sound: card.modelData.alarm.sound, enabled: checked
                                });
                            }
                        }
                    }
                    Text {
                        width: parent.width
                        text: card.modelData.text
                        textFormat: Text.PlainText
                        color: page.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.bodySize
                        elide: Text.ElideRight
                    }
                    Text {
                        width: parent.width
                        text: card.modelData.alarm.days.length
                            ? card.modelData.alarm.days.map(day => page.locale.standaloneDayName(day + 1, Locale.ShortFormat)).join(" · ")
                            : Eitr.I18n.tr("Once")
                        color: Qt.alpha(page.foreground, PanelStyle.secondaryTextOpacity)
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                        wrapMode: Text.Wrap
                    }
                    Row {
                        width: parent.width
                        spacing: 8
                        PanelButton {
                            width: (parent.width - 8) / 2
                            foreground: page.foreground
                            text: Eitr.I18n.tr("Edit")
                            onClicked: page.edit(card.modelData)
                        }
                        PanelButton {
                            width: (parent.width - 8) / 2
                            foreground: page.foreground
                            text: Eitr.I18n.tr("Delete")
                            onClicked: {
                                page.error = "";
                                page.deleteId = card.modelData.id;
                                confirmation.forceActiveFocus();
                            }
                        }
                    }
                }
            }
        }
    }
}
