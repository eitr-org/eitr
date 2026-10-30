import QtQuick
import Quickshell.Io
import Quickshell.Hyprland
import "JsonState.js" as JsonState

Item {
    id: model
    property bool observing: true
    property var clients: []
    property bool refreshPending: false
    visible: false
    function refresh() {
        if (!observing) return;
        if (query.running) refreshPending = true;
        else query.running = true;
    }
    onObservingChanged: if (observing) refresh()
    Component.onCompleted: refresh()
    Process {
        id: query
        command: ["hyprctl", "-j", "clients"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            if (code === 0) try {
                var next = JSON.parse(output.text);
                if (Array.isArray(next) && JsonState.changed(model.clients, next)) model.clients = next;
            } catch (error) { console.warn("Dock client list:", error); }
            if (model.refreshPending) { model.refreshPending = false; refreshDelay.restart(); }
        }
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (["openwindow", "closewindow", "activewindowv2", "movewindow", "movewindowv2", "windowtitlev2", "configreloaded"].indexOf(event.name) >= 0)
                refreshDelay.restart();
        }
    }
    Timer { id: refreshDelay; interval: 40; onTriggered: model.refresh() }
    Timer { interval: 60000; repeat: true; running: model.observing; onTriggered: model.refresh() }
}
