import ".."
import QtQuick
import Quickshell.Io

// Add-ons in the Settings family: the shared frame, sidebar and palette.
FamilyWindow {
    id: window
    title: "Add-ons"
    function show() { showWindow(); }
    function showThemes(tone) {
        content.kind = "themes"; content.tab = "official"; content.tone = tone;
        showWindow();
    }
    CatalogContent {
        id: content
        objectName: "catalog-content"
        anchors.fill: parent
        foreground: SettingsPalette.foreground; background: window.color; accent: SettingsPalette.accent
        opened: window.opened
        onCloseRequested: window.opened = false
    }
    IpcHandler {
        target: "catalog"
        function toggle(): void { window.toggle(); }
        function close(): void { window.opened = false; }
    }
}
