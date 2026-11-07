import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

FamilyWindow {
    id: window
    property alias page: content.page
    property alias networkService: content.networkService
    property alias notifications: content.notifications
    property alias idleEnabled: content.idleEnabled
    signal idleToggleRequested()
    signal themesRequested()
    property alias live: content.live
    stateName: "settings"
    title: Eitr.I18n.tr("Settings")

    function show(page) {
        content.navigate(page || "system");
        showWindow();
    }
    function closeSettings() { rememberSize(); opened = false; }
    SettingsContent {
        id: content
        anchors.fill: parent
        foreground: SettingsPalette.foreground; background: window.color; accent: SettingsPalette.accent
        opened: window.opened
        onThemesRequested: window.themesRequested()
        onIdleToggleRequested: window.idleToggleRequested()
        onCloseRequested: window.closeSettings()
    }
    IpcHandler {
        target: "settings"
        function toggle(): void { window.toggle(); }
        function show(page: string): void { window.show(page); }
        function palette(value: string): void { SettingsPalette.select(value); }
        function close(): void { window.closeSettings(); }
    }
}
