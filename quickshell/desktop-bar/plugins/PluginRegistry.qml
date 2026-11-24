pragma Singleton
import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../JsonState.js" as JsonState

QtObject {
    id: registry
    property var palette: ({})
    function widgetSurface(entry) {
        return entry.geometry && entry.geometry.surface || entry.surface || "none";
    }
    property var entries: []
    property var installed: []
    property bool snapshotLoaded: false
    readonly property bool refreshing: query.running || pending
    readonly property string installedRevision: snapshotLoaded ? JSON.stringify(installed.map(plugin =>
        JSON.stringify([plugin.id, plugin.commit])).sort()) : ""
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
        // Quickshell's plain-text copy of this instance's log, read from its start and
        // until the bar exits. `quickshell log --follow` aborts on its own at times.
        command: ["tail", "-n", "+1", "-F", "--pid=" + Quickshell.processId,
            Quickshell.env("XDG_RUNTIME_DIR") + "/quickshell/by-pid/" + Quickshell.processId + "/log.log"]
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
    // Each placed copy of a widget is named by its plugin, widget id and instance.
    signal widgetAction(string plugin, string id, string instance, string action, bool custom)
    function widgetKey(placement) { return placement.plugin + "/" + placement.id + "/" + placement.instance; }
    function setMenu(placement, entries) {
        const next = Object.assign({}, widgetMenus);
        next[widgetKey(placement)] = entries;
        widgetMenus = next;
    }
    property string clockFormat: "12h"
    property var placements: ({version: 3, widgets: [], barItems: []})
    function copies(entry) {
        return (placements.widgets || []).filter(placement => placement.plugin === entry.plugin && placement.id === entry.id);
    }
    property bool editing: false
    // {plugin, id, instance} of the copy being edited, or null to edit every widget.
    property var editTarget: null
    // The widget copy whose right-click menu is open: {plugin, id, instance, monitor, x, y},
    // with x and y in that display's coordinates. PluginWidgetMenuHost draws it.
    property var menuTarget: null
    function openWidgetMenu(placement, x, y) {
        menuTarget = {plugin: placement.plugin, id: placement.id, instance: placement.instance, monitor: placement.monitor, x: x, y: y};
    }
    function closeWidgetMenu() { menuTarget = null; }
    onReviewStarted: closeWidgetMenu()
    function editingCopy(placement) {
        return editing && editTarget !== null && editTarget.plugin === placement.plugin
            && editTarget.id === placement.id && editTarget.instance === placement.instance;
    }
    function editCopy(placement, start) {
        editTarget = {plugin: placement.plugin, id: placement.id, instance: placement.instance};
        editing = start;
    }
    // Angles shown while the rotation slider is dragged, before the saved file catches up.
    property var rotationDrafts: ({})
    function previewRotation(placement, degrees) {
        const next = Object.assign({}, rotationDrafts);
        next[widgetKey(placement)] = degrees;
        rotationDrafts = next;
    }
    function rotation(placement) {
        const draft = rotationDrafts[widgetKey(placement)];
        return draft !== undefined ? draft : placement.rotation || 0;
    }
    property bool pending: false
    readonly property string helper: Eitr.Paths.code("walker/scripts/actions/install/plugins.py")
    readonly property string stateRoot: Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state"
    readonly property string configRoot: Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config"
    readonly property var placedBarItems: placed("barItems", "")
    function slotItems(slot) {
        return placedBarItems.filter(entry => (entry.slot || "status") === slot).slice(0, slot === "status" ? 8 : slot === "start" ? 4 : 2);
    }
    readonly property var clockBarItems: slotItems("clock")
    readonly property var barItems: slotItems("status")
    function barItemShown(plugin, itemId) {
        const barEntries = entries.filter(entry => entry.plugin === plugin && entry.kind === "barItems" && (!itemId || entry.id === itemId));
        if (!barEntries.length) return true;
        return barEntries.some(entry => !entry.disabled && (placements.barItems || []).some(placement => placement.plugin === plugin && placement.id === entry.id));
    }
    readonly property bool weatherEnabled: entries.some(entry => entry.plugin === "weather" && !entry.disabled && (entry.capabilities || []).includes("weather")) && barItemShown("weather")
    readonly property bool aiUsageEnabled: entries.some(entry => entry.bundled && entry.plugin === "ai-usage" && entry.kind === "panels" && entry.id === "limits" && !entry.disabled) && barItemShown("ai-usage")
    readonly property bool hardwareEnabled: entries.some(entry => entry.bundled && entry.plugin === "hardware" && entry.kind === "panels" && !entry.disabled) && barItemShown("hardware")
    function placed(kind, monitor) {
        return (placements[kind] || []).filter(placement => kind !== "widgets" || placement.monitor === monitor)
            .map(placement => {
                const entry = entries.find(entry => entry.plugin === placement.plugin && entry.id === placement.id && entry.kind === kind);
                return entry && !entry.disabled ? Object.assign({}, entry, {geometry: placement, slot: placement.slot || entry.slot || "status"}) : null;
            }).filter(entry => entry !== null);
    }
    function refreshEntries() {
        if (query.running) pending = true;
        else query.running = true;
    }
    function refreshPlacements() { refreshEntries(); }
    function refresh() { refreshEntries(); }
    // options: {instance, monitor, isNew, geometry, surface, rotation}, each optional.
    function change(action, entry, options) {
        const settings = options || {};
        let args = ["python3", helper, action, entry.plugin, entry.id];
        if (settings.instance) args = args.concat(["--instance", settings.instance]);
        if (settings.monitor) args = args.concat(["--monitor", settings.monitor]);
        if (settings.isNew) args.push("--new");
        if (settings.geometry) args = args.concat(["--geometry", JSON.stringify(settings.geometry)]);
        if (settings.slot) args = args.concat(["--slot", settings.slot]);
        if (settings.surface) args = args.concat(["--surface", settings.surface]);
        if (settings.rotation !== undefined) args = args.concat(["--rotation", String(settings.rotation)]);
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
    function refreshInstalled() { refreshEntries(); }
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
        command: ["python3", registry.helper, "snapshot"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            const result = JsonState.parse(output.text, code, {entries: "array", installed: "array", placements: "object"});
            if (result.ok) {
                const next = result.data;
                if (JsonState.changed(registry.entries, next.entries)) registry.entries = next.entries;
                if (JsonState.changed(registry.installed, next.installed)) registry.installed = next.installed;
                if (JsonState.changed(registry.placements, next.placements)) registry.placements = next.placements;
                registry.snapshotLoaded = true;
                registry.rotationDrafts = ({});
            } else registry.entries = [];
            if (registry.pending) { registry.pending = false; Qt.callLater(registry.refreshEntries); }
        }
    }
    property IpcHandler ipc: IpcHandler {
        target: "plugin-widgets"
        function edit(): void { registry.editTarget = null; registry.editing = !registry.editing; }
        function done(): void { registry.editing = false; }
    }
}
