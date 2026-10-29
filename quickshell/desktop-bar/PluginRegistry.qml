pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "JsonState.js" as JsonState

QtObject {
    id: registry
    property var palette: ({})
    function widgetSurface(entry) {
        return entry.geometry && entry.geometry.surface || entry.surface || "none";
    }
    property var entries: []
    property var installed: []
    // Session diagnostics only: never persist arbitrary plugin messages.
    property var errors: []
    property var diagnosticRoots: ({})
    function registerSource(entry) {
        if (!entry.source || !entry.qml) return;
        let folder = String(entry.source);
        for (let depth = entry.qml.split("/").length; depth > 0; depth--) folder = folder.slice(0, folder.lastIndexOf("/"));
        const next = Object.assign({}, diagnosticRoots);
        next[entry.plugin] = decodedUrl(folder + "/");
        diagnosticRoots = next;
    }
    function decodedUrl(url) {
        try { return decodeURIComponent(url); } catch (error) { return url; }
    }
    onEntriesChanged: entries.forEach(entry => registerSource(entry))
    function pluginErrors(plugin) { return errors.filter(error => error.plugin === plugin); }
    function recordError(plugin, file, line, message) {
        message = String(message).slice(0, 2048);
        file = String(file).slice(0, 4096);
        if (errors.some(error => error.plugin === plugin && error.file === file && error.line === line && error.message === message)) return;
        let next = errors.slice();
        if (pluginErrors(plugin).length >= 50) {
            const oldest = next.findIndex(error => error.plugin === plugin);
            next.splice(oldest, 1);
        }
        next.push({plugin: plugin, file: file, line: line, message: message, time: new Date().toISOString()});
        errors = next.slice(-200);
    }
    function diagnostic(line) {
        // Accept Qt URL:line:column and Quickshell URL[line:column] locations.
        if (!/\b(?:WARN|ERROR)\b/.test(line)) return;
        const match = /(?:^|\s)(file:\/\/\/.+?)(?::(-?\d+)(?::[-\d]+)?|\[(-?\d+):[-\d]+\])?:\s*(.*)/.exec(line);
        if (!match) return;
        for (const plugin of Object.keys(diagnosticRoots)) {
            if (decodedUrl(match[1]).startsWith(diagnosticRoots[plugin])) {
                recordError(plugin, match[1], Math.max(0, Number(match[2] || match[3] || 0)), match[4]);
                return;
            }
        }
    }
    function errorDetails(plugin) {
        return pluginErrors(plugin).map(error => error.time + " · " + error.plugin + "\n"
            + error.file + ":" + error.line + "\n" + error.message).join("\n\n");
    }
    property bool diagnosticStopping: false
    property int diagnosticRetryDelay: 500
    property int diagnosticExitCode: 0
    property string diagnosticLogError: ""
    function startDiagnostics() {
        if (!diagnosticStopping && !diagnosticLog.running && !diagnosticRetry.running)
            diagnosticRetry.start();
    }
    function retryDiagnostics() {
        if (diagnosticStopping || diagnosticRetry.running) return;
        diagnosticRetry.interval = diagnosticRetryDelay;
        diagnosticRetryDelay = Math.min(30000, diagnosticRetryDelay * 2);
        diagnosticRetry.start();
    }
    property Timer diagnosticRetry: Timer {
        interval: 500
        onTriggered: if (!registry.diagnosticStopping && !registry.diagnosticLog.running)
            registry.diagnosticLog.running = true
    }
    property Timer diagnosticStable: Timer {
        interval: 10000
        running: registry.diagnosticLog.running
        onTriggered: registry.diagnosticRetryDelay = 500
    }
    property Process diagnosticLog: Process {
        command: ["quickshell", "log", "--follow", "--pid", String(Quickshell.processId), "--no-color"]
        stdout: SplitParser { onRead: line => registry.diagnostic(line) }
        stderr: SplitParser { onRead: line => registry.diagnosticLogError = line.slice(0, 1024) }
        onStarted: registry.diagnosticLogError = ""
        onExited: function(code) { registry.diagnosticExitCode = code; }
        // FailedToStart emits runningChanged but no exited signal in Quickshell 0.3.2.
        onRunningChanged: if (!running) registry.retryDiagnostics()
    }
    Component.onDestruction: {
        diagnosticStopping = true;
        diagnosticRetry.stop();
        diagnosticStable.stop();
        diagnosticLog.running = false;
    }
    property var widgetMenus: ({})
    signal reviewStarted()
    signal widgetAction(string plugin, string id, string monitor, string action, bool custom)
    function menuKey(entry, monitor) { return entry.plugin + "/" + entry.id + "/" + monitor; }
    function setMenu(entry, monitor, entries) {
        const next = Object.assign({}, widgetMenus);
        next[menuKey(entry, monitor)] = entries;
        widgetMenus = next;
    }
    property var placements: ({version: 2, widgets: [], barItems: []})
    property bool editing: false
    property var editTarget: null
    property bool pending: false
    property bool installedPending: false
    property bool placementPending: false
    readonly property string helper: Eitr.Paths.code("walker/scripts/actions/install/plugins.py")
    readonly property string stateRoot: Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state"
    readonly property string configRoot: Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config"
    readonly property var barItems: placed("barItems", "")
    function placed(kind, monitor) {
        return (placements[kind] || []).filter(placement => kind !== "widgets" || placement.monitor === monitor)
            .map(placement => {
                const entry = entries.find(entry => entry.plugin === placement.plugin && entry.id === placement.id && entry.kind === kind);
                return entry && !entry.disabled ? Object.assign({}, entry, {geometry: placement}) : null;
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
    function refresh() { refreshEntries(); refreshPlacements(); if (installedQuery.running) installedPending = true; else installedQuery.running = true; }
    function change(action, entry, monitor, geometry, surface) {
        let args = ["python3", helper, action, entry.plugin, entry.id];
        if (monitor) args = args.concat(["--monitor", monitor]);
        if (geometry) args = args.concat(["--geometry", JSON.stringify(geometry)]);
        if (surface) args = args.concat(["--surface", surface]);
        Quickshell.execDetached(args);
    }
    function setEnabled(plugin, enabled) {
        Quickshell.execDetached(["python3", helper, enabled ? "enable" : "disable", plugin]);
    }
    function review(action, plugin) {
        editing = false;
        editTarget = null;
        reviewStarted();
        Quickshell.execDetached([Eitr.Paths.code("walker/bin/menu-path/kitty"), "--class", "eitr-plugins", "-e",
            "python3", Eitr.Paths.code("walker/scripts/actions/task-terminal.py"), "python3", helper, action].concat(plugin ? [plugin] : []));
    }
    function refreshInstalled() { installedQuery.running = true; }
    property Process installedQuery: Process {
        command: ["python3", registry.helper, "installed"]
        stdout: StdioCollector { id: installedOutput }
        onExited: function(code) {
            if (code === 0) try {
                const next = JSON.parse(installedOutput.text);
                if (JsonState.changed(registry.installed, next)) registry.installed = next;
            } catch (error) { console.warn("Plugin manager:", error); }
            if (registry.installedPending) { registry.installedPending = false; Qt.callLater(registry.refreshInstalled); }
        }
    }
    Component.onCompleted: { refresh(); startDiagnostics(); }
    property FileView approvalWatch: FileView {
        path: registry.stateRoot + "/eitr/plugins.json"; watchChanges: true; printErrors: false
        onFileChanged: { registry.editing = false; registry.editTarget = null; reload(); registry.refresh(); }
    }
    property FileView updateWatch: FileView {
        path: registry.stateRoot + "/eitr/plugin-updates.json"; watchChanges: true; printErrors: false
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
        function edit(): void { registry.editTarget = null; registry.editing = !registry.editing; }
        function done(): void { registry.editing = false; }
    }
}
