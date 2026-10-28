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
    // Read-only calendar subscriptions, cached by calendars.py; they have no trash button.
    property var events: []
    readonly property var selectedReminders: ReminderModel.dayItems(reminders, events, selectedDay)
    FileView {
        id: calendarEventsFile
        path: {
            const cache = Quickshell.env("XDG_CACHE_HOME");
            return (cache && cache.startsWith("/") ? cache : Quickshell.env("HOME") + "/.cache") + "/eitr/calendar-events.json";
        }
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: { const snapshot = text(); menu.updateContent(function() { menu.applySnapshot("events", ReminderModel.parseEvents(snapshot)); }); }
        onLoadFailed: menu.applySnapshot("events", [])
    }
    FileView {
        id: reminderFile
        path: {
            const state = Quickshell.env("XDG_STATE_HOME");
            return (state && state.startsWith("/") ? state : Quickshell.env("HOME") + "/.local/state") + "/eitr/reminders.json";
        }
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: { const snapshot = text(); menu.updateContent(function() { menu.applySnapshot("reminders", ReminderModel.parse(snapshot)); }); }
        onLoadFailed: menu.applySnapshot("reminders", [])
    }
    // One reminder row at a time asks before deleting; the list follows the file watch.
    property string pendingKey: ""
    property Item pendingRow: null
    property string deleteError: ""
    property int confirmationTimeout: 5000
    readonly property string reminderHelper: Eitr.Paths.code("walker/scripts/actions/tools/reminders.py")
    function requestDelete(row) {
        deleteError = "";
        if (pendingKey === row.key) {
            cancelDelete();
            return;
        }
        pendingRow = row;
        pendingKey = row.key;
    }
    function cancelDelete() {
        if (pendingRow && pendingRow.choicesFocused()) pendingRow.restoreFocus();
        pendingKey = "";
        pendingRow = null;
    }
    function deleteReminder(identifier, scope) {
        if (reminderCancel.running) return;
        deleteError = "";
        reminderCancel.command = ["python3", reminderHelper, "cancel", identifier, scope];
        reminderCancel.running = true;
    }
    Process {
        id: reminderCancel
        stderr: StdioCollector { id: reminderCancelErrors }
        onExited: function(code) {
            menu.pendingKey = "";
            menu.pendingRow = null;
            calendarContent.forceActiveFocus();
            if (code !== 0)
                menu.deleteError = reminderCancelErrors.text.trim().split("\n")[0] || Eitr.I18n.tr("Could not delete the reminder");
        }
    }
    Timer {
        id: pendingTimeout
        interval: menu.confirmationTimeout
        running: menu.pendingKey !== "" && !reminderCancel.running && !(menu.pendingRow && menu.pendingRow.hovered)
        onTriggered: menu.cancelDelete()
    }
    onSelectedDayChanged: {
        cancelDelete();
        deleteError = "";
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
    onOpenedChanged: {
        cancelDelete();
        deleteError = "";
        if (opened) {
            goToday();
            // New events in a subscribed calendar show up while the panel is open:
            // the refresh rewrites the cache this panel watches.
            if (!calendarSync.running) calendarSync.running = true;
        }
    }
    Process {
        id: calendarSync
        command: ["python3", Eitr.Paths.code("walker/scripts/actions/tools/calendars.py"), "refresh", "--if-older", "60"]
    }

    Item {
        id: calendarContent
        anchors.fill: parent
        focus: true
        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Left || event.key === Qt.Key_BracketLeft) moveMonth(-1);
            else if (event.key === Qt.Key_Right || event.key === Qt.Key_BracketRight) moveMonth(1);
            else if (event.key === Qt.Key_Up) moveMonth(-12);
            else if (event.key === Qt.Key_Down) moveMonth(12);
            else if (event.key === Qt.Key_Escape && menu.pendingKey !== "") menu.cancelDelete();
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
                    readonly property bool hasReminders: row > 0 && column > 0 && (ReminderModel.forDay(menu.reminders, day).length > 0
                        || ReminderModel.eventsForDay(menu.events, day).length > 0)
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
            Item {
                width: parent.width
                height: dayCaption.implicitHeight
                Text {
                    id: dayCaption
                    text: Qt.formatDate(menu.selectedDay, "ddd d MMM")
                    color: menu.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                }
                Text {
                    objectName: "reminderDeleteError"
                    anchors.right: parent.right
                    anchors.rightMargin: PanelStyle.selectionActionInset
                    width: Math.min(implicitWidth, parent.width - dayCaption.implicitWidth - 12 - PanelStyle.selectionActionInset)
                    visible: menu.deleteError !== ""
                    text: "󰀦 " + menu.deleteError
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: menu.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    font.bold: true
                }
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
                            Item {
                                id: reminderRow
                                required property var modelData
                                readonly property string key: modelData.id + ":" + modelData.due
                                readonly property bool confirming: menu.pendingKey === key
                                readonly property bool repeating: !!modelData.repeat
                                // A subscribed calendar's event belongs to its provider: no trash button.
                                readonly property bool external: modelData.kind === "event"
                                readonly property string timeLabel: external && modelData.allDay ? Eitr.I18n.tr("All day")
                                    : external && modelData.continued ? "…" : Qt.formatTime(new Date(modelData.due * 1000), "HH:mm")
                                // The backend skips the pending occurrence, so a later one can only end the series.
                                readonly property bool nextOccurrence: !repeating || modelData.occurrence === (modelData.repeat_index || 0)
                                readonly property bool hovered: actionsHover.hovered
                                readonly property Item actionsItem: actions
                                function choicesFocused() { return thisOneButton.activeFocus || allButton.activeFocus; }
                                function restoreFocus() { trashButton.forceActiveFocus(); }
                                objectName: "reminderRow"
                                width: reminderSection.width
                                height: Math.max(reminderText.implicitHeight, PanelStyle.selectionActionHeight)
                                Text {
                                    id: reminderText
                                    width: parent.width - (reminderRow.external ? 0 : actions.width + PanelStyle.selectionActionInset + PanelStyle.selectionActionGap)
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: reminderRow.timeLabel + " · "
                                        + (reminderRow.external ? String.fromCodePoint(0xF00ED) + " " : reminderRow.repeating ? String.fromCodePoint(0xF0456) + " " : "")
                                        + reminderRow.modelData.text + (reminderRow.external ? " · " + reminderRow.modelData.calendar : "")
                                    textFormat: Text.PlainText
                                    wrapMode: Text.Wrap
                                    color: menu.foreground
                                    opacity: reminderRow.confirming ? PanelStyle.secondaryTextOpacity : 1
                                    font.family: DesktopFonts.family
                                    font.pixelSize: PanelStyle.bodySize
                                }
                                Row {
                                    id: actions
                                    visible: !reminderRow.external
                                    anchors.right: parent.right
                                    anchors.rightMargin: PanelStyle.selectionActionInset
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: PanelStyle.selectionActionGap
                                    HoverHandler { id: actionsHover }
                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        visible: reminderRow.confirming && !reminderRow.repeating
                                        text: Eitr.I18n.tr("Delete?")
                                        color: menu.foreground
                                        font.family: DesktopFonts.family
                                        font.pixelSize: PanelStyle.captionSize
                                        font.bold: true
                                    }
                                    Item {
                                        id: thisOneSlot
                                        visible: reminderRow.confirming && reminderRow.repeating
                                        width: thisOneButton.width
                                        height: thisOneButton.height
                                        HoverHandler { id: thisOneHover }
                                        PanelButton {
                                            id: thisOneButton
                                            objectName: "reminderDeleteOccurrence"
                                            foreground: menu.foreground
                                            text: Eitr.I18n.tr("This one")
                                            textSize: PanelStyle.captionSize
                                            width: thisOneMetrics.advanceWidth + 16
                                            height: PanelStyle.selectionActionHeight
                                            outlined: true
                                            available: reminderRow.nextOccurrence && !reminderCancel.running
                                            Accessible.name: Eitr.I18n.tr("Skip this occurrence")
                                            onClicked: menu.deleteReminder(reminderRow.modelData.id, "occurrence")
                                            TextMetrics { id: thisOneMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; text: thisOneButton.text }
                                        }
                                        BarTooltip { target: thisOneSlot; hovered: thisOneHover.hovered; text: reminderRow.nextOccurrence ? Eitr.I18n.tr("Skip this occurrence") : Eitr.I18n.tr("Only the next occurrence can be skipped"); foreground: menu.foreground; background: menu.background }
                                    }
                                    PanelButton {
                                        id: allButton
                                        objectName: "reminderDeleteSeries"
                                        anchors.verticalCenter: parent.verticalCenter
                                        visible: reminderRow.confirming && reminderRow.repeating
                                        foreground: menu.foreground
                                        text: Eitr.I18n.tr("All")
                                        textSize: PanelStyle.captionSize
                                        width: allMetrics.advanceWidth + 16
                                        height: PanelStyle.selectionActionHeight
                                        outlined: true
                                        available: !reminderCancel.running
                                        Accessible.name: Eitr.I18n.tr("Delete every occurrence")
                                        onClicked: menu.deleteReminder(reminderRow.modelData.id, "series")
                                        HoverHandler { id: allHover }
                                        TextMetrics { id: allMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; text: allButton.text }
                                        BarTooltip { target: allButton; hovered: allHover.hovered; text: Eitr.I18n.tr("Delete every occurrence"); foreground: menu.foreground; background: menu.background }
                                    }
                                    PanelButton {
                                        id: trashButton
                                        objectName: "reminderDelete"
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: PanelStyle.selectionActionWidth
                                        height: PanelStyle.selectionActionHeight
                                        icon: true
                                        text: "󰆴"
                                        foreground: menu.foreground
                                        selected: reminderRow.confirming
                                        outlined: reminderRow.confirming
                                        available: !reminderCancel.running
                                        Accessible.name: trashTip.text
                                        onClicked: {
                                            if (reminderRow.confirming && !reminderRow.repeating) menu.deleteReminder(reminderRow.modelData.id, "series");
                                            else menu.requestDelete(reminderRow);
                                        }
                                        HoverHandler { id: trashHover }
                                        BarTooltip { id: trashTip; target: trashButton; hovered: trashHover.hovered; text: reminderRow.confirming && reminderRow.repeating ? Eitr.I18n.tr("Keep reminder") : Eitr.I18n.tr("Delete reminder"); foreground: menu.foreground; background: menu.background }
                                    }
                                }
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
        // While a row asks for confirmation, a press anywhere but its buttons cancels it and still reaches its target.
        MouseArea {
            anchors.fill: parent
            z: 10
            enabled: menu.pendingKey !== ""
            onPressed: function(mouse) {
                const row = menu.pendingRow;
                const point = row ? mapToItem(row.actionsItem, mouse.x, mouse.y) : null;
                if (!point || point.x < 0 || point.y < 0 || point.x > row.actionsItem.width || point.y > row.actionsItem.height)
                    menu.cancelDelete();
                mouse.accepted = false;
            }
        }
    }
}
