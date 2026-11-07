import ".."
import QtQuick
import Eitr as Eitr

Column {
    required property var context
    readonly property var view: context
    width: parent ? parent.width : 0
    spacing: 18
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Focus")
        foreground: view.foreground
        visible: view.page === "focus"
        ToggleRow {
            text: Eitr.I18n.tr("Focus")
            description: Eitr.I18n.tr("Use tabs and panes for a quiet desktop.")
            foreground: view.foreground
            accent: view.accent
            checked: FocusMode.enabled
            onToggled: checked => {
                if (view.live) {
                    FocusMode.select(checked);
                }
            }
        }
    }
}
