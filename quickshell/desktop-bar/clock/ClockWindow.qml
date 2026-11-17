import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

// Clock window in the Settings/Store family: Timers, Stopwatch, Focus, and World.
// Remembers the last viewed page within the desktop session.
FamilyWindow {
    id: window
    property string page: "timers"
    property string clockFormat: "24h"
    property bool live: true
    signal storeRequested(string kind, string tab)
    title: Eitr.I18n.tr("Clock")

    function normalizePage(value) {
        return ["timers", "stopwatch", "focus", "world"].indexOf(value) >= 0 ? value : "";
    }

    onPageChanged: {
        const valid = normalizePage(page);
        if (!valid) return;
        if (contentLoader.item && contentLoader.item.page !== valid) contentLoader.item.page = valid;
    }

    function ensureContent() {
        contentLoader.active = true;
        contentLoader.asynchronous = false;
        return contentLoader.item;
    }

    function show(requestedPage) {
        const valid = normalizePage(requestedPage);
        if (valid) page = valid;
        const content = ensureContent();
        if (content) content.page = page;
        showWindow();
    }

    function closeClock() {
        opened = false;
    }

    onOpenedChanged: if (opened) ensureContent()

    Loader {
        id: contentLoader
        anchors.fill: parent
        active: false
        onLoaded: item.parent = window.contentItem
        sourceComponent: ClockContent {
            anchors.fill: parent
            objectName: "clock-content"
            foreground: SettingsPalette.foreground
            background: window.color
            accent: SettingsPalette.accent
            opened: window.opened
            page: window.page
            clockFormat: window.clockFormat
            live: window.live
            onPageChanged: window.page = page
            onStoreRequested: function(kind, tab) {
                window.closeClock();
                window.storeRequested(kind, tab);
            }
            onCloseRequested: window.closeClock()
        }
    }

    IpcHandler {
        target: "clock"
        function toggle(): void { window.toggle(); }
        function show(page: string): void { window.show(page); }
        function close(): void { window.closeClock(); }
    }
}
