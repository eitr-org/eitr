import ".."
import QtQuick
import Eitr as Eitr
import "../ChoiceLists.js" as ChoiceLists

Column {
    required property var context
    readonly property var view: context
    readonly property var styleModel: context.styleState
    width: parent ? parent.width : 0
    spacing: 18
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Window shape")
        foreground: view.foreground
        visible: view.page === "windows"
        Column {
            width: parent.width
            spacing: 8
            SettingsText { text: Eitr.I18n.tr("Window gaps"); color: SettingsInk.gold }
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                kind: "gaps"
                edge: styleModel.barPosition
                appearance: styleModel.appearance
                compact: true
                choices: ChoiceLists.windowGaps
                current: DesktopStyle.gaps
                onChosen: value => {
                    if (view.live) {
                        DesktopStyle.selectGaps(value);
                    }
                }
            }
        }
        Column {
            width: parent.width
            spacing: 8
            SettingsText { text: Eitr.I18n.tr("Corners"); color: SettingsInk.gold }
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                kind: "corners"
                edge: styleModel.barPosition
                appearance: styleModel.appearance
                compact: true
                choices: DesktopStyle.options
                current: DesktopStyle.corners
                onChosen: value => {
                    if (view.live) {
                        DesktopStyle.select(value);
                    }
                }
            }
        }
        ToggleRow {
            text: Eitr.I18n.tr("Reduce motion")
            description: Eitr.I18n.tr("Minimise decorative movement.")
            foreground: view.foreground
            accent: view.accent
            checked: DesktopStyle.reduceMotion
            onToggled: checked => {
                if (view.live) {
                    styleModel.settingRequested("reduceMotion", checked ? "yes" : "no");
                }
            }
        }
    }
}
