pragma Singleton
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "Spectrum.js" as Spectrum

QtObject {
    id: provider
    property var consumers: []
    property var levels: []
    property bool hasFrame: false
    property bool failed: false
    property int retryDelay: 500
    readonly property bool wanted: consumers.length > 0
    readonly property bool audioActive: hasFrame && levels.some(level => level > 0)
    property var config: ({bars: 4, fps: 30, smoothing: false})
    property bool reconfiguring: false
    function update() {
        if (!wanted) { reconfigure.stop(); return; }
        const desired = Spectrum.configuration(consumers);
        if (desired.bars === config.bars && desired.fps === config.fps && desired.smoothing === config.smoothing)
            reconfigure.stop();
        else
            reconfigure.restart();
    }
    property Timer reconfigure: Timer {
        interval: 300
        onTriggered: {
            provider.stale.stop();
            const wasRunning = provider.process.running;
            provider.reconfiguring = true;
            if (!wasRunning) provider.applyConfig();
        }
    }
    function applyConfig() {
        config = Spectrum.configuration(consumers);
        reconfiguring = false;
    }
    function acquire(consumer) {
        if (consumers.indexOf(consumer) === -1) consumers = consumers.concat([consumer]);
        update();
    }
    function release(consumer) {
        consumers = consumers.filter(existing => existing !== consumer);
        update();
    }
    onWantedChanged: {
        if (!wanted) {
            reconfigure.stop(); retry.stop(); stale.stop(); stable.stop(); failed = false; retryDelay = 500;
            hasFrame = false; levels = [];
        }
    }
    property Process process: Process {
        command: ["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/cava-bar.py"), "--bars", String(provider.config.bars), "--framerate", String(provider.config.fps), "--monstercat", provider.config.smoothing ? "1" : "0"]
        running: provider.wanted && !provider.failed && !provider.reconfiguring
        stdout: SplitParser {
            onRead: line => {
                const values = Spectrum.frame(line);
                if (values) {
                    provider.levels = values; provider.hasFrame = true;
                    stale.restart();
                }
            }
        }
        onExited: {
            if (provider.reconfiguring) { provider.applyConfig(); return; }
            provider.hasFrame = false; provider.levels = [];
            if (provider.wanted) { provider.failed = true; retry.start(); }
        }
    }
    property Timer retry: Timer {
        interval: provider.retryDelay
        onTriggered: {
            provider.retryDelay = Math.min(30000, provider.retryDelay * 2);
            provider.failed = false;
        }
    }
    property Timer stable: Timer {
        interval: 10000; running: provider.process.running
        onTriggered: provider.retryDelay = 500
    }
    property Timer stale: Timer {
        interval: 1500
        onTriggered: { provider.hasFrame = false; provider.levels = []; }
    }
}
