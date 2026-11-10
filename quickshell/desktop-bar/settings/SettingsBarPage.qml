import ".."
import QtQuick
import Eitr as Eitr
import "../ChoiceLists.js" as ChoiceLists

Column {
    required property var context
    readonly property var view: context
    readonly property var styleModel: context.styleState
    readonly property var workspaceHelper: context.workspaceHelper
    width: parent ? parent.width : 0
    spacing: 18
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Bar")
        foreground: view.foreground
        visible: view.page === "bar"
        SettingsChoiceSection {
            SettingsTarget { objectName: "setting-bar-layout" }
            text: Eitr.I18n.tr("Layout")
            description: Eitr.I18n.tr((ChoiceLists.barLayouts.find(choice => choice.id === styleModel.layout) || {}).description || "")
            foreground: view.foreground
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                kind: "layout"
                edge: styleModel.barPosition
                appearance: styleModel.appearance
                compact: false
                choices: ChoiceLists.barLayouts
                current: styleModel.layout
                onChosen: value => {
                    if (view.live) {
                        styleModel.settingRequested("layout", value);
                    }
                }
            }
        }
        SettingsChoiceSection {
            SettingsTarget { objectName: "setting-bar-position" }
            text: Eitr.I18n.tr("Position")
            description: Eitr.I18n.tr("Choose the screen edge for the bar.")
            foreground: view.foreground
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                kind: "position"
                edge: styleModel.barPosition
                appearance: styleModel.appearance
                compact: true
                choices: [
                    {
                        id: "top",
                        label: "Top"
                    },
                    {
                        id: "bottom",
                        label: "Bottom"
                    },
                    {
                        id: "left",
                        label: "Left"
                    },
                    {
                        id: "right",
                        label: "Right"
                    }
                ]
                current: styleModel.barPosition
                onChosen: value => {
                    if (view.live) {
                        styleModel.settingRequested("edge", value);
                    }
                }
            }
        }
        SettingsChoiceSection {
            SettingsTarget { objectName: "setting-bar-appearance" }
            text: Eitr.I18n.tr("Appearance")
            description: Eitr.I18n.tr((ChoiceLists.barAppearances.find(choice => choice.id === styleModel.appearance) || {}).description || "")
            foreground: view.foreground
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                kind: "appearance"
                edge: styleModel.barPosition
                appearance: styleModel.appearance
                compact: true
                choices: ChoiceLists.barAppearances
                current: styleModel.appearance
                onChosen: value => {
                    if (view.live) {
                        styleModel.settingRequested("appearance", value);
                    }
                }
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-bar-show-on" }
            text: Eitr.I18n.tr("Show on")
            description: Eitr.I18n.tr("Choose which displays show a bar.")
            foreground: view.foreground
            ChoiceSegmented { gold: SettingsInk.gold; background: SettingsInk.background;
                foreground: view.foreground
                choices: [
                    {
                        id: "main",
                        label: "Main Display"
                    },
                    {
                        id: "all",
                        label: "All Displays"
                    }
                ]
                current: styleModel.barScreens
                onChosen: value => {
                    if (view.live) {
                        styleModel.settingRequested("screens", value);
                    }
                }
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-bar-clock" }
            text: Eitr.I18n.tr("Clock")
            description: Eitr.I18n.tr("Choose the time format.")
            foreground: view.foreground
            ChoiceSegmented { gold: SettingsInk.gold; background: SettingsInk.background;
                foreground: view.foreground
                choices: [
                    {
                        id: "12h",
                        label: "12-hour"
                    },
                    {
                        id: "24h",
                        label: "24-hour"
                    }
                ]
                current: styleModel.clockFormat
                onChosen: value => {
                    if (view.live) {
                        styleModel.settingRequested("clock", value);
                    }
                }
            }
        }
        SettingsChoiceSection {
            SettingsTarget { objectName: "setting-bar-media-style" }
            text: Eitr.I18n.tr("Media style")
            description: Eitr.I18n.tr("Choose the shape of the playing indicator.")
            foreground: view.foreground
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                kind: "media"
                edge: styleModel.barPosition
                appearance: styleModel.appearance
                compact: true
                choices: [
                    {
                        id: "bars",
                        label: "Bars"
                    },
                    {
                        id: "line",
                        label: "Line"
                    }
                ]
                current: styleModel.mediaStyle
                onChosen: value => {
                    if (view.live) {
                        styleModel.settingRequested("mediaStyle", value);
                    }
                }
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-bar-blur-strength-shared" }
            text: Eitr.I18n.tr("Blur strength (shared)")
            description: Eitr.I18n.tr("Adjust blur across the desktop.")
            foreground: view.foreground
            ChoiceLevel {
                foreground: view.foreground
                accent: view.accent
                choices: styleModel.terminalAppearanceChoices["blur-strength"] || []
                current: styleModel.terminalAppearance["blur-strength"] || ""
                accessibleName: Eitr.I18n.tr("Blur strength (shared)")
                onChosen: value => styleModel.run(styleModel.terminalWriteRef, ["python3", styleModel.terminalScript, "set", "blur-strength", value])
            }
        }
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-bar-workspace-style" }
            floatingLabel: Eitr.I18n.tr("Workspace style")
            helperText: Eitr.I18n.tr("Choose how workspaces appear in the bar.")
            width: Math.min(parent.width, 460)
            gold: SettingsInk.gold; background: SettingsInk.background;
            foreground: view.foreground
            choices: workspaceHelper.summary.choices || []
            current: styleModel.workspaceStyle
            onChosen: value => {
                if (view.live) {
                    styleModel.workspaceStyleRequested(value);
                }
            }
        }
    }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Behavior")
        foreground: view.foreground
        visible: view.page === "bar"
        ToggleRow {
            SettingsTarget { objectName: "setting-bar-auto-hide" }
            text: Eitr.I18n.tr("Auto-hide")
            description: Eitr.I18n.tr("Hide the bar until you reach its screen edge.")
            foreground: view.foreground
            accent: view.accent
            checked: styleModel.barAutoHide
            onToggled: checked => {
                if (view.live) {
                    styleModel.settingRequested("autohide", checked ? "yes" : "no");
                }
            }
        }
        ToggleRow {
            SettingsTarget { objectName: "setting-bar-dock" }
            text: Eitr.I18n.tr("Dock")
            description: Eitr.I18n.tr("Show the application dock.")
            foreground: view.foreground
            accent: view.accent
            checked: styleModel.barDock
            onToggled: checked => {
                if (view.live) {
                    styleModel.settingRequested("dock", checked ? "yes" : "no");
                }
            }
        }
        ToggleRow {
            SettingsTarget { objectName: "setting-bar-reduce-motion" }
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
        ToggleRow {
            SettingsTarget { objectName: "setting-bar-keep-expanded" }
            text: Eitr.I18n.tr("Keep expanded")
            description: Eitr.I18n.tr("Keep the centered bar expanded.")
            foreground: view.foreground
            accent: view.accent
            checked: styleModel.bar.pinned === "yes"
            onToggled: checked => {
                if (view.live) {
                    styleModel.settingRequested("pinned", checked ? "yes" : "no");
                }
            }
        }
    }
}
