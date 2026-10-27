pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "JsonState.js" as JsonState

QtObject {
    id: registry
    property var entries: []
    property var placements: ({version: 2, widgets: [], barItems: []})
    property bool editing: false
    property var editTarget: null
    property bool pending: false
    property bool placementPending: false
    readonly property string helper: Eitr.Paths.code("walker/scripts/actions/install/plugins.py")
    readonly property string stateRoot: Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state"
    readonly property string configRoot: Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config"
    readonly property var barItems: placed("barItems", "")
    function placed(kind, monitor) {
        return (placements[kind] || []).filter(placement => kind !== "widgets" || placement.monitor === monitor)
            .map(placement => {
                const entry = entries.find(entry => entry.plugin === placement.plugin && entry.id === placement.id && entry.kind === kind);
                return entry ? Object.assign({}, entry, {geometry: placement}) : null;
            }).filter(entry => entry !== null);
    }
    function refreshEntries() {
        if (query.running) pending = true;
        else query.running = true;
    }
    function refreshPlacements() {
        if (placementQuery.running) placementPending = true;
        else placementQuery.running = true;
    }
    function refresh() { refreshEntries(); refreshPlacements(); }
    function change(action, entry, monitor, geometry) {
        let args = ["python3", helper, action, entry.plugin, entry.id];
        if (monitor) args = args.concat(["--monitor", monitor]);
        if (geometry) args = args.concat(["--geometry", JSON.stringify(geometry)]);
        Quickshell.execDetached(args);
    }
    Component.onCompleted: refresh()
    property FileView approvalWatch: FileView {
        path: registry.stateRoot + "/eitr/plugins.json"; watchChanges: true; printErrors: false
        onFileChanged: { reload(); registry.refresh(); }
    }
    property FileView failureWatch: FileView {
        path: registry.stateRoot + "/eitr/plugin-ui.json"; watchChanges: true; printErrors: false
        onFileChanged: { reload(); registry.refresh(); }
    }
    property FileView placementWatch: FileView {
        path: registry.configRoot + "/eitr/plugin-placements.json"; watchChanges: true; printErrors: false
        onFileChanged: { reload(); registry.refresh(); }
    }
    property Process query: Process {
        command: ["python3", registry.helper, "ui"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            if (code !== 0) registry.entries = [];
            else try {
                const next = JSON.parse(output.text);
                if (JsonState.changed(registry.entries, next)) registry.entries = next;
            } catch (error) { registry.entries = []; }
            if (registry.pending) { registry.pending = false; Qt.callLater(registry.refreshEntries); }
        }
    }
    property Process placementQuery: Process {
        command: ["python3", registry.helper, "placements"]
        stdout: StdioCollector { id: placementOutput }
        onExited: function(code) {
            if (registry.placementPending) { registry.placementPending = false; Qt.callLater(registry.refreshPlacements); }
            if (code === 0) try {
                const next = JSON.parse(placementOutput.text);
                if (JsonState.changed(registry.placements, next)) registry.placements = next;
            } catch (error) { console.warn("Plugin placements:", error); }
        }
    }
    property IpcHandler ipc: IpcHandler {
        target: "plugin-widgets"
        function edit(): void { registry.editTarget = null; registry.editing = true; }
        function done(): void { registry.editing = false; }
    }
}
