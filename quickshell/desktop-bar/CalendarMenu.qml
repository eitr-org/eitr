import Eitr as Eitr
import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import "ReminderModel.js" as ReminderModel
import "PanelStyle.js" as PanelStyle

ThemedPopup {
    id: menu
    implicitWidth: grid.implicitWidth + (contentGaps[1] + contentGaps[3]) * PanelStyle.contentGapMultiplier
        + (!detached && (barEdge === "top" || barEdge === "bottom") ? PanelStyle.surfaceInset * 2 : 0)
    implicitHeight: navigation.y + navigation.height + 22 + 28 + reminderSection.height + 12 + verticalContentInset
    keyTarget: calendarContent
    property date selectedDay: new Date()
    property var reminders: []
    readonly property var selectedReminders: ReminderModel.forDay(reminders, selectedDay)
    FileView {
        id: reminderFile
        path: {
            const state = Quickshell.env("XDG_STATE_HOME");
            return (state && state.startsWith("/") ? state : Quickshell.env("HOME") + "/.local/state") + "/eitr/reminders.json";
        }
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: menu.reminders = ReminderModel.parse(text())
        onLoadFailed: menu.reminders = []
    }
    property date today: new Date()
    property int viewYear: today.getFullYear()
    property int viewMonth: today.getMonth()
    readonly property var firstDay: new Date(viewYear, viewMonth, 1)
    readonly property var startDay: new Date(viewYear, viewMonth, 1 - (firstDay.getDay() + 6) % 7)
    readonly property real yearProgress: (new Date(today.getFullYear(), today.getMonth(), today.getDate()) - new Date(today.getFullYear(), 0, 1)) / (new Date(today.getFullYear() + 1, 0, 1) - new Date(today.getFullYear(), 0, 1))

    function isoWeek(date) {
        var d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
        return Math.ceil((((d - new Date(Date.UTC(d.getUTCFullYear(), 0, 1))) / 86400000) + 1) / 7);
    }
    function moveMonth(delta) {
        var d = new Date(viewYear, viewMonth + delta, 1);
        viewYear = d.getFullYear();
        viewMonth = d.getMonth();
    }
    function goToday() {
        today = new Date();
        selectedDay = today;
        viewYear = today.getFullYear();
        viewMonth = today.getMonth();
    }
    onOpenedChanged: if (opened) goToday()

    Item {
        id: calendarContent
        anchors.fill: parent
        focus: true
        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Left || event.key === Qt.Key_BracketLeft) moveMonth(-1);
            else if (event.key === Qt.Key_Right || event.key === Qt.Key_BracketRight) moveMonth(1);
            else if (event.key === Qt.Key_Up) moveMonth(-12);
            else if (event.key === Qt.Key_Down) moveMonth(12);
            else if (event.key === Qt.Key_T) goToday();
            else return;
            event.accepted = true;
        }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 0
            spacing: 18
            PanelHeading {
                width: 28; height: 60; text: ""
                foreground: menu.foreground; accent: menu.accent; rune: "calendar"
            }
            Column {
                spacing: 2
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: menu.viewYear === menu.today.getFullYear() && menu.viewMonth === menu.today.getMonth() ? Qt.formatDate(menu.today, "MMMM d") : Qt.formatDate(menu.firstDay, "MMMM yyyy")
                    color: menu.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: 34
                    font.bold: true
                }
                Text {
                    text: (Eitr.I18n.tr("{day} · WEEK {week} · {year}", {day: Qt.formatDate(menu.today, "dddd"), week: menu.isoWeek(menu.today), year: menu.today.getFullYear()})).toUpperCase()
                    color: menu.foreground
                    opacity: 0.72
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                    font.bold: true
                }
            }
        }
        Grid {
            id: grid
            anchors.horizontalCenter: parent.horizontalCenter
            y: 83
            columns: 8
            columnSpacing: 6
            rowSpacing: 8
            Repeater {
                model: 56
                Rectangle {
                    required property int index
                    readonly property int row: Math.floor(index / 8)
                    readonly property int column: index % 8
                    readonly property var day: new Date(menu.startDay.getFullYear(), menu.startDay.getMonth(), menu.startDay.getDate() + (row - 1) * 7 + Math.max(0, column - 1))
                    readonly property bool isToday: row > 0 && column > 0 && day.getFullYear() === menu.today.getFullYear() && day.getMonth() === menu.today.getMonth() && day.getDate() === menu.today.getDate()
                    width: column === 0 ? 34 : 56
                    height: row === 0 ? 24 : 38
                    radius: DesktopStyle.radius(7)
                    color: isToday ? menu.foreground : "transparent"
                    readonly property bool hasReminders: row > 0 && column > 0 && ReminderModel.forDay(menu.reminders, day).length > 0
                    border.width: row > 0 && column > 0 && day.toDateString() === menu.selectedDay.toDateString() ? 1 : 0
                    border.color: menu.foreground
                    MouseArea {
                        anchors.fill: parent
                        enabled: parent.row > 0 && parent.column > 0
                        cursorShape: Qt.PointingHandCursor
                        onClicked: menu.selectedDay = parent.day
                    }
                    Rectangle {
                        width: 4; height: 4; radius: 2
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom; anchors.bottomMargin: 2
                        visible: parent.hasReminders
                        color: parent.isToday ? menu.background : menu.foreground
                    }
                    Text {
                        anchors.centerIn: parent
                        text: parent.row === 0 ? ["W", "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][parent.column] : parent.column === 0 ? String(menu.isoWeek(parent.day)).padStart(2, "0") : parent.day.getDate()
                        color: parent.isToday ? menu.background : menu.foreground
                        opacity: parent.isToday ? 1 : parent.row === 0 || parent.column === 0 ? 0.58 : parent.day.getMonth() !== menu.viewMonth ? 0.32 : 1
                        font.family: DesktopFonts.family
                        font.pixelSize: parent.row === 0 || parent.column === 0 ? 11 : 13
                        font.bold: true
                    }
                }
            }
        }
        Row {
            id: navigation
            anchors.horizontalCenter: parent.horizontalCenter
            y: grid.y + grid.height + 22
            spacing: 8
            PanelButton { foreground: menu.foreground; text: "‹"; onClicked: menu.moveMonth(-1) }
            PanelButton { foreground: menu.foreground; text: Eitr.I18n.tr("Today"); onClicked: menu.goToday() }
            PanelButton { foreground: menu.foreground; text: "›"; onClicked: menu.moveMonth(1) }
        }
        Column {
            id: reminderSection
            x: grid.x
            y: navigation.y + navigation.height + 12
            width: grid.width
            spacing: 6
            Text {
                text: Qt.formatDate(menu.selectedDay, "ddd d MMM")
                color: menu.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
            // Fixed, so the calendar keeps its height from day to day.
            Item {
                width: parent.width
                height: 60
                Text {
                    visible: menu.selectedReminders.length === 0
                    text: Eitr.I18n.tr("No reminders")
                    color: menu.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
                ScrollView {
                    anchors.fill: parent
                    visible: menu.selectedReminders.length > 0
                    clip: true
                    contentWidth: availableWidth
                    Column {
                        id: reminderRows
                        width: parent.width
                        spacing: 6
                        Repeater {
                            model: menu.selectedReminders
                            Text {
                                required property var modelData
                                width: reminderSection.width
                                text: Qt.formatTime(new Date(modelData.due * 1000), "HH:mm") + " · " + (modelData.repeat ? String.fromCodePoint(0xF0456) + " " : "") + modelData.text
                                textFormat: Text.PlainText
                                wrapMode: Text.Wrap
                                color: menu.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                            }
                        }
                    }
                }
            }
        }
        Item {
            id: yearFooter
            x: grid.x
            width: grid.width
            height: 28
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 0
            Text { text: Eitr.I18n.tr("YEAR"); color: menu.foreground; opacity: 0.72; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
            Text { anchors.right: parent.right; text: Math.round(menu.yearProgress * 100) + "%"; color: menu.foreground; opacity: 0.72; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
            Rectangle {
                y: 22
                width: parent.width
                height: 6
                radius: 3
                color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.12)
                Rectangle { width: parent.width * menu.yearProgress; height: 6; radius: 3; color: menu.foreground }
            }
        }
    }
}
