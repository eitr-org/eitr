import ".."
import QtQuick
import Eitr as Eitr

Column {
    required property var context
    readonly property var view: context
    readonly property var styleModel: context.styleState
    readonly property var themeModel: context.themeModel
    readonly property var wallpaperModel: context.wallpaperModel
    readonly property var fontHelper: context.fontHelper
    width: parent ? parent.width : 0
    spacing: 18
    TabStrip { foreground: SettingsPalette.foreground; gold: SettingsPalette.gold; carved: true;
        width: parent.width
        visible: view.page === "appearance"
        height: visible ? 42 : 0
        choices: [{id: "theme", label: Eitr.I18n.tr("Theme & Wallpaper")}, {id: "fonts", label: Eitr.I18n.tr("Fonts & Cursor")}, {id: "terminal", label: Eitr.I18n.tr("Terminal")}]
        current: view.tab
        onChosen: value => { view.tabRequested(value); view.contentY = 0; }
    }
    ControlCard {
        SettingsTarget { objectName: "setting-appearance-settings-colours" } surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Settings colours")
        foreground: view.foreground
        visible: view.page === "appearance" && view.tab === "theme"
        SettingsChoiceSection {
            text: Eitr.I18n.tr("Settings colours")
            description: Eitr.I18n.tr("Choose the colours used by Settings.")
            foreground: view.foreground
            PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                themeBackground: SettingsPalette.themeBackground
                themeForeground: SettingsPalette.themeForeground
                themeAccent: SettingsPalette.themeAccent
                kind: "palette"
                choices: [{id: "theme", label: Eitr.I18n.tr("Theme colours")}, {id: "website", label: Eitr.I18n.tr("Eitr website")}]
                current: SettingsPalette.palette
                onChosen: value => SettingsPalette.select(value, view.live)
            }
        }
    }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Theme & Wallpaper")
        foreground: view.foreground
        visible: view.page === "appearance" && view.tab === "theme"
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-appearance-theme" }
            floatingLabel: Eitr.I18n.tr("Theme")
            helperText: Eitr.I18n.tr("Choose the colours used across your desktop.")
            width: Math.min(parent.width, 460)
            gold: SettingsInk.gold; background: SettingsInk.background;
            foreground: view.foreground
            choices: themeModel.items
            current: (themeModel.items.find(item => item.current) || {}).value || ""
            onChosen: value => {
                if (view.live) {
                    themeModel.selectedIndex = themeModel.items.findIndex(item => item.value === value);
                    themeModel.apply();
                }
            }
        }
        PanelButton {
            SettingsTarget { objectName: "setting-appearance-more-themes" }
            width: 180
            text: Eitr.I18n.tr("More themes")
            foreground: view.foreground
            onClicked: view.themesRequested()
        }
        SettingsText {
            text: Eitr.I18n.tr("Wallpaper")
            color: SettingsInk.gold
            font.family: SiteStyle.carved
        }
        SettingsText {
            text: Eitr.I18n.tr("Choose an image for your desktop.")
            font.pixelSize: 11
        }
        ToggleRow {
            width: parent.width
            text: Eitr.I18n.tr("Wallpaper per display")
            description: Eitr.I18n.tr("When on, a new wallpaper changes only the display you are using.")
            foreground: view.foreground
            accent: view.accent
            checked: wallpaperModel.perDisplay
            available: !wallpaperModel.busy
            onToggled: checked => { if (view.live) wallpaperModel.setPerDisplay(checked); }
        }
        SettingsText {
            text: Eitr.I18n.tr("Click a picture to preview it, then Apply or Cancel preview.")
            font.pixelSize: 11
        }
        Row {
            spacing: 8
            PanelButton {
                text: Eitr.I18n.tr("Apply")
                foreground: view.foreground
                available: wallpaperModel.previewing
                onClicked: if (view.live) { wallpaperModel.previewing = false; wallpaperModel.apply(); }
            }
            PanelButton {
                width: 156
                text: Eitr.I18n.tr("Cancel preview")
                foreground: view.foreground
                available: wallpaperModel.previewing
                onClicked: if (view.live) { wallpaperModel.previewing = false; wallpaperModel.cancelPreview(); }
            }
        }
        Flow {
            SettingsTarget { objectName: "setting-appearance-wallpaper" }

            width: parent.width
            spacing: 6
            Repeater {
                model: wallpaperModel.items
                Rectangle {
                    required property var modelData
                    required property int index
                    width: (parent.width - 12) / 3
                    height: width * 9 / 16
                    color: view.background
                    border.width: index === wallpaperModel.selectedIndex ? 2 : 0
                    border.color: SettingsInk.gold
                    Image {
                        anchors.fill: parent
                        anchors.margins: 3
                        source: modelData.image
                        sourceSize.width: 320
                        fillMode: Image.PreserveAspectCrop
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: if (view.live) {
                            wallpaperModel.selectedIndex = parent.index;
                            wallpaperModel.opened = true;
                            wallpaperModel.previewing = true;
                            wallpaperModel.previewSelection();
                        }
                    }
                }
            }
        }
    }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Typography")
        foreground: view.foreground
        visible: view.page === "appearance" && view.tab === "fonts"
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-appearance-fonts" }
            floatingLabel: Eitr.I18n.tr("Fonts")
            helperText: Eitr.I18n.tr("Set the font used by desktop text.")
            width: Math.min(parent.width, 460)
            gold: SettingsInk.gold; background: SettingsInk.background;
            foreground: view.foreground
            choices: fontHelper.summary.choices || []
            current: fontHelper.summary.current || ""
            onChosen: value => {
                if (view.live) {
                    fontHelper.change(["select", value]);
                }
            }
        }
    }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Cursor")
        foreground: view.foreground
        visible: view.page === "appearance" && view.tab === "fonts"
        // The outlined field with the pointer's preview beside it.
        Row {
            width: parent.width
            spacing: 14
            ChoiceDropdown {
                id: cursorFamily
                SettingsTarget { objectName: "setting-appearance-cursor-family" }
                floatingLabel: Eitr.I18n.tr("Cursor family")
                helperText: Eitr.I18n.tr("Choose the pointer shape.")
                width: Math.min(parent.width - (cursorSample.visible ? cursorSample.width + parent.spacing : 0), 460)
                gold: SettingsInk.gold; background: SettingsInk.background
                foreground: view.foreground
                choices: styleModel.cursorChoices.family
                current: (styleModel.cursorChoices.family.find(choice => choice.selected) || {}).id || ""
                onChosen: value => {
                    if (view.live) {
                        styleModel.run(styleModel.cursorWriteRef, ["python3", styleModel.cursorScript, "set", "family", value]);
                    }
                }
            }
            Image {
                id: cursorSample
                // Centred on the field itself, below the room kept for its raised label.
                y: cursorFamily.labelRoom + (48 - height) / 2
                visible: source.toString() !== ""
                width: Number((styleModel.cursorChoices.size.find(choice => choice.selected) || {}).id || 24)
                height: width
                source: styleModel.cursorPreview ? "file://" + styleModel.cursorPreview : ""
                fillMode: Image.PreserveAspectFit
                Accessible.name: Eitr.I18n.tr("Cursor preview")
            }
        }
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-appearance-cursor-colour" }
            floatingLabel: Eitr.I18n.tr("Cursor colour")
            helperText: Eitr.I18n.tr("Follow the theme or choose a fixed colour.")
            width: Math.min(parent.width, 460)
            gold: SettingsInk.gold; background: SettingsInk.background;
            foreground: view.foreground
            choices: styleModel.cursorChoices.color
            current: (styleModel.cursorChoices.color.find(choice => choice.selected) || {}).id || ""
            onChosen: value => {
                if (view.live) {
                    styleModel.run(styleModel.cursorWriteRef, ["python3", styleModel.cursorScript, "set", "color", value]);
                }
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-appearance-cursor-size" }
            text: Eitr.I18n.tr("Cursor size")
            description: Eitr.I18n.tr("Adjust the pointer size in pixels.")
            foreground: view.foreground
            ChoiceLevel {
                foreground: view.foreground
                accent: view.accent
                choices: styleModel.cursorChoices.size
                current: (styleModel.cursorChoices.size.find(choice => choice.selected) || {}).id || ""
                accessibleName: Eitr.I18n.tr("Cursor size")
                available: !styleModel.cursorWriteRef.running
                onChosen: value => styleModel.run(styleModel.cursorWriteRef, ["python3", styleModel.cursorScript, "set", "size", value])
            }
        }
    }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Terminal")
        foreground: view.foreground
        visible: view.page === "appearance" && view.tab === "terminal"
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-appearance-terminal" }
            floatingLabel: Eitr.I18n.tr("Terminal")
            helperText: Eitr.I18n.tr("Choose the app opened by the terminal shortcut.")
            width: Math.min(parent.width, 460)
            gold: SettingsInk.gold; background: SettingsInk.background;
            foreground: view.foreground
            choices: styleModel.terminalChoices
            current: styleModel.terminalChoice
            onChosen: value => {
                if (view.live) {
                    styleModel.run(styleModel.terminalWriteRef, ["python3", styleModel.terminalScript, "set", "terminal", value]);
                }
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-appearance-opacity" }
            text: Eitr.I18n.tr("Opacity")
            description: Eitr.I18n.tr("Adjust how much of the desktop shows through.")
            foreground: view.foreground
            ChoiceLevel {
                foreground: view.foreground
                accent: view.accent
                choices: styleModel.terminalAppearanceChoices["opacity"] || []
                current: styleModel.terminalAppearance["opacity"] || ""
                accessibleName: Eitr.I18n.tr("Opacity")
                available: !styleModel.terminalWriteRef.running
                onChosen: value => styleModel.run(styleModel.terminalWriteRef, ["python3", styleModel.terminalScript, "set", "opacity", value])
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-appearance-padding" }
            text: Eitr.I18n.tr("Padding")
            description: Eitr.I18n.tr("Set the space around terminal text.")
            foreground: view.foreground
            ChoiceLevel {
                foreground: view.foreground
                accent: view.accent
                choices: styleModel.terminalAppearanceChoices["padding"] || []
                current: styleModel.terminalAppearance["padding"] || ""
                accessibleName: Eitr.I18n.tr("Padding")
                available: !styleModel.terminalWriteRef.running
                onChosen: value => styleModel.run(styleModel.terminalWriteRef, ["python3", styleModel.terminalScript, "set", "padding", value])
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-appearance-blur-strength-shared" }
            text: Eitr.I18n.tr("Blur strength (shared)")
            description: Eitr.I18n.tr("Adjust blur across the desktop.")
            foreground: view.foreground
            ChoiceLevel {
                foreground: view.foreground
                accent: view.accent
                choices: styleModel.terminalAppearanceChoices["blur-strength"] || []
                current: styleModel.terminalAppearance["blur-strength"] || ""
                accessibleName: Eitr.I18n.tr("Blur strength (shared)")
                available: !styleModel.terminalWriteRef.running
                onChosen: value => styleModel.run(styleModel.terminalWriteRef, ["python3", styleModel.terminalScript, "set", "blur-strength", value])
            }
        }
        ToggleRow {
            SettingsTarget { objectName: "setting-appearance-blur" }
            text: Eitr.I18n.tr("Blur")
            description: Eitr.I18n.tr("Soften the desktop behind terminal windows.")
            foreground: view.foreground
            accent: view.accent
            checked: styleModel.terminalAppearance.blur === "on"
            onToggled: checked => {
                if (view.live) {
                    styleModel.run(styleModel.terminalWriteRef, ["python3", styleModel.terminalScript, "set", "blur", checked ? "on" : "off"]);
                }
            }
        }
        ToggleRow {
            SettingsTarget { objectName: "setting-appearance-cursor-fire" }
            text: Eitr.I18n.tr("Cursor Fire")
            description: Eitr.I18n.tr("Show a blazing trail behind the Kitty cursor.")
            foreground: view.foreground
            accent: view.accent
            checked: styleModel.cursorFire
            onToggled: checked => {
                if (view.live) {
                    styleModel.run(styleModel.fireWriteRef, ["python3", styleModel.effectsScript, "set", "cursor-fire", checked ? "on" : "off"]);
                }
            }
        }
    }
}
