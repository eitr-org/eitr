import ".."
import QtQuick
import Quickshell.Io

// Eitr Store in the Settings family: the shared frame, sidebar and palette.
FamilyWindow {
    id: window
    title: "Eitr Store"
    function show(kind, tab) {
        if (kind && content.kinds.some(entry => entry.id === kind)) content.kind = kind;
        if (tab) content.tab = tab === "installed" ? "installed" : "discover";
        showWindow();
    }
    function showThemes(tone) {
        content.kind = "themes"; content.tab = "discover"; content.tone = tone;
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
        target: "store"
        function show(kind: string, tab: string): void { window.show(kind, tab); }
        function toggle(): void { window.toggle(); }
        function close(): void { window.opened = false; }
    }
    IpcHandler {
        target: "catalog"
        function show(kind: string, tab: string): void { window.show(kind, tab); }
        function toggle(): void { window.toggle(); }
        function close(): void { window.opened = false; }
    }
}
