import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: service
    property bool observing: false
    property var state: ({})
    readonly property bool allowed: state.allowed === true
    readonly property bool busy: query.running
    function refresh() {
        if (!query.running) query.running = true;
    }
    onObservingChanged: if (observing) refresh()
    Timer { interval: 10000; repeat: true; running: service.observing; onTriggered: service.refresh() }
    Process {
        id: query
        command: ["python3", Quickshell.shellDir + "/scripts/remote-status.py"]
        stdout: StdioCollector { id: result }
        onExited: function(code) {
            try { service.state = code === 0 ? JSON.parse(result.text) : ({}); }
            catch (error) { service.state = ({}); }
        }
    }
}
