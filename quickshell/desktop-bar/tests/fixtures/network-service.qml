import QtQuick
import Quickshell

ShellRoot {
    id: harness
    property int phase: 0
    property int waitTicks: 0
    property string oldEpoch: ""
    property var first: null
    property var second: null
    property var center: null
    property int actionResults: 0
    property int qrResults: 0
    function check(condition, message) {
        if (!condition) { console.error("NETWORK FAIL", message); Qt.exit(1); }
    }
    function networkActionFinished(message) { check(message === "", "action result"); actionResults++; }
    function networkQrFinished(result) { check(result.image === "fixture-image", "QR result"); qrResults++; }
    NetworkService {
        id: service
        qrHelper: Quickshell.shellDir + "/network-reader.py"
    }
    Component {
        id: screen
        Item {
            property string detailToken: ""
            Component.onCompleted: detailToken = service.observe(this)
            property string latencyToken: ""
            function openWifi() { latencyToken = service.observe(this, "latency"); }
            Component.onDestruction: {
                service.release(detailToken);
                service.release(detailToken);
                service.release(latencyToken);
                service.detach(this);
            }
        }
    }
    Component.onCompleted: {
        first = screen.createObject(harness);
        second = screen.createObject(harness);
        center = screen.createObject(harness);
        first.openWifi(); second.openWifi();
    }
    Timer {
        interval: 600
        running: true
        repeat: true
        onTriggered: {
            if (harness.phase === 0) {
                harness.check(service.detailObservers === 3 && service.latencyObservers === 2, "shared demand");
                if (service.details.status !== "ready" || service.latency.status !== "ready") {
                    harness.check(++harness.waitTicks < 8, "read results");
                    return;
                }
                harness.waitTicks = 0;
                harness.first.destroy(); harness.second.destroy();
            } else if (harness.phase === 1) {
                harness.check(service.detailObservers === 1 && service.latencyObservers === 0, "screen removal");
                harness.center.destroy();
                harness.check(service.act(harness, "connect", "/fixture", undefined, {password:"fixture-secret"}), "first action");
                harness.check(!service.act(harness, "power", "/fixture", "false"), "action serialized");
                harness.check(service.generateQr(harness, {type:"open"}, ""), "first QR");
                harness.check(!service.generateQr(harness, {}, ""), "QR serialized");
            } else if (harness.phase === 2) {
                harness.check(service.detailObservers === 0 && service.latencyObservers === 0, "all released");
                harness.check(DesktopData.client.count("network.details") === 0 && DesktopData.client.count("network.latency") === 0, "readers stopped");
                harness.check(harness.actionResults === 2 && harness.qrResults === 1, "private action callbacks");
                harness.first = screen.createObject(harness);
                harness.check(service.details.status === "ready", "cache on reopening");
                harness.first.destroy();
                harness.check(service.generateQr(harness, {type:"open"}, ""), "queued QR");
                service.detach(harness);
                harness.check(!service.qrBusy, "queued QR cancellation releases lock");
            } else if (harness.phase === 3) {
                harness.check(service.detailObservers === 0, "destroy during read");
                harness.check(DesktopData.client.count("network.details") === 0, "queued read cancelled");
                harness.oldEpoch = service.details.epoch;
                harness.first = screen.createObject(harness);
                DesktopData.broker.running = false;
            } else {
                if (DesktopData.restartCount === 0 || service.details.status !== "ready" || service.details.epoch === harness.oldEpoch) {
                    harness.check(++harness.waitTicks < 8, "broker restart and replay");
                    return;
                }
                harness.check(service.detailObservers === 1, "only live tokens replayed");
                harness.first.destroy();
                console.log("NETWORK PASS");
                Qt.quit();
            }
            harness.phase++;
        }
    }
}
