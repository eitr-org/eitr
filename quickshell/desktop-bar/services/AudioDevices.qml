pragma Singleton
import ".."
import QtQuick
import Eitr as Eitr
import Quickshell.Io
import "../AudioNames.js" as AudioNames

// Display names for audio devices: the user's own name when they renamed one,
// otherwise AudioNames' cleaned-up PipeWire description. Renames are machine-local
// (eitr/audio-names.json, keyed by the stable PipeWire node name).
QtObject {
    id: devices
    property var renamed: ({})

    function label(node) {
        if (!node) return "";
        return renamed[node.name] || AudioNames.friendlyName(node.description, node.nickname) || node.name;
    }
    function glyph(node, microphone) {
        return node ? AudioNames.glyph(node.properties, node.description, microphone) : "";
    }
    function rename(node, text) {
        if (!node) return;
        let next = Object.assign({}, renamed);
        const value = String(text || "").trim();
        if (value && value !== AudioNames.friendlyName(node.description, node.nickname)) next[node.name] = value;
        else delete next[node.name];
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
