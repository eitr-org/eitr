pragma Singleton
import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../ReminderModel.js" as ReminderModel
import "../clock/AlarmModel.js" as AlarmModel

Scope {
    id: alarms
    property var items: []
    property double now: Date.now()
    readonly property var ringing: AlarmModel.ring(items, now)
    readonly property string ringingId: ringing ? ringing.id : ""
    readonly property string playbackKey: ringing ? ringing.id + ":" + ringing.alarm.ringUntil : ""
    property bool unlocked: false
    readonly property bool busy: action.running
    readonly property bool choosingSound: picker.running
    signal finished(bool success)
    signal soundChosen(string path)

    function chooseSound() { picker.running = true; }

    function run(operation, identifier, payload) {
        if (busy) return;
        action.payload = payload ? JSON.stringify(payload) : "";
        action.stdinEnabled = true;
        action.command = ["python3", Eitr.Paths.code("walker/scripts/actions/tools/reminders.py"), operation];
        if (identifier) action.command = action.command.concat([identifier]);
        action.running = true;
    }

    onPlaybackKeyChanged: {
        unlocked = false;
        playback.running = false;
        if (ringing) {
            lockStatus.running = true;
            repeatSound.restart();
        }
    }

    FileView {
        id: state
        path: Eitr.Paths.state("eitr/reminders.json")
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            alarms.now = Date.now();
            alarms.items = ReminderModel.parseAlarms(text());
        }
        onLoadFailed: alarms.items = []
    }

    Process {
        id: action
        property string payload: ""
        onStarted: {
            if (payload) write(payload);
            stdinEnabled = false;
        }
        onExited: exitCode => {
            state.reload();
            alarms.finished(exitCode === 0);
        }
    }

    Process {
        id: picker
        command: ["python3", Eitr.Paths.library("eitr_file_chooser.py"), "audio",
            Eitr.I18n.tr("Choose a file…"), Eitr.I18n.tr("Audio files")]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const reply = JSON.parse(text);
                    const path = reply.ok && reply.result ? reply.result.path : "";
                    if (path) alarms.soundChosen(path);
                } catch (error) {
                    console.warn("Alarm sound picker:", error);
                }
            }
        }
    }

    // The compositor protects the lock surface. Check the existing lock launcher as well
    // so the overlay only requests exclusive keyboard focus after the session unlocks.
    Process {
        id: lockStatus
        command: ["timeout", "2s", "bash", Eitr.Paths.code("quickshell/lockscreen/scripts/launch.sh"), "active"]
        onExited: exitCode => alarms.unlocked = Boolean(alarms.ringing) && exitCode === 1
    }
    Timer {
        interval: 1500
        repeat: true
        running: Boolean(alarms.ringing)
        onTriggered: {
            alarms.now = Date.now();
            if (alarms.ringing) lockStatus.running = true;
        }
    }

    Timer {
        id: repeatSound
        interval: 300
        onTriggered: {
            alarms.now = Date.now();
            if (!alarms.ringing || playback.running) return;
            playback.fallback = false;
            playback.command = EventSounds.playback(alarms.ringing.alarm.sound);
            playback.running = true;
        }
    }
    Process {
        id: playback
        property bool fallback: false
        onExited: exitCode => {
            if (!alarms.ringing || repeatSound.running) return;
            if (exitCode !== 0 && !fallback && alarms.ringing.alarm.sound !== EventSounds.timerSound) {
                fallback = true;
                command = EventSounds.playback(EventSounds.timerSound);
                running = true;
            } else {
                repeatSound.restart();
            }
        }
    }
}
