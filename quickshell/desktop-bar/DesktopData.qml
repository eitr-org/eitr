pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "DesktopDataProtocol.js" as Protocol

QtObject {
    id: facade
    property var topics: ({})
    property var networkDomain: ({busy: false, name: ""})
    property var powerDomain: ({busy: false, name: ""})
    property var captureDomain: ({busy: false, name: ""})
    property var diagnostics: ({})
    property int restartCount: 0
    property int failures: 0
    property bool retryAvailable: false
    property var client: Protocol.createClient(send, publish)
    function send(frame) { broker.write(JSON.stringify(frame) + "\n"); }
    function publish() { topics = Object.assign({}, client.states); networkDomain = Object.assign({}, client.domain); captureDomain = Object.assign({}, client.captureDomain); powerDomain = Object.assign({}, client.powerDomain); }
    function observe(topic, owner, interval) { return client.observe(topic, owner, interval); }
    function release(token) { client.release(token); }
    function releaseOwner(owner) { client.releaseOwner(owner); }
    function refresh(topic) { client.refresh(topic); }
    function retry() {
        if (broker.running) return;
        failures = 0;
        retryAvailable = false;
        restartTimer.stop();
        restartCount++;
        broker.running = true;
    }
    function status() {
        if (broker.running) send({v: 1, op: "status", id: "diagnostics"});
        const result = {};
        ["hardware.details", "display.topology", "display.settings", "display.brightness", "display.nightlight", "power.battery", "power.profile", "power.radios", "network.summary", "network.details", "network.latency", "capture.summary", "capture.details", "capture.options"].forEach(topic => {
            const state = topics[topic];
            result[topic] = Object.assign({}, diagnostics[topic], {
                ageMs: state && state.updatedAt ? Date.now() - state.updatedAt : null,
                observers: client.count(topic), restartCount: restartCount,
                lastError: state ? state.error || "" : "",
                inFlight: broker.running && diagnostics[topic] ? diagnostics[topic].inFlight : 0
            });
        });
        return JSON.stringify({topics: result, restartCount: restartCount, retryAvailable: retryAvailable});
    }
    Component.onCompleted: broker.running = true
    property Process broker: Process {
        command: ["python3", Quickshell.shellDir + "/scripts/bar-data.py"]
        stdinEnabled: true
        stdout: SplitParser {
            onRead: line => {
                facade.client.receive(line);
                try {
                    const frame = JSON.parse(line);
                    if (frame.v === 1 && frame.epoch === facade.client.epoch() && frame.op === "status") facade.diagnostics = frame.data;
                } catch (error) {}
            }
        }
        // Protocol failures are reported as codes; never retain adapter stderr.
        stderr: SplitParser { onRead: line => {} }
        onStarted: stableTimer.restart()
        onRunningChanged: if (!running) {
            stableTimer.stop();
            facade.client.died();
            facade.failures++;
            if (facade.failures > 6) facade.retryAvailable = true;
            else {
                restartTimer.interval = Protocol.restartDelay(facade.failures, Math.random());
                restartTimer.start();
            }
        }
    }
    property Timer restartTimer: Timer {
        onTriggered: { facade.restartCount++; broker.running = true; }
    }
    property Timer stableTimer: Timer {
        interval: 60000
        onTriggered: facade.failures = 0
    }
    property IpcHandler ipc: IpcHandler {
        target: "data"
        function status(): string { return facade.status(); }
        function retry(): void { facade.retry(); }
    }
}
