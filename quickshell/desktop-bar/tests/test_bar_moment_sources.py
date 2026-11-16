"""Notification, keyboard and MPRIS events through the real QML queue owner."""
from pathlib import Path
import tempfile
import unittest

from layout_render import copy_runtime, render_environment, render

FIXTURE = r'''import QtQuick
import Quickshell
import Quickshell.Io
import "." as Bar
ShellRoot {
    id: shell
    property bool barMoments: true
    property bool verticalBar: false
    QtObject { id: island; property bool hovered: false; property bool expanded: false; property bool morphed: false }
    QtObject { id: mediaIsland; property bool hovered: false; property bool expanded: false; property bool morphed: false }
    QtObject { id: notification; property int id: 1; property string summary: "Original"; property int urgency: 1; property string image: ""; property var hints: ({}) }
    QtObject { id: critical; property int id: 2; property string summary: "Critical"; property int urgency: 2; property string image: ""; property var hints: ({}) }
    QtObject { id: notices; property bool doNotDisturb: false; property var popups: [notification]; property var timestamps: ({}) }
    QtObject { id: keyboard; property int activeLayout: 0; property var layouts: [{index: 0, code:"us", label: "English (US)"}, {index: 1, code:"us", label: "English (US International)"}] }
    QtObject { id: player; property string trackTitle: "First song"; property string trackArtist: "Artist"; property bool isPlaying: true }
    QtObject { id: strip; property var player: player }
    QtObject { id: bar; property bool dynamicLayout: true; property var notificationsRef: notices; property var keyboardMenu: keyboard; property var mediaStrip: strip }
    Bar.BarMoments { id: moments; host: shell; barHost: bar; middle: island; media: mediaIsland }
    QtObject { id: audio; property real volume: 0.5; property bool muted: false }
    QtObject { id: device; property bool connected: false; property string icon: "audio-headphones"; property string name: "Headphones"; property string address: "fixture"; property bool batteryAvailable: true; property real battery: 0.8 }
    QtObject { id: adapter; property var devices: ({values:[device]}) }
    function sources() { return moments.children.find(child => child.syncPopups !== undefined); }
    Process {
        id: levelEvent
        command: ["bash", "-c", "printf '%s' '{\"kind\":\"brightness\",\"level\":100,\"at\":'$(date +%s%3N)'}' > \"$XDG_RUNTIME_DIR/eitr-level-moment.json\""]
    }
    property int stage: 0
    function require(condition, message) { if (!condition) throw new Error(message); }
    function clear() { moments.queueState = {active:null, queue:[]}; }
    Timer {
        interval: 150; running: true; repeat: true
        onTriggered: {
            try {
                if (shell.stage === 0) {
                    require(!moments.current, "Initial state created a moment");
                    keyboard.activeLayout = 1;
                } else if (shell.stage === 1) {
                    require(moments.current.kind === "layout" && moments.current.text === "English (US International)", "Layout event missing");
                    clear(); keyboard.layouts = [{index: 0, code:"us", label: "English (US)"}]; keyboard.activeLayout = 0;
                } else if (shell.stage === 2) {
                    require(!moments.current, "Single-layout event shown");
                    player.isPlaying = false;
                } else if (shell.stage === 3) {
                    require(!moments.current, "Pause created song moment");
                    player.isPlaying = true; player.trackTitle = "Second song"; player.trackArtist = "New artist";
                } else if (shell.stage === 4) {
                    require(moments.current.kind === "song" && moments.current.text === "Second song · New artist", "Song metadata was not coalesced");
                    clear(); notification.summary = "Replacement with same id";
                } else if (shell.stage === 5) {
                    require(moments.current.kind === "notification" && moments.current.text === notification.summary, "Same-id replacement lost");
                    notices.popups = [critical];
                } else if (shell.stage === 6) {
                    require(moments.current.critical && moments.current.deadline === 0, "Critical notification expired");
                    notices.popups = [];
                } else if (shell.stage === 7) {
                    require(!moments.current, "Dismissed critical moment remained");
                    notices.doNotDisturb = true; notices.popups = [notification];
                } else if (shell.stage === 8) {
                    require(!moments.current, "DND showed moment");
                    notices.doNotDisturb = false; notices.popups = [];
                    island.hovered = true;
                    moments.submit({kind:"volume", level:50});
                } else if (shell.stage === 9) {
                    require(!moments.current && moments.queueState.queue.length === 1, "Hovered island did not defer");
                    island.hovered = false;
                } else if (shell.stage === 10) {
                    require(moments.current.kind === "volume", "Deferred moment did not resume");
                    island.morphed = true;
                } else if (shell.stage === 11) {
                    require(!moments.current, "Panel did not defer");
                    island.morphed = false; Bar.FocusMode.enabled = true;
                } else if (shell.stage === 12) {
                    require(!moments.current, "Focus showed moment");
                    Bar.FocusMode.enabled = false; clear(); shell.barMoments = false;
                    notification.summary = "Other layout"; player.trackTitle = "Other song";
                } else if (shell.stage === 13) {
                    require(!moments.current && !moments.queueState.queue.length, "Other layout received moment");
                    shell.barMoments = true;
                    sources().adapter = adapter; sources().audio = audio;
                } else if (shell.stage === 14) {
                    require(!moments.current, "Initial Bluetooth or audio state created moment");
                    device.connected = true;
                } else if (shell.stage === 15) {
                    require(moments.current.kind === "bluetooth" && moments.current.text.indexOf("80%") !== -1, "Bluetooth connect missing battery");
                    device.connected = false;
                } else if (shell.stage === 16) {
                    require(moments.current.text.indexOf("Disconnected") !== -1, "Bluetooth disconnect missing");
                    clear(); audio.volume = 0.64;
                } else if (shell.stage === 17) {
                    require(moments.current.kind === "volume" && moments.current.level === 64, "Native volume observation missing");
                    audio.muted = true;
                } else if (shell.stage === 18) {
                    require(moments.current.icon === "󰖁", "Mute icon missing");
                    clear(); levelEvent.running = true;
                } else {
                    require(moments.current && moments.current.kind === "brightness" && moments.current.level === 100, "Watched brightness event missing");
                    clear();
                    require(!moments.current && !moments.queueState.queue.length, "Other layout received moment");
                    console.log("DYNAMIC_SOURCES_OK"); Qt.quit();
                }
                shell.stage++;
            } catch (error) { console.error(error); Qt.exit(1); }
        }
    }
}'''


class BarMomentSourceTests(unittest.TestCase):
    def test_events_and_interaction_guards(self):
        with tempfile.TemporaryDirectory(prefix='eitr-moment-events-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            path = folder / 'fixture.qml'
            path.write_text(FIXTURE)
            code, output = render(path, render_environment(directory), 10)
            self.assertEqual(code, 0, output)
            self.assertIn('DYNAMIC_SOURCES_OK', output)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Unable to assign', 'Error:'):
                self.assertNotIn(error, output)
