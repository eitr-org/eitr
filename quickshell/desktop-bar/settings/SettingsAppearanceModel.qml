import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../JsonState.js" as JsonState

Item {
    id: model
    signal loaded()
    signal applied()
    readonly property bool loading: loader.running
    property bool opened: false
    property string mode: "wallpaper"
    property var targetScreen: null
    // IPC opens on the bar's primary screen; desktop double-clicks use their own screen.
    property var defaultScreen: null
    property var items: []
    property var allItems: []
    property var catalogs: ({})
    property string searchText: ""
    readonly property bool searchable: mode.startsWith("theme")
    property int selectedIndex: 0
    property color accent: "#cdd6f4"
    property color foreground: "#ffffff"
    property color background: "#202024"
    property string error: ""
    property bool contextReady: false
    // Settings: a thumbnail was clicked and its preview waits for Apply or Cancel.
    property bool previewing: false
    property string preferredPath: ""
    property string scope: "global"
    property string monitorName: ""
    property int workspaceNumber: 0
    property var assignments: []
    property string previewOwner: Date.now().toString() + "-" + Math.random().toString(36).slice(2)
    property var pendingCommands: []
    readonly property bool busy: wallpaperCommand.running || pendingCommands.length > 0
    signal catalogRequested(string tone)

    function wallpaperAction(action, extra) {
        const command = ["python3", Eitr.Paths.code("walker/scripts/actions/wallpaper/assignments.py"), action,
            "--scope", scope, "--monitor", monitorName, "--number", workspaceNumber.toString(), "--owner", previewOwner].concat(extra || []);
        // A single queue preserves preview/apply/cancel ordering across rapid clicks.
        if (action === "preview") pendingCommands = pendingCommands.filter(entry => entry.action !== "preview");
        pendingCommands = pendingCommands.concat([{action: action, command: command}]);
        pumpCommands();
    }
    function pumpCommands() {
        if (wallpaperCommand.running || !pendingCommands.length) return;
        const next = pendingCommands[0];
        pendingCommands = pendingCommands.slice(1);
        wallpaperCommand.action = next.action;
        wallpaperCommand.command = next.command;
        wallpaperCommand.running = true;
    }
    function previewSelection() {
        if (opened && contextReady && !loader.running && mode === "wallpaper" && items[selectedIndex])
            wallpaperAction("preview", ["--path", items[selectedIndex].value]);
    }
    function cancelPreview() { if (mode === "wallpaper") wallpaperAction("cancel"); }
    onSelectedIndexChanged: previewSelection()
    onScopeChanged: { cancelPreview(); previewSelection(); }
    onOpenedChanged: if (!opened) { previewing = false; cancelPreview(); }
    Component.onDestruction: {
        if (mode === "wallpaper") Quickshell.execDetached(["python3", Eitr.Paths.code("walker/scripts/actions/wallpaper/assignments.py"), "cancel", "--owner", previewOwner]);
    }

    function open(kind, screen) {
        if (loader.running)
            return;
        if (opened) cancelPreview();
        mode = kind;
        contextReady = kind !== "wallpaper";
        targetScreen = screen;
        const cached = catalogs[mode] || [];
        if (JsonState.changed(items, cached)) items = cached;
        if (JsonState.changed(allItems, cached)) allItems = cached;
        searchText = "";
        error = "";
        opened = true;
        if (mode === "wallpaper") wallpaperAction("summary", ["--monitor", screen ? screen.name : ""]);
        loader.command = ["python3", Quickshell.shellDir + "/scripts/appearance-items.py", mode];
        loader.running = true;
    }

    function navigate(delta) {
        if (items.length)
            selectedIndex = (selectedIndex + delta + items.length) % items.length;
    }

    function search(value) {
        searchText = value;
        var query = value.trim().toLocaleLowerCase();
        items = allItems.filter(function(item) {
            return item.name.toLocaleLowerCase().indexOf(query) !== -1;
        });
        selectedIndex = 0;
    }

    function apply() {
        if (!items.length || applyProcess.running)
            return;
        if (mode === "wallpaper") {
            if (!contextReady) return;
            wallpaperAction("apply", ["--path", items[selectedIndex].value]);
            opened = false;
            return;
        }
        var script = mode.startsWith("theme") ? "style/apply.sh" : "wallpaper/apply.sh";
        applyProcess.command = [Eitr.Paths.code("walker/scripts/actions/") + script, items[selectedIndex].value];
        opened = false;
        applyProcess.running = true;
    }

    // All themes by default; a Sun or Moon click shows only that mode, a second click all again.
    function filterThemes(target) {
        if (!loader.running && searchable)
            open(mode === target ? "theme" : target, targetScreen);
    }

    Process {
        id: loader
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            const result = JsonState.parse(output.text, code, {mode: "string", items: [{name: "string", value: "string", image: "string", current: "boolean"}], accent: "string", foreground: "string", background: "string"});
            const data = result.data;
            if (result.ok) {
                model.mode = data.mode;
                if (JsonState.changed(model.items, data.items)) model.items = data.items;
                if (JsonState.changed(model.allItems, data.items)) model.allItems = data.items;
                model.catalogs[model.mode] = data.items;
                model.accent = data.accent;
                model.foreground = data.foreground;
                model.background = data.background;
                model.selectedIndex = 0;
                for (var index = 0; index < data.items.length; index++) {
                    if (preferredPath ? data.items[index].value === preferredPath : data.items[index].current)
                        model.selectedIndex = index;
                }
                model.preferredPath = "";
                if (model.searchText) model.search(model.searchText);
                model.error = data.items.length ? "" : Eitr.I18n.tr("No images found");
            } else {
                model.items = [];
                model.allItems = [];
                model.catalogs[model.mode] = [];
                model.error = Eitr.I18n.tr("Images unavailable");
            }
            model.loaded();
            Qt.callLater(model.previewSelection);
        }
    }

    Process {
        id: wallpaperCommand
        property string action: ""
        stdout: StdioCollector { id: wallpaperOutput }
        stderr: StdioCollector { id: wallpaperErrors }
        onExited: function(code) {
            if (code) model.error = wallpaperErrors.text.trim();
            else {
                try {
                    const result = JSON.parse(wallpaperOutput.text);
                    if (action === "summary") {
                        model.monitorName = result.monitor;
                        model.workspaceNumber = result.number;
                        model.contextReady = true;
                        Qt.callLater(model.previewSelection);
                    }
                    model.assignments = result.assignments;
                } catch (error) { model.error = Eitr.I18n.tr("Images unavailable"); }
                if (action === "apply" || action === "clear") model.applied();
            }
            Qt.callLater(model.pumpCommands);
        }
    }

    Process {
        id: applyProcess
        stderr: StdioCollector { id: errors }
        onExited: function(code) {
            model.error = code ? errors.text.trim() : "";
            if (!code) model.applied();
        }
    }

}
