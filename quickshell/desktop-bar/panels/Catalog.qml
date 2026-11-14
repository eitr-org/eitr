import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

// Eitr Store in the Settings family: the shared frame, sidebar and palette.
FamilyWindow {
    id: window
    title: "Eitr Store"
    property bool explicitView: false
    function show(kind, tab) {
        if (kind || tab) explicitView = true;
        if (kind && content.kinds.some(entry => entry.id === kind)) content.kind = kind;
        if (tab) content.tab = ["installed", "updates"].includes(tab) ? tab : "discover";
        showWindow();
    }
    function showThemes(tone) {
        explicitView = true;
        content.kind = "themes"; content.tab = "discover"; content.tone = tone;
        showWindow();
    }
    FileView {
        id: viewState
        path: Eitr.Paths.config("eitr/store.json")
        atomicWrites: true; printErrors: false
        onLoaded: {
            if (window.explicitView) return;
            try {
                const saved = Eitr.Paths.settings(text());
                if (content.kinds.some(entry => entry.id === saved.kind)) content.kind = saved.kind;
                if (["discover", "installed", "updates"].includes(saved.section)) content.tab = saved.section;
            } catch (error) { console.warn("Invalid Store view state"); }
        }
    }
    onOpenedChanged: if (!opened) viewState.setText(JSON.stringify({version: 1, kind: content.kind, section: content.tab}) + "\n")
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
