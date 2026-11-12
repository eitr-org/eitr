import ".."
import QtQuick
import Eitr as Eitr

Column {
    required property var context
    readonly property var view: context
    readonly property var notificationState: context.notificationState
    width: parent ? parent.width : 0
    spacing: 18
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Notifications")
        foreground: view.foreground
        visible: view.page === "notifications"
        ToggleRow {
            SettingsTarget { objectName: "setting-notifications-do-not-disturb" }
            text: Eitr.I18n.tr("Do Not Disturb")
            description: Eitr.I18n.tr("Pause notification popups.")
            foreground: view.foreground
            accent: view.accent
            checked: !!view.notifications && view.notifications.doNotDisturb
            onToggled: checked => {
                if (view.live) {
                    if (view.notifications)
                        view.notifications.toggleDnd();
                }
            }
        }
        ToggleRow {
            SettingsTarget { objectName: "setting-notifications-every-display" }
            text: Eitr.I18n.tr("Popups on Every Display")
            description: Eitr.I18n.tr("Off shows them only on the main display.")
            foreground: view.foreground
            accent: view.accent
            checked: !view.notifications || view.notifications.popupsOnAllDisplays
            onToggled: checked => {
                if (view.live && view.notifications)
                    view.notifications.setPopupsOnAllDisplays(checked);
            }
        }
        ToggleRow {
            SettingsTarget { objectName: "setting-notifications-crash-notifications" }
            text: Eitr.I18n.tr("Crash Notifications")
            description: Eitr.I18n.tr("Show help notifications when a program crashes.")
            foreground: view.foreground
            accent: view.accent
            checked: notificationState.enabled
            onToggled: checked => {
                if (view.live) {
                    if (!notificationState.operation.running)
                        notificationState.operation.running = true;
                }
            }
        }
        EventSoundSettings {
            searchPage: "notifications"
            width: parent.width
            foreground: view.foreground
            accent: view.accent
            live: view.live
            hasBattery: view.active && view.page === "notifications" && PowerService.battery.available
        }
    }
    SettingsText {
        visible: view.page === "notifications" && notificationState.error !== ""
        text: notificationState.error
    }
}
