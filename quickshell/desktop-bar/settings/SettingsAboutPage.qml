import ".."
import QtQuick
import Eitr as Eitr

Column {
    id: pageBody
    required property var context
    readonly property var view: context
    width: parent ? parent.width : 0
    spacing: 12
    ControlCard {
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        title: Eitr.I18n.tr("About logo")
        foreground: view.foreground
        width: parent.width
        PictureChoices {
            foreground: SettingsPalette.foreground; background: SettingsPalette.background
            accent: SettingsPalette.accent; gold: SettingsPalette.gold
            raised: SettingsPalette.raised; surface: SettingsPalette.surface
            line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true
            themeAccent: SettingsPalette.themeAccent; themeBackground: SettingsPalette.themeBackground
            kind: "about-logo"
            choices: view.helper.summary.aboutLogos || []
            current: view.helper.summary.aboutLogo || "emblem"
            available: !view.helper.busy
            onChosen: value => view.helper.change(["about-logo", "about", value])
        }
    }
    SettingsSummaryCards { context: pageBody.context }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("About")
        foreground: view.foreground
        visible: view.page === "about"
        width: parent.width
        spacing: 12
        Repeater {
            model: view.helper.summary.hardware || []
            SettingsText {
                required property var modelData
                text: Eitr.I18n.tr(modelData.title) + " · " + modelData.name
            }
        }
    }
}
