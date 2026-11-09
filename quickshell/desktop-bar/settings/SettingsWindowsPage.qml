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
    SettingsWorkspacesCard { foreground: view.foreground; live: view.live }
    ControlCard {
        title: Eitr.I18n.tr("Window layout")
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        foreground: view.foreground
        ChoiceDropdown {
            objectName: "windowLayoutChoice"
            SettingsTarget { objectName: "setting-windows-layout" }
            foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold
            label: Eitr.I18n.tr("Window layout")
            choices: ChoiceLists.windowLayouts
            current: DesktopStyle.windowLayout.layout
            onChosen: value => { if (view.live) DesktopStyle.selectLayout("layout", value); }
        }
        Column {
            objectName: "scrollingOptions"
            width: parent.width; spacing: 8
            visible: DesktopStyle.windowLayout.layout === "scrolling"
            ChoiceDropdown {
                foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold
                label: Eitr.I18n.tr("Direction")
                SettingsTarget { objectName: "setting-windows-scroll-direction" }
                choices: ChoiceLists.scrollingDirections
                current: DesktopStyle.windowLayout.scrollDirection
                onChosen: value => { if (view.live) DesktopStyle.selectLayout("scrollDirection", value); }
            }
            ChoiceDropdown {
                foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold
                label: Eitr.I18n.tr("Default column width")
                SettingsTarget { objectName: "setting-windows-column-width" }
                choices: ChoiceLists.scrollingWidths.map(choice => ({id: choice.id, label: choice.label}))
                current: DesktopStyle.windowLayout.scrollWidth
                onChosen: value => { if (view.live) DesktopStyle.selectLayout("scrollWidth", value); }
            }
            ChoiceDropdown {
                foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold
                label: Eitr.I18n.tr("Focus fit")
                SettingsTarget { objectName: "setting-windows-focus-fit" }
                choices: ChoiceLists.scrollingFocusFit.map(choice => ({id: choice.id, label: choice.label}))
                current: DesktopStyle.windowLayout.scrollFocusFit
                onChosen: value => { if (view.live) DesktopStyle.selectLayout("scrollFocusFit", value); }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Follow focus")
                SettingsTarget { objectName: "setting-windows-follow-focus" }
                foreground: view.foreground; accent: view.accent
                checked: DesktopStyle.windowLayout.scrollFollowFocus === "yes"
                onToggled: checked => { if (view.live) DesktopStyle.selectLayout("scrollFollowFocus", checked ? "yes" : "no"); }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Fullscreen when one column")
                SettingsTarget { objectName: "setting-windows-fullscreen-one-column" }
                foreground: view.foreground; accent: view.accent
                checked: DesktopStyle.windowLayout.scrollFullscreen === "yes"
                onToggled: checked => { if (view.live) DesktopStyle.selectLayout("scrollFullscreen", checked ? "yes" : "no"); }
            }
        }
    }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Window shape")
        foreground: view.foreground
        visible: view.page === "windows"
        Column {
            SettingsTarget { objectName: "setting-windows-window-gaps" }
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
            SettingsTarget { objectName: "setting-windows-corners" }
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
            SettingsTarget { objectName: "setting-windows-reduce-motion" }
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
