import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../ReminderModel.js" as ReminderModel

// A day's plans on Drop's home page, opened by clicking a day: its events and reminders
// with their times, a field to add a reminder at a time that day, and a bin on one-off
// reminders (clicked twice). Repeating ones and subscribed events are managed in the
// Calendar panel.
Item {
    id: agenda
    required property var barHost
    required property color foreground
    required property color accent
    required property date day
    signal closed()
    readonly property var calendar: barHost.calendarMenu
    readonly property var items: calendar ? ReminderModel.dayItems(calendar.reminders || [], calendar.events || [], day) : []
    readonly property string helper: Eitr.Paths.code("walker/scripts/actions/tools/reminders.py")
    property string pendingKey: ""
    property string error: ""
    onDayChanged: { pendingKey = ""; error = ""; }

    function add() {
        const time = timeField.text.trim(), text = titleField.text.trim();
        if (!/^\d{1,2}:\d{2}$/.test(time) || text === "" || saving.running) {
            error = Eitr.I18n.tr("Type a time like 18:30 and what to remember");
            return;
        }
        error = "";
        saving.command = ["python3", helper, "new", Qt.formatDate(day, "yyyy-MM-dd") + " " + time, text];
        saving.running = true;
    }
    Process {
        id: saving
        stderr: StdioCollector { id: savingErrors }
        onExited: function(code) {
            if (code === 0) { titleField.text = ""; timeField.text = ""; }
            else agenda.error = savingErrors.text.trim().split("\n")[0] || Eitr.I18n.tr("Could not add the reminder");
        }
    }
    Process {
        id: removing
        onExited: agenda.pendingKey = ""
    }

    Item {
        width: parent.width; height: 28
        PanelButton {
            id: back
            width: 24; height: 24; icon: true; anchors.verticalCenter: parent.verticalCenter
            text: "󰅁"; foreground: agenda.foreground
            Accessible.name: Eitr.I18n.tr("Back to the weather")
            onClicked: agenda.closed()
        }
        Text {
            x: back.width + 6; anchors.verticalCenter: parent.verticalCenter
            width: parent.width - x
            text: agenda.day.toLocaleDateString(Qt.locale(), "dddd d MMM")
            color: agenda.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
            font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2; elide: Text.ElideRight
        }
    }

    Flickable {
        y: 38; width: parent.width; height: parent.height - y - addRow.height - 12
        contentHeight: rows.implicitHeight; clip: true
        boundsBehavior: Flickable.StopAtBounds
        Text {
            visible: agenda.items.length === 0
            y: 4
            text: Eitr.I18n.tr("Nothing planned")
            color: agenda.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        Column {
            id: rows
            width: parent.width
            spacing: 8
            Repeater {
                model: agenda.items
                Item {
                    id: row
                    required property var modelData
                    readonly property string key: modelData.id + ":" + modelData.due
                    readonly property bool removable: modelData.kind !== "event" && !modelData.repeat
                    readonly property bool confirming: agenda.pendingKey === key
                    width: rows.width; height: Math.max(titleText.implicitHeight, 22)
                    Text {
                        id: timeText
                        width: 44; anchors.top: parent.top; anchors.topMargin: 2
                        text: row.modelData.allDay ? Eitr.I18n.tr("All day") : row.modelData.continued ? "…"
                            : Qt.formatTime(new Date(row.modelData.due * 1000), Qt.locale().timeFormat(Locale.ShortFormat))
                        color: agenda.accent; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures; elide: Text.ElideRight
                    }
                    Text {
                        id: titleText
                        x: timeText.width + 6; width: parent.width - x - (row.removable ? 28 : 0)
                        text: (row.modelData.kind === "event" ? "󰃭 " : row.modelData.repeat ? "󰑖 " : "") + row.modelData.text
                        textFormat: Text.PlainText; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
                        color: agenda.foreground; opacity: row.confirming ? PanelStyle.secondaryTextOpacity : 1
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    }
                    PanelButton {
                        visible: row.removable
                        anchors.right: parent.right
                        width: 22; height: 22; icon: true; text: "󰆴"
                        foreground: agenda.foreground; selected: row.confirming; outlined: row.confirming
                        available: !removing.running
                        Accessible.name: row.confirming ? Eitr.I18n.tr("Click again to delete") : Eitr.I18n.tr("Delete reminder")
                        onClicked: {
                            if (!row.confirming) { agenda.pendingKey = row.key; return; }
                            removing.command = ["python3", agenda.helper, "cancel", row.modelData.id, "series"];
                            removing.running = true;
                        }
                    }
                }
            }
        }
    }

    Column {
        id: addRow
        anchors.bottom: parent.bottom
        width: parent.width
        spacing: 4
        Text {
            visible: agenda.error !== ""
            width: parent.width; wrapMode: Text.Wrap; textFormat: Text.PlainText
            text: agenda.error
            color: agenda.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: 11
        }
        Row {
            spacing: 6
            PanelTextField {
                id: timeField
                width: 58; height: 30
                foreground: agenda.foreground; accent: agenda.accent
                placeholderText: "18:30"; inputMethodHints: Qt.ImhTime
                onAccepted: titleField.forceActiveFocus()
            }
            PanelTextField {
                id: titleField
                width: addRow.width - timeField.width - 6; height: 30
                foreground: agenda.foreground; accent: agenda.accent
                placeholderText: Eitr.I18n.tr("Remind me…")
                onAccepted: agenda.add()
            }
        }
    }
}
