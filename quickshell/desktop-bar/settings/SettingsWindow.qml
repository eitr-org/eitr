import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

FamilyWindow {
    id: window
    property string page: "system"
    onPageChanged: if (contentLoader.item && contentLoader.item.page !== page) contentLoader.item.navigate(page)
    property var networkService: null
    property var notifications: null
    property bool idleEnabled: false
    signal idleToggleRequested()
    signal themesRequested()
    property bool live: true
    title: Eitr.I18n.tr("Settings")

    function show(page) {
        ensureContent().navigate(page || "system");
        showWindow();
    }
    function closeSettings() { opened = false; }
    function ensureContent() {
        contentLoader.active = true;
        contentLoader.asynchronous = false;
        return contentLoader.item;
    }
    onOpenedChanged: if (opened) ensureContent()
    Loader {
        id: contentLoader
        anchors.fill: parent
        active: false
        // Native overlays share the window's content and keyboard focus scope.
        onLoaded: item.parent = window.contentItem
        sourceComponent: SettingsContent {
            anchors.fill: parent
            foreground: SettingsPalette.foreground; background: window.color; accent: SettingsPalette.accent
            opened: window.opened
            networkService: window.networkService
            notifications: window.notifications
            idleEnabled: window.idleEnabled
            live: window.live
            Component.onCompleted: navigate(window.page)
            onPageChanged: window.page = page
            onThemesRequested: window.themesRequested()
            onIdleToggleRequested: window.idleToggleRequested()
            onCloseRequested: window.closeSettings()
        }
    }
    IpcHandler {
        target: "settings"
        function toggle(): void { window.toggle(); }
        function show(page: string): void { window.show(page); }
        function palette(value: string): void { SettingsPalette.select(value); }
        function close(): void { window.closeSettings(); }
    }
}
