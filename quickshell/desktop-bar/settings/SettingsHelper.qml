import ".."
import QtQuick
import Quickshell.Io
import "../JsonState.js" as JsonState

Item {
    id: helper
    required property string script
    property var summaryArguments: []
    property bool active: false
    property bool live: true
    property var summary: ({current: "", choices: [], available: false})
    property string error: ""
    readonly property bool busy: write.running
    property var schema: ({current: "string", choices: "array", available: "boolean"})
    function refresh() { if (active && live && !read.running) read.running = true; }
    function change(arguments) {
        if (!live || busy) return;
        write.command = ["python3", script].concat(arguments);
        write.running = true;
    }
    onActiveChanged: { if (!active) read.running = false; else refresh(); }
    onSummaryArgumentsChanged: { read.running = false; if (active) Qt.callLater(refresh); }
    Timer {
        interval: 30000; running: read.running
        onTriggered: { read.running = false; helper.error = "Settings read timed out"; }
    }
    Process {
        id: read
        command: ["python3", helper.script, "summary"].concat(helper.summaryArguments)
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            const result = JsonState.parse(output.text, code, helper.schema);
            helper.error = result.ok ? "" : result.error;
            if (result.ok) helper.summary = result.data;
        }
    }
    Process {
        id: write
        stderr: StdioCollector { id: errors }
        onExited: function(code) { helper.error = code ? errors.text.trim() : ""; helper.refresh(); }
    }
}
