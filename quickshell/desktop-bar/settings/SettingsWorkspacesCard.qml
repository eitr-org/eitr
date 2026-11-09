import ".."
import QtQuick
import Eitr as Eitr
import "../ChoiceLists.js" as ChoiceLists

ControlCard {
    id: card
    required property bool live
    title: Eitr.I18n.tr("Workspaces")
    surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
    function numbers(first, last) {
        return Array.from({length: last - first + 1}, (unused, index) => ({id: String(first + index), label: String(first + index)}));
    }
    ChoiceDropdown {
        SettingsTarget { objectName: "setting-windows-workspace-monitors" }
        foreground: card.foreground; background: SettingsInk.background; gold: SettingsInk.gold
        label: Eitr.I18n.tr("Monitors")
        choices: ChoiceLists.workspaceModes
        current: DesktopStyle.workspaceMode
        onChosen: value => { if (card.live) DesktopStyle.selectWorkspace("workspaceMode", value); }
    }
    Column {
        width: parent.width; spacing: 4
        SettingsTarget { objectName: "setting-windows-workspace-count" }
        SettingsText { text: Eitr.I18n.tr("Number of workspaces"); color: card.foreground }
        ChoiceLevel {
            foreground: card.foreground; accent: SettingsInk.gold
            accessibleName: Eitr.I18n.tr("Number of workspaces")
            choices: card.numbers(5, 10)
            current: String(DesktopStyle.workspaceCount)
            onChosen: value => { if (card.live) DesktopStyle.selectWorkspace("workspaceCount", value); }
        }
    }
    Column {
        width: parent.width; spacing: 4
        SettingsTarget { objectName: "setting-windows-workspace-always-show" }
        SettingsText { text: Eitr.I18n.tr("Always show"); color: card.foreground }
        ChoiceLevel {
            foreground: card.foreground; accent: SettingsInk.gold
            accessibleName: Eitr.I18n.tr("Always show")
            choices: card.numbers(2, DesktopStyle.workspaceCount)
            current: String(DesktopStyle.workspaceAlwaysShow)
            onChosen: value => { if (card.live) DesktopStyle.selectWorkspace("workspaceAlwaysShow", value); }
        }
    }
}
