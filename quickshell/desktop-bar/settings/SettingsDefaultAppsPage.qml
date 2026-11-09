import ".."
import QtQuick
import Eitr as Eitr

Column {
    required property var context
    readonly property var view: context
    readonly property var defaults: context.defaults
    readonly property var content: parent
    width: parent ? parent.width : 0
    spacing: 12
    Repeater {
        model: view.page === "default-apps" ? defaults.summary.items || [] : []
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            id: appCard
            objectName: "settings-default-app-card"
            required property var modelData
            width: content.width
            title: Eitr.I18n.tr(modelData.label)
            foreground: view.foreground
            ControlRow {
                SettingsTarget { objectName: "setting-default-apps-" + appCard.modelData.kind }
                text: Eitr.I18n.tr(appCard.modelData.label)
                description: Eitr.I18n.tr("Choose the app used for this file or link type.")
                foreground: view.foreground
                ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
                    foreground: view.foreground
                    choices: appCard.modelData.choices
                    current: appCard.modelData.current
                    available: !defaults.busy
                    onChosen: value => defaults.change(["set", appCard.modelData.kind, value])
                }
            }
        }
    }
}
