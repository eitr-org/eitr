pragma Singleton
import ".."
import QtQuick
import Eitr as Eitr
import Quickshell.Io
import Quickshell.Services.Pipewire
import "../AudioNames.js" as AudioNames

// The audio devices to choose from: PipeWire's devices plus the ports a card offers on its
// other profiles (a second monitor on the graphics card, a jack beside the optical output),
// which the data broker's audio domain reads and switches to. Display names are the user's
// own when they renamed one, otherwise AudioNames' cleaned-up description. Renames are
// machine-local (eitr/audio-names.json), keyed by the monitor's name for monitor audio
// (a graphics card's ports can trade places) and by the PipeWire node name otherwise.
QtObject {
    id: devices
    property var renamed: ({})
    // Ports beyond the cards' current profiles, as the audio domain last read them.
    property var ports: []
    // A port being switched to: its device becomes the default once PipeWire has it.
    property var pending: null

    function monitorName(node) {
        const match = String(node && node.description || "").match(/\[([^\]]+)\]\s*$/);
        return match ? match[1].trim() : "";
    }
    function key(node) { return monitorName(node) ? "monitor:" + monitorName(node) : node.name; }
    function label(node) {
        if (!node) return "";
        return renamed[key(node)] || AudioNames.friendlyName(node.description, node.nickname) || node.name;
    }
    function glyph(node, microphone) {
        return node ? AudioNames.glyph(node.properties, node.description, microphone) : "";
    }
    function portKey(port) { return port.monitor ? "monitor:" + port.monitor : port.node; }
    function portName(port) { return port.monitor || AudioNames.friendlyName(port.device) + " (" + port.label + ")"; }

    // Dropdown choices: the devices PipeWire has, then the cards' other ports.
    function choices(nodes, microphone) {
        const live = nodes.map(node => ({value: String(node.id), label: label(node), glyph: glyph(node, microphone), key: key(node),
                                         fallback: AudioNames.friendlyName(node.description, node.nickname) || node.name}));
        const known = live.map(choice => choice.key);
        return live.concat(ports.filter(port => (port.direction === "input") === microphone && !known.includes(portKey(port)))
            .map(port => ({value: "port:" + port.card + "|" + port.profile, label: renamed[portKey(port)] || portName(port),
                           glyph: AudioNames.portGlyph(port.kind, microphone), key: portKey(port), fallback: portName(port)})));
    }
    function choose(value, nodes, microphone) {
        if (String(value).startsWith("port:")) {
            const port = ports.find(entry => "port:" + entry.card + "|" + entry.profile === value);
            if (!port) return;
            DesktopData.queryAudio("select", {card: port.card, profile: port.profile}, devices, (error, data) => {
                if (error) { readPorts(); return; }
                pending = {node: port.node, microphone: microphone, tries: 0};
                settle.restart();
            });
            return;
        }
        const node = nodes.find(entry => String(entry.id) === value);
        if (!node) return;
        if (microphone) Pipewire.preferredDefaultAudioSource = node;
        else Pipewire.preferredDefaultAudioSink = node;
    }
    property Timer settle: Timer {
        interval: 150; repeat: true
        onTriggered: {
            const wanted = devices.pending;
            const node = wanted ? Pipewire.nodes.values.find(entry => entry.name === wanted.node) : null;
            if (node) {
                if (wanted.microphone) Pipewire.preferredDefaultAudioSource = node;
                else Pipewire.preferredDefaultAudioSink = node;
            }
            if (node || !wanted || ++wanted.tries > 20) { devices.pending = null; stop(); devices.readPorts(); }
        }
    }
    // Read while a picker is on screen and whenever PipeWire's devices change meanwhile
    // (a card switching profile, a screen or jack connected); never on a timer.
    property int watchers: 0
    function watch(on) { watchers = Math.max(0, watchers + (on ? 1 : -1)); if (on) readPorts(); }
    property int deviceCount: Pipewire.nodes.values.length
    onDeviceCountChanged: if (watchers > 0) readSoon.restart()
    property Timer readSoon: Timer { interval: 300; onTriggered: devices.readPorts() }
    property string reading: ""
    function readPorts() {
        if (reading) return;
        reading = DesktopData.queryAudio("ports", {}, devices, (error, data) => {
            reading = "";
            if (!error && data && Array.isArray(data.ports)) ports = data.ports;
        }) || "";
    }

    function rename(choice, text) {
        if (!choice) return;
        let next = Object.assign({}, renamed);
        const value = String(text || "").trim();
        if (value && value !== choice.fallback) next[choice.key] = value;
        else delete next[choice.key];
        renamed = next;
        store.setText(JSON.stringify(next, null, 2) + "\n");
    }

    property FileView store: FileView {
        path: Eitr.Paths.config("eitr/audio-names.json")
        atomicWrites: true; printErrors: false
        onLoaded: {
            try {
                const data = JSON.parse(text());
                devices.renamed = data && typeof data === "object" && !Array.isArray(data) ? data : {};
            } catch (error) { devices.renamed = {}; }
        }
    }
}
