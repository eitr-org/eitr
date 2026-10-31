pragma Singleton
import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import "../FocusModel.js" as FocusModel
import Eitr as Eitr

QtObject {
    id: focus
    property bool enabled: false
    property DockClients clients: DockClients { observing: focus.enabled; followTitles: true }
    property string error: ""
    property var requested: null
    function command(action) { return ["python3", Quickshell.shellDir + "/scripts/focus-mode.py", action]; }
    function select(value) {
        requested = value;
        applyRequested();
    }
    function applyRequested() {
        if (change.running || requested === null) return;
        change.command = command(requested ? "on" : "off");
        requested = null;
        change.running = true;
    }
    function tabs(screen) {
        const monitor = Hyprland.monitorFor(screen);
        return monitor ? FocusModel.tabsForMonitor(clients.clients, monitor.id) : [];
    }
    function activate(address) {
        if (!/^0x[0-9a-fA-F]+$/.test(address)) return;
        Quickshell.execDetached(["hyprctl", "eval", 'local window=hl.get_window("address:' + address + '"); if window then hl.dispatch(hl.dsp.focus({window=window})) end']);
    }
    property FileView preference: FileView {
        path: Eitr.Paths.config("eitr/focus.json")
        watchChanges: true; printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try { focus.enabled = Eitr.Paths.settings(text()).enabled === true; }
            catch (error) { focus.error = String(error); }
        }
        onLoadFailed: focus.enabled = false
    }
    property Process change: Process {
        stderr: StdioCollector { id: errors }
        onExited: function(code) {
            focus.error = code === 0 ? "" : errors.text;
            focus.preference.reload();
            Qt.callLater(focus.applyRequested);
        }
    }
    property Connections events: Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (["togglegroup", "moveintogroup", "moveoutofgroup", "changegroupactive"].indexOf(event.name) >= 0)
                focus.clients.refresh();
        }
    }
}
