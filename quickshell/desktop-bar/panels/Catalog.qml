import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import "../PanelStyle.js" as PanelStyle

LibraryWindow {
    id: window
    required property color foreground
    required property color background
    required property color accent
    title: "Themes & Plugins"
    function show() { showWindow(); }
    Rectangle {
        anchors.fill: parent
        color: window.background
        radius: DesktopStyle.radius(PanelStyle.cornerRadius)
        border.width: 1; border.color: Qt.alpha(window.foreground, 0.12)
        CatalogContent {
            id: content
            anchors.fill: parent
            foreground: window.foreground; background: window.background; accent: window.accent
            opened: window.opened
            onCloseRequested: { window.rememberSize(); window.opened = false; }
        }
    }
    IpcHandler {
        target: "catalog"
        function toggle(): void { window.toggle(); }
        function close(): void { window.rememberSize(); window.opened = false; }
    }
}
