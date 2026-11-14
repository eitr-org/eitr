import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland
import "../PanelStyle.js" as PanelStyle

// Settings, the Handbook and Eitr Store: a floating window that opens at its
// default size every time (bounded by the screen); a resize lasts until it closes.
FloatingWindow {
    id: window
    property bool opened: false
    property size defaultSize: Qt.size(1100, 800)
    readonly property var toplevel: ToplevelManager.toplevels.values.find(entry => entry.appId === "eitr-catalog" && entry.title === window.title) || null
    readonly property bool focused: !!toplevel && toplevel.activated
    visible: opened
    title: "Eitr"
    color: "transparent"
    implicitWidth: defaultSize.width
    implicitHeight: defaultSize.height

    function showWindow() {
        if (!opened) {
            const width = Math.max(1, Math.min(defaultSize.width, screen ? screen.width - 32 : defaultSize.width));
            const height = Math.max(1, Math.min(defaultSize.height, screen ? screen.height - 64 : defaultSize.height));
            // A resize by the person changes the window, not these requested values, so
            // assigning the same default again would change nothing: step off it first.
            implicitWidth = width + 1;
            implicitHeight = height + 1;
            implicitWidth = width;
            implicitHeight = height;
        }
        opened = true;
        minimized = false;
        if (toplevel) toplevel.activate();
    }
    function toggle() {
        if (opened && focused) opened = false;
        else showWindow();
    }
    onClosed: opened = false
}
