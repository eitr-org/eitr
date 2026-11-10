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
        ControlRow {
            text: Eitr.I18n.tr("Window layout")
            description: Eitr.I18n.tr((ChoiceLists.windowLayouts.find(choice => choice.id === DesktopStyle.windowLayout.layout) || {}).description || "")
            foreground: view.foreground
            ChoiceSegmented {
                objectName: "windowLayoutChoice"
                SettingsTarget { objectName: "setting-windows-layout" }
                foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold

                choices: ChoiceLists.windowLayouts
                current: DesktopStyle.windowLayout.layout
                onChosen: value => { if (view.live) DesktopStyle.selectLayout("layout", value); }
            }
        }
        Column {
            objectName: "scrollingOptions"
            width: parent.width; spacing: 8
            visible: DesktopStyle.windowLayout.layout === "scrolling"
            // The three scrolling choices sit side by side, each describing its current value.
            Row {
                width: parent.width
                spacing: 16
                ChoiceDropdown {
                    SettingsTarget { objectName: "setting-windows-scroll-direction" }
                    objectName: "scrollDirectionChoice"
                    width: (parent.width - 2 * parent.spacing) / 3
                    floatingLabel: Eitr.I18n.tr("Direction")
                    helperText: Eitr.I18n.tr((ChoiceLists.scrollingDirections.find(choice => choice.id === DesktopStyle.windowLayout.scrollDirection) || {}).description || "")
                    foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold
                    choices: ChoiceLists.scrollingDirections
                    current: DesktopStyle.windowLayout.scrollDirection
                    onChosen: value => { if (view.live) DesktopStyle.selectLayout("scrollDirection", value); }
                }
                ChoiceDropdown {
                    SettingsTarget { objectName: "setting-windows-column-width" }
                    objectName: "scrollWidthChoice"
                    width: (parent.width - 2 * parent.spacing) / 3
                    floatingLabel: Eitr.I18n.tr("Default column width")
                    helperText: Eitr.I18n.tr((ChoiceLists.scrollingWidths.find(choice => choice.id === DesktopStyle.windowLayout.scrollWidth) || {}).description || "")
                    foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold
                    choices: ChoiceLists.scrollingWidths.map(choice => ({id: choice.id, label: choice.label}))
                    current: DesktopStyle.windowLayout.scrollWidth
                    onChosen: value => { if (view.live) DesktopStyle.selectLayout("scrollWidth", value); }
                }
                ChoiceDropdown {
                    SettingsTarget { objectName: "setting-windows-focus-fit" }
                    objectName: "scrollFocusFitChoice"
                    width: (parent.width - 2 * parent.spacing) / 3
                    floatingLabel: Eitr.I18n.tr("Focus fit")
                    helperText: Eitr.I18n.tr((ChoiceLists.scrollingFocusFit.find(choice => choice.id === DesktopStyle.windowLayout.scrollFocusFit) || {}).description || "")
                    foreground: view.foreground; background: SettingsInk.background; gold: SettingsInk.gold
                    choices: ChoiceLists.scrollingFocusFit.map(choice => ({id: choice.id, label: choice.label}))
                    current: DesktopStyle.windowLayout.scrollFocusFit
                    onChosen: value => { if (view.live) DesktopStyle.selectLayout("scrollFocusFit", value); }
                }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Follow focus")
                description: Eitr.I18n.tr("Scroll to the window that gets focus.")
                SettingsTarget { objectName: "setting-windows-follow-focus" }
                foreground: view.foreground; accent: view.accent
                checked: DesktopStyle.windowLayout.scrollFollowFocus === "yes"
                onToggled: checked => { if (view.live) DesktopStyle.selectLayout("scrollFollowFocus", checked ? "yes" : "no"); }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Fullscreen when one column")
                description: Eitr.I18n.tr("A lone column fills the screen.")
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
        SettingsChoiceSection {
            SettingsTarget { objectName: "setting-windows-window-gaps" }
            text: Eitr.I18n.tr("Window gaps")
            description: Eitr.I18n.tr((ChoiceLists.windowGaps.find(choice => choice.id === DesktopStyle.gaps) || {}).description || "")
            foreground: view.foreground
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
        SettingsChoiceSection {
            SettingsTarget { objectName: "setting-windows-corners" }
            text: Eitr.I18n.tr("Corners")
            description: Eitr.I18n.tr("Choose the shape of desktop corners.")
            foreground: view.foreground
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
