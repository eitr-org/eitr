import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

// The Clock: a small chronograph window with Timers, Stopwatch, Focus and Alarms.
// It lives in the bar so the clock's ring shares its state, and remembers the last
// page within the desktop session.
FamilyWindow {
    id: window
    property string page: "timers"
    property bool live: true
    title: Eitr.I18n.tr("Clock")
    defaultSize: Qt.size(420, 660)

    function normalizePage(value) {
        return ["timers", "stopwatch", "focus", "alarms"].indexOf(value) >= 0 ? value : "";
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
            live: window.live
            onPageChanged: window.page = page
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
