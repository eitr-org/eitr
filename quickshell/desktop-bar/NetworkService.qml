import QtQuick
import Quickshell
import Quickshell.Io
import "NetworkStatus.js" as NetworkStatus

Item {
    id: service
    property var summary: ({status: "loading", data: {}})
    property var details: ({status: "loading", data: {}})
    property var latency: ({status: "loading", data: {}})
    property int detailObservers: 0
    property int latencyObservers: 0
    readonly property var device: details.data.devices && details.data.devices.length ? details.data.devices[0] : null
    readonly property var connected: device ? device.networks.find(network => network.connected) : null
    readonly property string glyph: NetworkStatus.glyph(Object.assign({}, details.updatedAt >= summary.updatedAt ? details.data : summary.data,
        {blocked: summary.data.blocked}))
    readonly property string focusGlyph: summary.data.wired ? "󰈀" : glyph
    property bool busy: false
    readonly property string actionKind: operation.command.length > 2 ? operation.command[2] : ""
    property bool qrBusy: false
    property string helper: Quickshell.shellDir + "/scripts/wifi-popup.py"
    property string qrHelper: Quickshell.shellDir + "/scripts/wifi-qr.py"
    property var actionOwner: null
    property var actionInput: ({})
    property var qrOwner: null
    property var qrInput: ({})
    property int readSequence: 0
    property var scheduledReads: ({})
    property bool qrScheduled: false
    property var model: NetworkStatus.createOwner(startRead, stopRead, publish)

    function publish() {
        summary = Object.assign({}, model.topics.summary);
        details = Object.assign({}, model.topics.details);
        latency = Object.assign({}, model.topics.latency);
        detailObservers = model.count("details");
        latencyObservers = model.count("latency");
    }
    function observe(owner, topic) { return model.observe(owner, topic); }
    function release(token) { model.release(token); }
    function refresh() { model.refresh("details"); }
    function reader(topic) {
        return topic === "summary" ? summaryQuery : topic === "details" ? detailsQuery : pingQuery;
    }
    function startRead(topic) {
        if (topic === "latency") {
            if (!device || device.state !== "connected") return false;
            pingQuery.command = ["python3", helper, "probe", device.name];
        }
        const request = ++readSequence;
        scheduledReads[topic] = request;
        Qt.callLater(function() {
            if (scheduledReads[topic] !== request) return;
            delete scheduledReads[topic];
            reader(topic).running = true;
        });
        return true;
    }
    function stopRead(topic) {
        if (scheduledReads[topic]) {
            delete scheduledReads[topic];
            model.finish(topic, "", 1);
        } else reader(topic).running = false;
    }
    function act(owner, kind, path, extra, input) {
        if (busy) return false;
        busy = true;
        actionOwner = owner;
        owner.networkActionFinished("");
        actionInput = input || ({});
        operation.command = ["python3", helper, kind, path];
        if (extra !== undefined) operation.command = operation.command.concat([extra]);
        operation.running = true;
        return true;
    }
    function generateQr(owner, network, password) {
        if (qrBusy) return false;
        qrBusy = true;
        qrOwner = owner;
        qrInput = {network: network, password: password};
        qrScheduled = true;
        Qt.callLater(function() {
            if (!qrScheduled) return;
            qrScheduled = false;
            qrQuery.running = true;
        });
        return true;
    }
    function detach(owner) {
        model.releaseOwner(owner);
        if (actionOwner === owner) actionOwner = null;
        if (qrOwner === owner) {
            qrOwner = null;
            qrInput = ({});
            if (qrScheduled) { qrScheduled = false; qrBusy = false; }
            else qrQuery.running = false;
        }
    }
    Component.onCompleted: model.refresh("summary")
    Timer { interval: 10000; running: true; repeat: true; onTriggered: service.model.refresh("summary") }
    Timer { interval: 2000; running: service.detailObservers > 0; repeat: true; onTriggered: service.refresh() }
    Timer { interval: 15000; running: service.latencyObservers > 0; repeat: true; onTriggered: service.model.refresh("latency") }
    Process {
        id: summaryQuery
        command: ["python3", service.helper, "icon"]
        stdout: StdioCollector { id: summaryOutput }
        onExited: function(code) { service.model.finish("summary", summaryOutput.text, code); }
    }
    Process {
        id: detailsQuery
        command: ["python3", service.helper, "status"]
        stdout: StdioCollector { id: detailsOutput }
        onExited: function(code) {
            service.model.finish("details", detailsOutput.text, code);
            if (service.latency.status === "loading" && !service.model.topics.latency.running) service.model.refresh("latency");
        }
    }
    Process {
        id: pingQuery
        stdout: StdioCollector { id: pingOutput }
        onExited: function(code) { service.model.finish("latency", pingOutput.text, code); }
    }
    Process {
        id: operation
        stdinEnabled: true
        onStarted: { write(JSON.stringify(service.actionInput) + "\n"); service.actionInput = ({}); }
        stdout: StdioCollector { id: operationOutput }
        onExited: function(code) {
            let message = "Could not complete request";
            try { const result = JSON.parse(operationOutput.text); message = result.error || (code === 0 ? "" : message); } catch (error) {}
            service.busy = false;
            if (service.actionOwner) service.actionOwner.networkActionFinished(message);
            service.actionOwner = null;
            service.actionInput = ({});
            service.refresh();
            service.model.refresh("summary");
        }
    }
    Process {
        id: qrQuery
        command: ["python3", service.qrHelper]
        stdinEnabled: true
        onStarted: { write(JSON.stringify(service.qrInput) + "\n"); service.qrInput = ({}); }
        stdout: StdioCollector { id: qrOutput }
        onExited: function(code) {
            let result = {error: "Could not generate QR code"};
            try { if (code === 0) result = JSON.parse(qrOutput.text); } catch (error) {}
            service.qrBusy = false;
            if (service.qrOwner) service.qrOwner.networkQrFinished(result);
            service.qrOwner = null;
            service.qrInput = ({});
        }
    }
}
