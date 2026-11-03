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
    color: SiteStyle.card
    function show() { showWindow(); }
    Rectangle {
        anchors.fill: parent
        color: SiteStyle.card
        radius: 4
        border.width: 1; border.color: SiteStyle.line
        SiteBackdrop { anchors.fill: parent; anchors.margins: 1 }
        CatalogContent {
            id: content
            anchors.fill: parent; anchors.margins: 1
            foreground: SiteStyle.fg; background: SiteStyle.card; accent: SiteStyle.accent
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
