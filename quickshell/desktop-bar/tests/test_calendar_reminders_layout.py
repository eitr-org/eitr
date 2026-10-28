from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'
THEMES = {'dark': ('#18212b', '#e9eef1'), 'light': ('#f5f0e7', '#252936')}
POPUP_STUB = '''import QtQuick
import "JsonState.js" as JsonState
Item {
    id: popup
    function updateContent(action) { action(); }
    function applySnapshot(name, value) { if (JsonState.changed(popup[name], value)) popup[name] = value; }
    property bool opened: true
    property var keyTarget
    property color foreground
    property color background
    property color accent
    property var contentGaps: [4,4,4,4]
    property bool detached: true
    property string barEdge: "top"
    property real verticalContentInset: 0
    width: implicitWidth; height: implicitHeight
}
'''
# Stands in for reminders.py: records its arguments and edits the state file as the real cancel would.
FAKE_BACKEND = '''import json, os, sys
from pathlib import Path
Path(__file__).with_name("calls.jsonl").open("a").write(json.dumps(sys.argv[1:]) + "\\n")
command, identifier, scope = sys.argv[1:]
if identifier == "missing":
    print("No such reminder.", file=sys.stderr)
    sys.exit(1)
state = Path(os.environ["XDG_STATE_HOME"]) / "eitr/reminders.json"
reminders = json.loads(state.read_text())
if scope == "series":
    state.write_text(json.dumps([item for item in reminders if item["id"] != identifier]))
'''
# Finds the delegates inside the ScrollView by objectName.
FIND = '''
    function find(item, name, found) {
        found = found || [];
        if (!item) return found;
        if (item.objectName === name) found.push(item);
        const kids = item.children || [];
        for (let index = 0; index < kids.length; index++) find(kids[index], name, found);
        if (item.contentItem && kids.indexOf(item.contentItem) < 0) find(item.contentItem, name, found);
        return found;
    }
    function child(item, name) { return find(item, name)[0]; }
    function rows() { return find(panel, "reminderRow"); }
    function row(id) { return rows().filter(function(candidate) { return candidate.modelData.id === id; })[0]; }
    function check(condition, message) { if (!condition) throw new Error(message); }
'''


def run_fixture(test, folder, fixture_text, extra_environment=None):
    fixture = folder/'fixture.qml'
    fixture.write_text(fixture_text)
    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                       QML_IMPORT_PATH=str(ROOT/'quickshell'), XDG_CONFIG_HOME=str(folder),
                       XDG_STATE_HOME=str(folder), XDG_CACHE_HOME=str(folder), XDG_RUNTIME_DIR=str(folder),
                       DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='',
                       **(extra_environment or {}))
    try:
        result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired as error:
        test.fail(str(error.stdout) + str(error.stderr))
    test.assertEqual(result.returncode, 0, result.stdout+result.stderr)
    test.assertIn('CALENDAR_OK', result.stdout+result.stderr, result.stdout+result.stderr)


def keep_renders(captures):
    if os.environ.get('EITR_CALENDAR_REVIEW_RENDERS'):
        destination = Path(os.environ['EITR_CALENDAR_REVIEW_RENDERS'])
        destination.mkdir(parents=True, exist_ok=True)
        for capture in captures:
            shutil.copy(capture, destination/capture.name)


def copy_bar(folder):
    for source in BAR.iterdir():
        if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
            shutil.copy(source, folder / source.name)
    (folder/'ThemedPopup.qml').write_text(POPUP_STUB)


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class CalendarReminderLayoutTests(unittest.TestCase):
    def test_reminder_list_is_bounded_and_fixed_in_both_themes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            folder = Path(directory)
            copy_bar(folder)
            for theme, (background, foreground) in THEMES.items():
                capture = folder/(theme+'.png')
                run_fixture(self, folder, '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 560; implicitHeight: 700
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.CalendarMenu {
                id: panel
                x: 12; y: 12
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#509475"
            }
            property real emptyHeight: 0
            Timer {
                interval: 250; running: true
                onTriggered: {
                    const day = new Date(2026, 9, 30, 15);
                    panel.selectedDay = day; panel.viewYear = 2026; panel.viewMonth = 9;
                    sample.emptyHeight = panel.height;
                    panel.reminders = Array.from({length: 20}, function(unused, index) {
                        return {id: String(index), text: "Dentist appointment with a deliberately long title for wrapping", due: day.getTime()/1000, repeat: {frequency: "weekly", weekdays: [4]}, repeat_anchor: "2026-10-30T15:00:00", repeat_index: 0};
                    });
                    finish.start();
                }
            }
            Timer {
                id: finish; interval: 250
                onTriggered: {
                    if (panel.height > sample.height - 24 || panel.selectedReminders.length !== 20)
                        throw new Error("Calendar overflow or missing reminders: " + panel.height + "/" + panel.selectedReminders.length);
                    // The calendar keeps one height whether a day has reminders or not.
                    if (panel.height !== sample.emptyHeight)
                        throw new Error("Calendar height changed: " + sample.emptyHeight + " -> " + panel.height);
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE"); console.log("CALENDAR_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('BACKGROUND', background).replace('FOREGROUND', foreground).replace('CAPTURE', str(capture)))
                self.assertTrue(capture.exists())
                keep_renders([capture])

    def test_subscribed_events_are_listed_without_a_trash_button(self):
        for theme, (background, foreground) in THEMES.items():
            with self.subTest(theme=theme), tempfile.TemporaryDirectory(dir=ROOT) as directory:
                folder = Path(directory)
                copy_bar(folder)
                (folder/'eitr').mkdir()
                (folder/'eitr/reminders.json').write_text(json.dumps([
                    {'id': 'once', 'text': 'Dentist', 'due': int(datetime(2026, 10, 30, 9).timestamp())}]))
                (folder/'eitr/calendar-events.json').write_text(json.dumps({'updated': 0, 'events': [
                    {'key': 'meet', 'calendarId': 'c', 'calendar': 'Work', 'title': 'Planning',
                     'start': int(datetime(2026, 10, 30, 10).timestamp()), 'end': int(datetime(2026, 10, 30, 11).timestamp())},
                    {'key': 'trip', 'calendarId': 'c', 'calendar': 'Family', 'title': 'Trip', 'allDay': True,
                     'date': '2026-10-29', 'endDate': '2026-10-31'},
                    {'key': 'bad', 'calendar': 'Work', 'title': 'Missing times'}]}))
                capture = folder/f'{theme}-events.png'
                run_fixture(self, folder, '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 560; implicitHeight: 700
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.CalendarMenu {
                id: panel
                x: 12; y: 12
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#509475"
                Component.onCompleted: { selectedDay = new Date(2026, 9, 30, 15); viewYear = 2026; viewMonth = 9; }
            }
FIND
            Timer {
                interval: 300; running: true
                onTriggered: {
                    try {
                        sample.check(sample.rows().length === 3, "expected a reminder and two events, got " + sample.rows().length);
                        sample.check(sample.rows()[0].modelData.id === "trip" && sample.rows()[1].modelData.id === "once" && sample.rows()[2].modelData.id === "meet", "wrong order");
                        sample.check(!sample.child(sample.row("trip"), "reminderDelete").visible && !sample.child(sample.row("meet"), "reminderDelete").visible, "an event has a trash button");
                        sample.check(sample.child(sample.row("once"), "reminderDelete").visible, "the reminder lost its trash button");
                        sample.check(sample.row("meet").external && sample.row("trip").timeLabel === "All day", "event labels");
                        const emptyDay = panel.height;
                        panel.selectedDay = new Date(2026, 9, 29, 15);
                        sample.check(sample.rows().length === 1 && panel.height === emptyDay, "the two-day event or the height is wrong");
                        panel.selectedDay = new Date(2026, 9, 30, 15);
                    } catch (error) { console.log("CALENDAR_FAIL " + error.message); Qt.exit(1); return; }
                    sample.grabToImage(function(result) { result.saveToFile("CAPTURE"); console.log("CALENDAR_OK"); Qt.quit(); });
                }
            }
        }
    }
}'''.replace('FIND', FIND).replace('BACKGROUND', background).replace('FOREGROUND', foreground)
                    .replace('CAPTURE', str(capture)))
                self.assertTrue(capture.exists())
                keep_renders([capture])

    def test_delete_buttons_confirm_and_run_the_backend_in_both_themes(self):
        for theme, (background, foreground) in THEMES.items():
            with self.subTest(theme=theme), tempfile.TemporaryDirectory(dir=ROOT) as directory:
                folder = Path(directory)
                copy_bar(folder)
                backend = folder/'code/walker/scripts/actions/tools/reminders.py'
                backend.parent.mkdir(parents=True)
                backend.write_text(FAKE_BACKEND)
                state = folder/'eitr/reminders.json'
                state.parent.mkdir()

                def at(hour, day=30):
                    return int(datetime(2026, 10, day, hour).timestamp())

                weekly = {'frequency': 'weekly', 'weekdays': [4]}
                state.write_text(json.dumps([
                    {'id': 'once', 'text': 'Dentist', 'due': at(9)},
                    {'id': 'next', 'text': 'Stand-up', 'due': at(10), 'repeat': weekly,
                     'repeat_anchor': '2026-10-30T10:00:00', 'repeat_index': 0},
                    {'id': 'later', 'text': 'Review', 'due': at(11, 23), 'repeat': weekly,
                     'repeat_anchor': '2026-10-23T11:00:00', 'repeat_index': 0},
                    {'id': 'missing', 'text': 'Gone', 'due': at(12)},
                ]))
                captures = {name: folder/f'{theme}-{name}.png' for name in ('normal', 'confirm', 'choice', 'error')}
                script = '''
    property real fixedHeight: 0
    property int step: 0
    function capture(path) { sample.grabToImage(function(result) { result.saveToFile(path); }); }
    function actionsInset(item) {
        const trash = child(item, "reminderDelete");
        const point = trash.mapToItem(item, 0, 0);
        check(trash.visible && trash.width === 24 && trash.height === 24, "trash button is not a visible 24x24 action");
        check(item.width - point.x - trash.width === 4, "trash button is not inset 4 px: " + (item.width - point.x - trash.width));
        check(Math.abs(point.y + trash.height / 2 - item.height / 2) <= 0.5, "trash button is not vertically centred");
        return trash;
    }
    function advance() {
        const once = row("once"), next = row("next"), later = row("later"), missing = row("missing");
        // Each step ends with at most one capture, rendered before the next step changes the state.
        if (sample.step === 0) {
            if (rows().length !== 4) return;
            sample.fixedHeight = panel.height;
            rows().forEach(actionsInset);
            check(!child(once, "reminderDeleteOccurrence").parent.visible, "choices shown before a click");
            capture("NORMAL");
        } else if (sample.step === 1) {
            actionsInset(once).clicked();
            check(once.confirming && panel.pendingKey === once.key, "one-time reminder did not ask");
            check(panel.height === sample.fixedHeight, "height changed while confirming");
            capture("CONFIRM");
        } else if (sample.step === 2) {
            actionsInset(once).clicked();
        } else if (sample.step === 3) {
            if (row("once") || panel.pendingKey !== "") return;
            check(rows().length === 3, "deleted reminder still listed");
            actionsInset(next).clicked();
            check(next.confirming, "repeating reminder did not ask");
            check(child(next, "reminderDeleteOccurrence").available && child(next, "reminderDeleteSeries").visible, "choices missing");
            check(panel.height === sample.fixedHeight, "height changed while choosing");
            capture("CHOICE");
        } else if (sample.step === 4) {
            actionsInset(next).clicked();
            check(panel.pendingKey === "", "second trash click did not cancel the choice");
            actionsInset(next).clicked();
            panel.confirmationTimeout = 150;
        } else if (sample.step === 5) {
            if (panel.pendingKey !== "") return;
            panel.confirmationTimeout = 5000;
            actionsInset(next).clicked();
            child(next, "reminderDeleteOccurrence").clicked();
        } else if (sample.step === 6) {
            if (panel.pendingKey !== "") return;
            actionsInset(later).clicked();
            check(!child(later, "reminderDeleteOccurrence").available, "a later occurrence offered This one");
            child(later, "reminderDeleteSeries").clicked();
        } else if (sample.step === 7) {
            if (row("later") || panel.pendingKey !== "") return;
            actionsInset(missing).clicked();
            actionsInset(missing).clicked();
        } else if (sample.step === 8) {
            if (panel.deleteError === "") return;
            check(panel.deleteError === "No such reminder.", "unexpected error: " + panel.deleteError);
            check(child(panel, "reminderDeleteError").visible, "error is not shown");
            check(panel.height === sample.fixedHeight, "height changed with an error");
            sample.grabToImage(function(result) { result.saveToFile("ERROR"); console.log("CALENDAR_OK"); Qt.quit(); });
            driver.running = false;
            return;
        }
        sample.step++;
    }
    Timer {
        id: driver
        interval: 120; repeat: true; running: true
        onTriggered: {
            try { sample.advance(); }
            catch (error) { console.log("CALENDAR_FAIL " + error.message); Qt.exit(1); }
        }
    }
'''
                for name, path in captures.items():
                    script = script.replace('"' + name.upper() + '"', json.dumps(str(path)))
                run_fixture(self, folder, '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 560; implicitHeight: 700
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.CalendarMenu {
                id: panel
                x: 12; y: 12
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#509475"
                Component.onCompleted: { selectedDay = new Date(2026, 9, 30, 15); viewYear = 2026; viewMonth = 9; }
            }
FIND
SCRIPT
        }
    }
}'''.replace('FIND', FIND).replace('SCRIPT', script).replace('BACKGROUND', background)
                    .replace('FOREGROUND', foreground), {'EITR_CODE_ROOT': str(folder/'code')})
                calls = [json.loads(line) for line in (backend.parent/'calls.jsonl').read_text().splitlines()]
                self.assertEqual(calls, [['cancel', 'once', 'series'], ['cancel', 'next', 'occurrence'],
                                         ['cancel', 'later', 'series'], ['cancel', 'missing', 'series']])
                for path in captures.values():
                    self.assertTrue(path.exists(), path)
                keep_renders(captures.values())


if __name__ == '__main__':
    unittest.main()
