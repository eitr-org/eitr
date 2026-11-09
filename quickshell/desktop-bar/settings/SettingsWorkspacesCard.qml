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
    ControlRow {
        controlWidth: Math.min(440, width * 0.55)
        text: Eitr.I18n.tr("Monitors")
        description: Eitr.I18n.tr((ChoiceLists.workspaceModes.find(choice => choice.id === DesktopStyle.workspaceMode) || {}).description || "")
        foreground: card.foreground
        ChoiceSegmented {
            SettingsTarget { objectName: "setting-windows-workspace-monitors" }
            foreground: card.foreground; background: SettingsInk.background; gold: SettingsInk.gold

            choices: ChoiceLists.workspaceModes
            current: DesktopStyle.workspaceMode
            onChosen: value => { if (card.live) DesktopStyle.selectWorkspace("workspaceMode", value); }
        }
    }
    ControlRow {
        text: Eitr.I18n.tr("Number of workspaces")
        description: Eitr.I18n.tr("Set the total number of numbered workspaces.")
        foreground: card.foreground
        SettingsTarget { objectName: "setting-windows-workspace-count" }
        ChoiceDropdown {
            foreground: card.foreground; gold: SettingsInk.gold; background: SettingsInk.background
            accessibleName: Eitr.I18n.tr("Number of workspaces")
            choices: card.numbers(5, 10)
            current: String(DesktopStyle.workspaceCount)
            onChosen: value => { if (card.live) DesktopStyle.selectWorkspace("workspaceCount", value); }
        }
    }
    ControlRow {
        text: Eitr.I18n.tr("Always show")
        description: Eitr.I18n.tr("Keep this many workspace markers visible.")
        foreground: card.foreground
        SettingsTarget { objectName: "setting-windows-workspace-always-show" }
        ChoiceDropdown {
            foreground: card.foreground; gold: SettingsInk.gold; background: SettingsInk.background
            accessibleName: Eitr.I18n.tr("Always show")
            choices: card.numbers(2, DesktopStyle.workspaceCount)
            current: String(DesktopStyle.workspaceAlwaysShow)
            onChosen: value => { if (card.live) DesktopStyle.selectWorkspace("workspaceAlwaysShow", value); }
        }
    }
}
