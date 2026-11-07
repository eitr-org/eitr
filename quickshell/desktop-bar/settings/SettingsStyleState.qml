import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../JsonState.js" as JsonState

Item {
    id: state
    property bool active: false
    property bool live: true
    property string actionError: ""
    property var contentUpdater: null
    function updateContent(action) { if (contentUpdater) contentUpdater(action); else action(); }
    function run(process, command) {
        if (!live || process.running) return;
        actionError = "";
        process.command = command;
        process.running = true;
    }
    function loadStyle() {
        if (!live || !active) return;
        if (!cursorQuery.running) cursorQuery.running = true;
        if (!lockscreenQuery.running) lockscreenQuery.running = true;
        if (!terminalQuery.running) terminalQuery.running = true;
        if (!fireQuery.running) fireQuery.running = true;
    }
    onActiveChanged: if (active) loadStyle()
    readonly property var cursorWriteRef: cursorWrite
    readonly property var lockscreenWriteRef: lockscreenWrite
    readonly property var fireWriteRef: fireWrite
    readonly property var terminalWriteRef: terminalWrite
    property var styleErrors: ({})
    function styleResult(key, text, code, fields) {
        const result = JsonState.parse(text, code, fields);
        let errors = Object.assign({}, styleErrors);
        if (result.ok) delete errors[key];
        else errors[key] = result.error;
        styleErrors = errors;
        return result.data;
    }
    property string cursorPreview: ""
    property var cursorChoices: ({family: [], size: [], color: []})
    property var lockscreens: []
    property string lockscreen: ""
    property string terminalChoice: "kitty"
    property var terminalChoices: []
    property var terminalAppearance: ({})
    property var terminalAppearanceChoices: ({})
    readonly property string terminalScript: Eitr.Paths.code("walker/scripts/actions/style/terminal.py")
    property bool cursorFire: false
    property string updateChannel: ""
    property var organizationPolicy: ({})
    readonly property string cursorScript: Eitr.Paths.code("walker/scripts/actions/style/cursor.py")
    readonly property string lockscreenScript: Eitr.Paths.code("quickshell/lockscreen/scripts/settings.py")
    readonly property string effectsScript: Eitr.Paths.code("walker/scripts/actions/style/terminal-effects.py")
    Process {
        id: cursorQuery
        command: ["python3", state.cursorScript, "summary"]
        stdout: StdioCollector { id: cursorOutput }
        onExited: function(code) {
            const data = state.styleResult("cursor", cursorOutput.text, code, {choices: {family: [{id: "string", label: "string", selected: "boolean"}], size: [{id: "string", label: "string", selected: "boolean"}], color: [{id: "string", label: "string", selected: "boolean"}]}, current: "object", available: "boolean"});
            state.updateContent(function() {
                state.cursorPreview = data ? data.preview || "" : "";
                const choices = data ? data.choices : {family: [], size: [], color: []};
                if (JsonState.changed(state.cursorChoices, choices)) state.cursorChoices = choices;
            });
        }
    }
    Process { id: cursorWrite; onExited: function(code) { if (code !== 0) state.actionError = Eitr.I18n.tr("Could not change the cursor"); cursorQuery.running = true; } }
    Process {
        id: lockscreenQuery
        command: ["python3", state.lockscreenScript, "summary"]
        stdout: StdioCollector { id: lockscreenOutput }
        onExited: function(code) {
            const data = state.styleResult("lockscreen", lockscreenOutput.text, code, {choices: [{value: "string", label: "string"}], current: "string", available: "boolean"});
            state.updateContent(function() {
                const choices = data ? data.choices : [];
                if (JsonState.changed(state.lockscreens, choices)) state.lockscreens = choices;
                state.lockscreen = data ? data.current : "";
            });
        }
    }
    Process {
        id: lockscreenWrite
        stderr: StdioCollector { id: lockscreenError }
        onExited: function(code) { if (code !== 0) state.actionError = lockscreenError.text.trim() || Eitr.I18n.tr("Could not change the lockscreen"); lockscreenQuery.running = true; }
    }
    Process {
        id: fireQuery
        command: ["python3", state.effectsScript, "summary"]
        stdout: StdioCollector { id: fireOutput }
        onExited: function(code) {
            const data = state.styleResult("effects", fireOutput.text, code, {current: "boolean", choices: "array", available: "boolean"});
            state.cursorFire = data ? data.current : false;
        }
    }
    Process {
        id: terminalQuery
        command: ["python3", state.terminalScript, "summary"]
        stdout: StdioCollector { id: terminalOutput }
        onExited: function(code) {
            const data = state.styleResult("terminal", terminalOutput.text, code, {current: "string", choices: [{value: "string", label: "string"}], appearance: "object", appearanceChoices: "object", available: "boolean"});
            state.updateContent(function() {
                const choices = data ? data.choices : [];
                if (JsonState.changed(state.terminalChoices, choices)) state.terminalChoices = choices;
                state.terminalChoice = data ? data.current : "";
                const appearance = data ? data.appearance : {};
                if (JsonState.changed(state.terminalAppearance, appearance)) state.terminalAppearance = appearance;
                const appearanceChoices = data ? data.appearanceChoices : {};
                if (JsonState.changed(state.terminalAppearanceChoices, appearanceChoices)) state.terminalAppearanceChoices = appearanceChoices;
            });
        }
    }
    Process {
        id: terminalWrite
        stderr: StdioCollector { id: terminalError }
        onExited: function(code) {
            if (code !== 0) state.actionError = terminalError.text.trim();
            terminalQuery.running = true;
        }
    }
    Process { id: fireWrite; onExited: function(code) { if (code !== 0) state.actionError = Eitr.I18n.tr("Could not change Cursor Fire"); fireQuery.running = true; } }
}
