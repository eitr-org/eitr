pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Eitr as Eitr

QtObject {
    id: service
    property var topology: ({monitors: [], primary: "", preferred: [], windowGaps: [6, 6, 6, 6], screenGaps: [12, 12, 12, 12]})
    readonly property var snapshot: DesktopData.topics["display.topology"]
    onSnapshotChanged: if (snapshot && snapshot.status === "ready") {
        topology = snapshot.data;
        DesktopData.refresh("display.settings");
    }
    property var observers: []
    property int readInterval: 3
    property var brightnessWriters: []
    property var nightWriters: []
    readonly property bool brightnessPaused: brightnessWriters.length > 0
    readonly property bool nightPaused: nightWriters.length > 0
    property string brightnessToken: ""
    property string nightToken: ""
    property string settingsToken: ""
    function refreshBrightness() { if (!brightnessPaused) DesktopData.refresh("display.brightness"); }
    function pauseBrightness(owner) {
        if (!brightnessWriters.includes(owner)) brightnessWriters = brightnessWriters.concat([owner]);
        releaseWarm("display.brightness");
        if (brightnessToken) DesktopData.release(brightnessToken);
        brightnessToken = "";
    }
    function resumeBrightness(owner) {
        brightnessWriters = brightnessWriters.filter(writer => writer !== owner);
        if (brightnessPaused) return;
        if (observers.length && !brightnessToken) brightnessToken = DesktopData.observe("display.brightness", service, readInterval);
        refreshBrightness();
    }
    function pauseNightlight(owner) {
        if (!nightWriters.includes(owner)) nightWriters = nightWriters.concat([owner]);
        releaseWarm("display.nightlight");
        if (nightToken) DesktopData.release(nightToken);
        nightToken = "";
    }
    function resumeNightlight(owner) {
        nightWriters = nightWriters.filter(writer => writer !== owner);
        if (nightPaused) return;
        if (observers.length && !nightToken) nightToken = DesktopData.observe("display.nightlight", service, readInterval);
        DesktopData.refresh("display.nightlight");
    }
    function open(owner, interval) {
        if (observers.some(observer => observer.owner === owner)) return;
        observers = observers.concat([{owner: owner, interval: interval || 3}]);
        updateDemand();
    }
    function updateDemand() {
        const interval = observers.length ? Math.min.apply(null, observers.map(observer => observer.interval)) : 3;
        if (observers.length && (!settingsToken || readInterval !== interval)) {
            [brightnessToken, nightToken, settingsToken].forEach(token => { if (token) DesktopData.release(token); });
            readInterval = interval;
            brightnessToken = brightnessPaused ? "" : DesktopData.observe("display.brightness", service, readInterval);
            nightToken = nightPaused ? "" : DesktopData.observe("display.nightlight", service, readInterval);
            settingsToken = DesktopData.observe("display.settings", service);
        }
    }
    function close(owner) {
        observers = observers.filter(observer => observer.owner !== owner);
        if (!observers.length) {
            [brightnessToken, nightToken, settingsToken].forEach(token => { if (token) DesktopData.release(token); });
            brightnessToken = ""; nightToken = ""; settingsToken = "";
        } else updateDemand();
    }
    function releaseWarm(topic) {
        if (!warmTokens[topic]) return;
        const remaining = Object.assign({}, warmTokens);
        const token = remaining[topic];
        delete remaining[topic];
        warmTokens = remaining;
        DesktopData.release(token);
    }
    property var warmTokens: ({})
    readonly property var snapshots: DesktopData.topics
    onSnapshotsChanged: {
        const remaining = Object.assign({}, warmTokens);
        Object.keys(remaining).forEach(topic => {
            if (snapshots[topic] && snapshots[topic].status !== "loading") {
                // Released later: releasing changes DesktopData.topics, which this handler is
                // reacting to. One closure per token, since Qt.callLater merges repeated calls.
                const token = remaining[topic];
                Qt.callLater(() => DesktopData.release(token));
                delete remaining[topic];
            }
        });
        warmTokens = remaining;
    }
    property Timer warmup: Timer {
        interval: 8000; running: true
        onTriggered: {
            const tokens = {};
            ["display.brightness", "display.nightlight"].forEach(topic => {
                if ((topic === "display.brightness" && !service.brightnessPaused) || (topic === "display.nightlight" && !service.nightPaused))
                    tokens[topic] = DesktopData.observe(topic, service);
            });
            service.warmTokens = tokens;
        }
    }
    function refresh() { DesktopData.refresh("display.topology"); }
    property Timer debounce: Timer { interval: 80; onTriggered: service.refresh() }
    property Connections events: Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (["monitoradded", "monitoraddedv2", "monitorremoved", "configreloaded"].includes(event.name)) service.debounce.restart();
        }
    }
    property Connections screens: Connections {
        target: Quickshell
        function onScreensChanged() { service.debounce.restart(); }
    }
    property PreferenceWatch primary: PreferenceWatch {
        path: Eitr.Paths.config("hypr/primary-display")
        onChanged: service.debounce.restart()
    }
    property PreferenceWatch preferred: PreferenceWatch {
        path: Eitr.Paths.config("hypr/preferred-outputs")
        onChanged: service.debounce.restart()
    }
    Component.onCompleted: DesktopData.observe("display.topology", service)
    Component.onDestruction: DesktopData.releaseOwner(service)
}
