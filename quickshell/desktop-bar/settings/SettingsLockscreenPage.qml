import ".."
import QtQuick
import Eitr as Eitr

Column {
    required property var context
    readonly property var view: context
    readonly property var styleModel: context.styleState
    width: parent ? parent.width : 0
    spacing: 18
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Lockscreen")
        foreground: view.foreground
        visible: view.page === "lockscreen"
        Column {
            width: parent.width
            spacing: 8
            SettingsText { text: Eitr.I18n.tr("Design"); color: SettingsInk.gold }
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                kind: "lockscreen"
                edge: styleModel.barPosition
                appearance: styleModel.appearance
                compact: false
                choices: styleModel.lockscreens
                current: styleModel.lockscreen
                onChosen: value => {
                    if (view.live) {
                        styleModel.run(styleModel.lockscreenWriteRef, ["python3", styleModel.lockscreenScript, "select", value]);
                    }
                }
            }
        }
        ToggleRow {
            text: Eitr.I18n.tr("Idle Lock")
            description: Eitr.I18n.tr("Dim and lock automatically while idle.")
            foreground: view.foreground
            accent: view.accent
            checked: view.idleEnabled
            onToggled: checked => {
                if (view.live) {
                    view.idleToggleRequested();
                }
            }
        }
    }
}
