import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland
import "../PanelStyle.js" as PanelStyle

// Settings, the Handbook and Themes & Plugins: a floating window that opens at its
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
            implicitWidth = Math.max(1, Math.min(defaultSize.width, screen ? screen.width - 32 : defaultSize.width));
            implicitHeight = Math.max(1, Math.min(defaultSize.height, screen ? screen.height - 64 : defaultSize.height));
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
