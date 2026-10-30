pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import "Performance.js" as Performance

QtObject {
    id: obs
    property var state: ({running: false, ready: false, recording: false, paused: false, streaming: false})
    readonly property bool hasWindow: Hyprland.toplevels.values.some(window => /^(com\.obsproject\.studio|obs)$/i.test((window.lastIpcObject || {}).class))
    property int detailObservers: 0
    property bool pending: false
    signal received(var snapshot)
    function refresh() {
        if (query.running) pending = true;
        else query.running = true;
    }
    Component.onCompleted: refresh()
    onHasWindowChanged: refresh()
    property Timer poll: Timer {
        interval: 2000; repeat: true
        running: Performance.obsPolling(obs.hasWindow, obs.state.running === true, obs.detailObservers)
        onTriggered: obs.refresh()
    }
    property Connections events: Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "openwindow" && /,(com\.obsproject\.studio|obs),/i.test(event.data)) obs.refresh();
        }
    }
    property Process query: Process {
        command: ["python3", Quickshell.shellDir + "/scripts/obs-control.py", "status"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            try {
                if (code !== 0) throw new Error("OBS query failed");
                obs.state = JSON.parse(output.text);
            } catch (error) {
                obs.state = {running: obs.hasWindow, ready: false, recording: false, paused: false, streaming: false};
            }
            obs.received(obs.state);
            if (obs.pending) { obs.pending = false; Qt.callLater(obs.refresh); }
        }
    }
}
