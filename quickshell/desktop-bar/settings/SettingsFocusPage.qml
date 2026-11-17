import ".."
import QtQuick
import Eitr as Eitr

Column {
    id: focusPage
    required property var context
    readonly property var view: context
    width: parent ? parent.width : 0
    spacing: 18

    function durationChoices(presets, currentValue) {
        const values = presets.slice();
        if (currentValue >= 1 && values.indexOf(currentValue) < 0) {
            values.push(currentValue);
            values.sort(function(first, second) { return first - second; });
        }
        return values.map(function(minutes) {
            return {id: String(minutes), label: Eitr.I18n.tr("{minutes} min", {minutes: minutes})};
        });
    }

    ControlCard {
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        title: Eitr.I18n.tr("Focus")
        foreground: view.foreground
        visible: view.page === "focus"
        ToggleRow {
            SettingsTarget { objectName: "setting-focus-focus" }
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

    ControlCard {
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        title: Eitr.I18n.tr("Focus sessions")
        foreground: view.foreground
        visible: view.page === "focus"
        Row {
            width: parent.width
            spacing: 12
            ChoiceDropdown {
                SettingsTarget { objectName: "setting-focus-length" }
                width: Math.min(260, (parent.width - parent.spacing) / 2)
                floatingLabel: Eitr.I18n.tr("Focus length")
                helperText: Eitr.I18n.tr("Work duration before each break.")
                foreground: focusPage.view.foreground; gold: SettingsInk.gold; background: SettingsInk.background
                choices: focusPage.durationChoices([15, 20, 25, 30, 45, 60], FocusTimer.focusMinutes)
                current: String(FocusTimer.focusMinutes)
                onChosen: value => {
                    if (focusPage.view.live) FocusTimer.setLengths(Number(value), FocusTimer.breakMinutes);
                }
            }
            ChoiceDropdown {
                SettingsTarget { objectName: "setting-focus-break-length" }
                width: Math.min(260, (parent.width - parent.spacing) / 2)
                floatingLabel: Eitr.I18n.tr("Break length")
                helperText: Eitr.I18n.tr("Rest duration between focus rounds.")
                foreground: focusPage.view.foreground; gold: SettingsInk.gold; background: SettingsInk.background
                choices: focusPage.durationChoices([5, 10, 15, 20], FocusTimer.breakMinutes)
                current: String(FocusTimer.breakMinutes)
                onChosen: value => {
                    if (focusPage.view.live) FocusTimer.setLengths(FocusTimer.focusMinutes, Number(value));
                }
            }
        }
    }
}
