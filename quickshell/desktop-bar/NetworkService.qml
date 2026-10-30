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
    readonly property bool busy: DesktopData.networkDomain.busy
    readonly property string actionKind: DesktopData.networkDomain.name
    property bool qrBusy: false
    property string qrHelper: Quickshell.shellDir + "/scripts/wifi-qr.py"
    property var actionOwner: null
    property string actionId: ""
    property var qrOwner: null
    property var qrInput: ({})
    property bool qrScheduled: false
    property var observers: ({})
    property string summaryToken: ""

    function actionMessage(source) {
        switch (source) {
        case "Both network backends are running; select one in Settings > Connectivity > Network Backend and reboot": return Eitr.I18n.tr("Both network backends are running; select one in Settings > Connectivity > Network Backend and reboot");
        case "No WiFi backend is running": return Eitr.I18n.tr("No WiFi backend is running");
        case "Install the Eitr network helper first; see distro/NETWORKING.md": return Eitr.I18n.tr("Install the Eitr network helper first; see distro/NETWORKING.md");
        case "CA certificate is too large": return Eitr.I18n.tr("CA certificate is too large");
        case "Enter the WiFi password": return Eitr.I18n.tr("Enter the WiFi password");
        case "Supported enterprise methods: PEAP/MSCHAPv2 and TTLS/PAP": return Eitr.I18n.tr("Supported enterprise methods: PEAP/MSCHAPv2 and TTLS/PAP");
        case "Enterprise WiFi requires username, password, CA certificate and server domain": return Eitr.I18n.tr("Enterprise WiFi requires username, password, CA certificate and server domain");
        case "CA certificate file not found": return Eitr.I18n.tr("CA certificate file not found");
        case "Enter the authentication server domain without wildcards": return Eitr.I18n.tr("Enter the authentication server domain without wildcards");
        case "This WiFi security type requires advanced network configuration": return Eitr.I18n.tr("This WiFi security type requires advanced network configuration");
        case "WiFi adapter is unavailable; refresh the panel": return Eitr.I18n.tr("WiFi adapter is unavailable; refresh the panel");
        case "Connection failed; verify credentials and certificate settings": return Eitr.I18n.tr("Connection failed; verify credentials and certificate settings");
        case "Connection timed out; check the WiFi panel": return Eitr.I18n.tr("Connection timed out; check the WiFi panel");
        case "Radios were blocked elsewhere; enable them individually in WiFi/Bluetooth.": return Eitr.I18n.tr("Radios were blocked elsewhere; enable them individually in WiFi/Bluetooth.");
        case "Could not complete request": return Eitr.I18n.tr("Could not complete request");
        case "Outcome unknown; refresh before retrying.": return Eitr.I18n.tr("Outcome unknown; refresh before retrying.");
        default: return Eitr.I18n.tr(source);
        }
    }
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
        actionOwner = owner;
        const id = DesktopData.client.act(kind, {path: path, extra: extra, input: input || ({})}, function(code, message) {
            const target = service.actionOwner;
            service.actionOwner = null;
            service.actionId = "";
            if (target) target.networkActionFinished(code === "outcome-unknown" ? "Outcome unknown; refresh before retrying." : (message || (code ? "Could not complete request" : "")), code);
        });
        if (!id) {
            actionOwner = null;
            owner.networkActionFinished("Could not complete request", "broker-unavailable");
            return false;
        }
        actionId = id;
        owner.networkActionFinished("");
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
        if (actionOwner === owner) { DesktopData.client.detachAction(actionId); actionOwner = null; actionId = ""; }
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
