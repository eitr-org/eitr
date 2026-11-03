import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import "../PanelStyle.js" as PanelStyle

FloatingWindow {
    id: window
    property string stateName: "catalog"
    property bool opened: false
    property size savedSize: Qt.size(1100, 800)
    property bool stateReady: false
    readonly property var toplevel: ToplevelManager.toplevels.values.find(entry => entry.appId === "eitr-catalog" && entry.title === window.title) || null
    readonly property bool focused: !!toplevel && toplevel.activated
    visible: opened
    title: "Eitr"
    color: "transparent"
    implicitWidth: 1100
    implicitHeight: 800

    function showWindow() {
        if (!opened) {
            implicitWidth = Math.max(1, Math.min(savedSize.width, screen ? screen.width - 32 : 1100));
            implicitHeight = Math.max(1, Math.min(savedSize.height, screen ? screen.height - 64 : 800));
        }
        opened = true;
        minimized = false;
        if (toplevel) toplevel.activate();
    }
    function toggle() {
        if (opened && focused) { rememberSize(); opened = false; }
        else showWindow();
    }
    function rememberSize() {
        if (!stateReady || !opened || width <= 0 || height <= 0) return;
        savedSize = Qt.size(width, height);
        sizeStore.setText(JSON.stringify({width: width, height: height}) + "\n");
    }
    onWidthChanged: if (opened) saveDelay.restart()
    onHeightChanged: if (opened) saveDelay.restart()
    onOpenedChanged: {
        if (!opened) { saveDelay.stop(); }
    }
    onClosed: { rememberSize(); opened = false; }
    Timer { id: saveDelay; interval: 300; onTriggered: window.rememberSize() }
    Process {
        command: ["mkdir", "-p", (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/eitr"]
        running: true
    }
    FileView {
        id: sizeStore
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/eitr/" + window.stateName + "-window.json"
        atomicWrites: true
        printErrors: false
        onLoaded: {
            try {
                const size = JSON.parse(text());
                if (Number.isFinite(size.width) && Number.isFinite(size.height) && size.width > 0 && size.height > 0)
                    window.savedSize = Qt.size(size.width, size.height);
            } catch (error) { console.warn("Library window size:", error); }
            window.stateReady = true;
        }
        onLoadFailed: window.stateReady = true
    }
}
