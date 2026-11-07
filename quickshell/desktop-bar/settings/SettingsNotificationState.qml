import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../JsonState.js" as JsonState

Item {
    id: state
    property bool active: false
    property bool live: true
    property bool enabled: true
    property string error: ""
    readonly property alias operation: write
    readonly property string script: Eitr.Paths.code("walker/scripts/actions/system/crash-help.py")
    function refresh() { if (live && active && !query.running && !write.running) query.running = true; }
    onActiveChanged: refresh()
    Process {
        id: query
        command: ["python3", state.script, "summary"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            const result = JsonState.parse(output.text, code, {enabled: "boolean"});
            state.error = result.ok ? "" : result.error;
            if (result.ok) state.enabled = result.data.enabled;
        }
    }
    Process {
        id: write
        command: ["python3", state.script, "toggle"]
        onExited: function(code) { state.error = code ? Eitr.I18n.tr("Could not change crash notifications") : ""; state.refresh(); }
    }
}
