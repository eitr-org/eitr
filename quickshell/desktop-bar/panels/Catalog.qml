import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../StoreKinds.js" as StoreKinds

// Eitr Store in the Settings family: the shared frame, sidebar and palette.
FamilyWindow {
    id: window
    title: "Eitr Store"
    property bool explicitView: false
    property string kind: "themes"
    property string tab: "discover"
    property string tone: "all"
    onKindChanged: if (contentLoader.item) contentLoader.item.kind = kind
    onTabChanged: if (contentLoader.item) contentLoader.item.tab = tab
    onToneChanged: if (contentLoader.item) contentLoader.item.tone = tone
    function ensureContent() {
        contentLoader.active = true;
        contentLoader.asynchronous = false;
        return contentLoader.item;
    }
    function show(kind, tab) {
        if (kind || tab) explicitView = true;
        if (kind && StoreKinds.kinds.some(entry => entry.id === kind)) window.kind = kind;
        if (tab) window.tab = ["installed", "updates"].includes(tab) ? tab : "discover";
        showWindow();
    }
    function showThemes(tone) {
        explicitView = true;
        window.kind = "themes"; window.tab = "discover"; window.tone = tone;
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
                if (StoreKinds.kinds.some(entry => entry.id === saved.kind)) window.kind = saved.kind;
                if (["discover", "installed", "updates"].includes(saved.section)) window.tab = saved.section;
            } catch (error) { console.warn("Invalid Store view state"); }
        }
    }
    onOpenedChanged: if (opened) ensureContent(); else viewState.setText(JSON.stringify({version: 1, kind: window.kind, section: window.tab}) + "\n")
    Loader {
        id: contentLoader
        anchors.fill: parent
        active: false
        // Native overlays share the window's content and keyboard focus scope.
        onLoaded: item.parent = window.contentItem
        sourceComponent: CatalogContent {
            anchors.fill: parent
            objectName: "catalog-content"
            foreground: SettingsPalette.foreground; background: window.color; accent: SettingsPalette.accent
            opened: window.opened
            kind: window.kind; tab: window.tab; tone: window.tone
            onKindChanged: window.kind = kind
            onTabChanged: window.tab = tab
            onToneChanged: window.tone = tone
            onCloseRequested: window.opened = false
        }
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
