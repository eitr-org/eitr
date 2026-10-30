import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io
import "NetworkStatus.js" as NetworkStatus

Item {
    id: service
    property var summary: topicState("summary")
    property var details: topicState("details")
    property var latency: topicState("latency")
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
    property bool qrScheduled: false
    property var observers: ({})
    property string summaryToken: ""

    function topicState(topic) {
        const snapshot = DesktopData.topics["network." + topic] || {status: "loading", data: {}};
        return Object.assign({}, snapshot, {error: snapshot.error ? Eitr.I18n.tr("Could not load") : ""});
    }
    function observe(owner, topic) {
        topic = topic || "details";
        if (topic !== "details" && topic !== "latency") throw new Error("Unknown network topic");
        const token = DesktopData.observe("network." + topic, owner);
        observers[token] = {owner: owner, topic: topic};
        updateObservers();
        return token;
    }
    function release(token) {
        DesktopData.release(token);
        delete observers[token];
        updateObservers();
    }
    function updateObservers() {
        detailObservers = Object.keys(observers).filter(token => observers[token].topic === "details").length;
        latencyObservers = Object.keys(observers).filter(token => observers[token].topic === "latency").length;
    }
    function refresh() { DesktopData.refresh("network.details"); }
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
        Object.keys(observers).filter(token => observers[token].owner === owner).forEach(release);
        if (actionOwner === owner) actionOwner = null;
        if (qrOwner === owner) {
            qrOwner = null;
            qrInput = ({});
            if (qrScheduled) { qrScheduled = false; qrBusy = false; }
            else qrQuery.running = false;
        }
    }
    Component.onCompleted: summaryToken = DesktopData.observe("network.summary", service)
    Component.onDestruction: {
        Object.keys(observers).forEach(token => DesktopData.release(token));
        DesktopData.release(summaryToken);
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
            DesktopData.refresh("network.summary");
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
