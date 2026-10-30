import QtQuick
import "JsonState.js" as JsonState
import Quickshell
import Quickshell.Io

Item {
    id: service
    property bool observing: false
    property bool refreshPending: false
    property var state: ({})
    readonly property bool allowed: state.allowed === true
    readonly property bool busy: query.running
    function refresh() {
        if (query.running) refreshPending = true;
        else query.running = true;
    }
    Component.onCompleted: refresh()
    PreferenceWatch { path: "/etc/eitr/policies.json"; onChanged: service.refresh() }
    onObservingChanged: if (observing) refresh()
    Timer { interval: 10000; repeat: true; running: service.observing; onTriggered: service.refresh() }
    Process {
        id: query
        command: ["python3", Quickshell.shellDir + "/scripts/remote-status.py", service.observing ? "status" : "availability"]
        stdout: StdioCollector { id: result }
        onExited: function(code) {
            let next = ({});
            try { next = code === 0 ? JSON.parse(result.text) : ({}); } catch (error) {}
            if (JsonState.changed(service.state, next)) service.state = next;
            if (service.refreshPending) { service.refreshPending = false; Qt.callLater(service.refresh); }
        }
    }
}
