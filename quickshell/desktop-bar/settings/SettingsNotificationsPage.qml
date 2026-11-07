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
