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
    signal catalogRequested(string tone)

    function open(kind, screen) {
        if (loader.running)
            return;
        mode = kind;
        targetScreen = screen;
        const cached = catalogs[mode] || [];
        if (JsonState.changed(items, cached)) items = cached;
        if (JsonState.changed(allItems, cached)) allItems = cached;
        searchText = "";
        error = "";
        opened = true;
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
                    if (data.items[index].current)
                        model.selectedIndex = index;
                }
                if (model.searchText) model.search(model.searchText);
                model.error = data.items.length ? "" : Eitr.I18n.tr("No images found");
            } else {
                model.items = [];
                model.allItems = [];
                model.catalogs[model.mode] = [];
                model.error = Eitr.I18n.tr("Images unavailable");
            }
            model.loaded();
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
