pragma Singleton
import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr

// Optional sounds for desktop events, off until the user turns them on (Control Center >
// Sound, Settings > Sound or Walker's Event Sounds menu, which writes the watched file).
// Sounds come from the freedesktop sound theme and play through PipeWire. Nothing
// plays during Do Not Disturb, which Game Mode also turns on.
QtObject {
    id: sounds
    property bool notifications: false
    property bool charger: false
    // Mirrored from the notification service, which owns Do Not Disturb.
    property bool doNotDisturb: false
    readonly property string folder: "/usr/share/sounds/freedesktop/stereo/"
    property double lastPlayed: 0
    property var data: ({version: 1})

    function play(name) {
        if (doNotDisturb) return;
        // A burst of events (several notifications at once) chimes once.
        var now = Date.now();
        if (now - lastPlayed < 400) return;
        lastPlayed = now;
        Quickshell.execDetached(["pw-play", folder + name + ".oga"]);
    }
    function notificationArrived(notification) {
        if (!notifications || !notification) return;
        var urgency = notification.urgency !== undefined ? notification.urgency : 1;
        if (urgency === 0) return;
        // Senders that play their own sound ask the desktop to stay quiet.
        if (notification.hints && notification.hints["suppress-sound"]) return;
        play(urgency === 2 ? "dialog-warning" : "message-new-instant");
    }
    function chargerPlugged(pluggedIn) {
        if (charger) play(pluggedIn ? "power-plug" : "power-unplug");
    }
    function setEnabled(key, value) {
        if (key !== "notifications" && key !== "charger") return;
        sounds[key] = value;
        data = Object.assign({}, data, {version: 1, notifications: notifications, charger: charger});
        file.setText(JSON.stringify(data) + "\n");
    }

    property FileView file: FileView {
        path: Eitr.Paths.config("eitr/sounds.json")
        watchChanges: true; atomicWrites: true; printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                sounds.data = Eitr.Paths.settings(text());
                sounds.notifications = sounds.data.notifications === true;
                sounds.charger = sounds.data.charger === true;
            } catch (error) {
                console.warn("Invalid sound settings:", error);
            }
        }
        onLoadFailed: { sounds.notifications = false; sounds.charger = false; }
    }
}
