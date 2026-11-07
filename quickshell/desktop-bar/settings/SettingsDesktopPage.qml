import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../ChoiceLists.js" as ChoiceLists

Flickable {
    id: view
    objectName: "settings-desktop-page"
    required property string page
    required property string title
    required property color foreground
    required property color background
    required property color accent
    signal tabRequested(string value)
    property string tab: "theme"
    property bool active: false
    property bool live: true
    property var notifications: null
    property bool idleEnabled: false
    signal themesRequested
    signal idleToggleRequested
    contentHeight: content.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    onPageChanged: {
        contentY = 0;
        Qt.callLater(refreshPage);
    }
    function refreshPage() {
        if (!active || !live)
            return;
        state.loadStyle();
        if (page === "appearance") {
            themeModel.open("theme", null);
            wallpaperModel.open("wallpaper", null);
        }
    }
    SettingsNotificationState {
        id: notificationState
        active: view.active && view.page === "notifications"
        live: view.live
    }
    SettingsStyleState {
        id: state
        objectName: "settings-style-state"
        active: view.active
        live: view.live
        property color foreground: view.foreground
        property color background: view.background
        property color accent: view.accent
        property var bar: barHelper.summary.current || ({})
        property string layout: bar.layout || "unified"
        property string barPosition: bar.edge || "top"
        property string appearance: bar.appearance || "solid"
        property string barScreens: bar.screens || "main"
        property string clockFormat: bar.clock || "12h"
        property string mediaStyle: bar.mediaStyle || "bars"
        property bool barAutoHide: bar.autohide === "yes"
        property bool barDock: bar.dock !== "no"
        property string workspaceStyle: workspaceHelper.summary.current
        function settingRequested(key, value) {
            barHelper.change(["set", key, value]);
        }
        function workspaceStyleRequested(value) {
            workspaceHelper.change([value]);
        }
    }
    SettingsHelper {
        id: barHelper
        objectName: "settings-bar-helper"
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/bar-settings.py")
        active: view.active && view.page === "bar"
        live: view.live
        schema: ({
                current: "object",
                choices: "object",
                available: "boolean"
            })
    }
    SettingsHelper {
        id: workspaceHelper
        objectName: "settings-workspace-helper"
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/workspace-style.py")
        active: view.active && view.page === "bar"
        live: view.live
    }
    SettingsHelper {
        id: fontHelper
        objectName: "settings-font-helper"
        script: Eitr.Paths.code("walker/scripts/actions/style/fonts.py")
        active: view.active && view.page === "appearance"
        live: view.live
    }
    SettingsAppearanceModel {
        id: themeModel
        objectName: "settings-theme-model"
        onApplied: view.refreshPage()
    }
    SettingsAppearanceModel {
        id: wallpaperModel
        objectName: "settings-wallpaper-model"
        onApplied: if (view.active && view.live)
            open("wallpaper", null)
    }
    onActiveChanged: if (active && live && page === "appearance") {
        themeModel.open("theme", null);
        wallpaperModel.open("wallpaper", null);
    }
    component Label: Text {
        color: view.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
        wrapMode: Text.WordWrap
        width: parent.width
    }
    Column {
        id: content
        width: view.width
        spacing: 18
        SettingsPageHeader {
            page: view.page
            foreground: view.foreground
        }
        TabStrip { foreground: SettingsPalette.foreground; gold: SettingsPalette.gold; carved: true;
            width: parent.width
            visible: view.page === "appearance"
            height: visible ? 42 : 0
            choices: [{id: "theme", label: Eitr.I18n.tr("Theme & Wallpaper")}, {id: "fonts", label: Eitr.I18n.tr("Fonts & Cursor")}, {id: "terminal", label: Eitr.I18n.tr("Terminal")}]
            current: view.tab
            onChosen: value => { view.tabRequested(value); view.contentY = 0; }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Settings colours")
            foreground: view.foreground
            visible: view.page === "appearance" && view.tab === "theme"
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
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Theme & Wallpaper")
            foreground: view.foreground
            visible: view.page === "appearance" && view.tab === "theme"
            ControlRow {
                text: Eitr.I18n.tr("Theme")
                description: Eitr.I18n.tr("Choose the colours used across your desktop.")
                foreground: view.foreground
                ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
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
            }
            PanelButton {
                width: 180
                text: Eitr.I18n.tr("More themes")
                foreground: view.foreground
                onClicked: view.themesRequested()
            }
            Label {
                text: Eitr.I18n.tr("Wallpaper")
                color: SettingsInk.gold
                font.family: SiteStyle.carved
            }
            Label {
                text: Eitr.I18n.tr("Choose an image for your desktop.")
                font.pixelSize: 11
            }
            Flow {
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
                        border.width: modelData.current ? 2 : 0
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
                                wallpaperModel.apply();
                            }
                        }
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Typography & Shape")
            foreground: view.foreground
            visible: view.page === "appearance" && view.tab === "fonts"
            ControlRow {
                text: Eitr.I18n.tr("Fonts")
                description: Eitr.I18n.tr("Set the font used by desktop text.")
                foreground: view.foreground
                ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
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
            Column {
                width: parent.width
                spacing: 8
                Label { text: Eitr.I18n.tr("Corners"); color: SettingsInk.gold }
                PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                    kind: "corners"
                    edge: state.barPosition
                    appearance: state.appearance
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
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Cursor")
            foreground: view.foreground
            visible: view.page === "appearance" && view.tab === "fonts"
            ControlRow {
                text: Eitr.I18n.tr("Cursor family")
                description: Eitr.I18n.tr("Choose the pointer shape.")
                foreground: view.foreground
                Row {
                    width: parent.width
                    spacing: 10
                    Image {
                        id: cursorSample
                        anchors.verticalCenter: parent.verticalCenter
                        visible: source.toString() !== ""
                        width: Number((state.cursorChoices.size.find(choice => choice.selected) || {}).id || 24)
                        height: width
                        source: state.cursorPreview ? "file://" + state.cursorPreview : ""
                        fillMode: Image.PreserveAspectFit
                        Accessible.name: Eitr.I18n.tr("Cursor preview")
                    }
                    ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
                        width: parent.width - (cursorSample.visible ? cursorSample.width + 10 : 0)
                        anchors.verticalCenter: parent.verticalCenter
                        foreground: view.foreground
                        choices: state.cursorChoices.family
                        current: (state.cursorChoices.family.find(choice => choice.selected) || {}).id || ""
                        onChosen: value => {
                            if (view.live) {
                                state.run(state.cursorWriteRef, ["python3", state.cursorScript, "set", "family", value]);
                            }
                        }
                    }
                }
            }
            ControlRow {
                text: Eitr.I18n.tr("Cursor colour")
                description: Eitr.I18n.tr("Follow the theme or choose a fixed colour.")
                foreground: view.foreground
                ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
                    foreground: view.foreground
                    choices: state.cursorChoices.color
                    current: (state.cursorChoices.color.find(choice => choice.selected) || {}).id || ""
                    onChosen: value => {
                        if (view.live) {
                            state.run(state.cursorWriteRef, ["python3", state.cursorScript, "set", "color", value]);
                        }
                    }
                }
            }
            ControlRow {
                text: Eitr.I18n.tr("Cursor size")
                description: Eitr.I18n.tr("Adjust the pointer size in pixels.")
                foreground: view.foreground
                ChoiceLevel {
                    foreground: view.foreground
                    accent: view.accent
                    choices: state.cursorChoices.size
                    current: (state.cursorChoices.size.find(choice => choice.selected) || {}).id || ""
                    accessibleName: Eitr.I18n.tr("Cursor size")
                    available: !state.cursorWriteRef.running
                    onChosen: value => state.run(state.cursorWriteRef, ["python3", state.cursorScript, "set", "size", value])
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Terminal")
            foreground: view.foreground
            visible: view.page === "appearance" && view.tab === "terminal"
            ControlRow {
                text: Eitr.I18n.tr("Terminal")
                description: Eitr.I18n.tr("Choose the app opened by the terminal shortcut.")
                foreground: view.foreground
                ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
                    foreground: view.foreground
                    choices: state.terminalChoices
                    current: state.terminalChoice
                    onChosen: value => {
                        if (view.live) {
                            state.run(state.terminalWriteRef, ["python3", state.terminalScript, "set", "terminal", value]);
                        }
                    }
                }
            }
            ControlRow {
                text: Eitr.I18n.tr("Opacity")
                description: Eitr.I18n.tr("Adjust how much of the desktop shows through.")
                foreground: view.foreground
                ChoiceLevel {
                    foreground: view.foreground
                    accent: view.accent
                    choices: state.terminalAppearanceChoices["opacity"] || []
                    current: state.terminalAppearance["opacity"] || ""
                    accessibleName: Eitr.I18n.tr("Opacity")
                    available: !state.terminalWriteRef.running
                    onChosen: value => state.run(state.terminalWriteRef, ["python3", state.terminalScript, "set", "opacity", value])
                }
            }
            ControlRow {
                text: Eitr.I18n.tr("Padding")
                description: Eitr.I18n.tr("Set the space around terminal text.")
                foreground: view.foreground
                ChoiceLevel {
                    foreground: view.foreground
                    accent: view.accent
                    choices: state.terminalAppearanceChoices["padding"] || []
                    current: state.terminalAppearance["padding"] || ""
                    accessibleName: Eitr.I18n.tr("Padding")
                    available: !state.terminalWriteRef.running
                    onChosen: value => state.run(state.terminalWriteRef, ["python3", state.terminalScript, "set", "padding", value])
                }
            }
            ControlRow {
                text: Eitr.I18n.tr("Blur strength (shared)")
                description: Eitr.I18n.tr("Adjust blur across the desktop.")
                foreground: view.foreground
                ChoiceLevel {
                    foreground: view.foreground
                    accent: view.accent
                    choices: state.terminalAppearanceChoices["blur-strength"] || []
                    current: state.terminalAppearance["blur-strength"] || ""
                    accessibleName: Eitr.I18n.tr("Blur strength (shared)")
                    available: !state.terminalWriteRef.running
                    onChosen: value => state.run(state.terminalWriteRef, ["python3", state.terminalScript, "set", "blur-strength", value])
                }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Blur")
                description: Eitr.I18n.tr("Soften the desktop behind terminal windows.")
                foreground: view.foreground
                accent: view.accent
                checked: state.terminalAppearance.blur === "on"
                onToggled: checked => {
                    if (view.live) {
                        state.run(state.terminalWriteRef, ["python3", state.terminalScript, "set", "blur", checked ? "on" : "off"]);
                    }
                }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Cursor Fire")
                description: Eitr.I18n.tr("Show a blazing trail behind the Kitty cursor.")
                foreground: view.foreground
                accent: view.accent
                checked: state.cursorFire
                onToggled: checked => {
                    if (view.live) {
                        state.run(state.fireWriteRef, ["python3", state.effectsScript, "set", "cursor-fire", checked ? "on" : "off"]);
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Bar")
            foreground: view.foreground
            visible: view.page === "bar"
            Column {
                width: parent.width
                spacing: 8
                Label { text: Eitr.I18n.tr("Layout"); color: SettingsInk.gold }
                PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                    kind: "layout"
                    edge: state.barPosition
                    appearance: state.appearance
                    compact: false
                    choices: ChoiceLists.barLayouts
                    current: state.layout
                    onChosen: value => {
                        if (view.live) {
                            state.settingRequested("layout", value);
                        }
                    }
                }
            }
            Column {
                width: parent.width
                spacing: 8
                Label { text: Eitr.I18n.tr("Position"); color: SettingsInk.gold }
                PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                    kind: "position"
                    edge: state.barPosition
                    appearance: state.appearance
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
                    current: state.barPosition
                    onChosen: value => {
                        if (view.live) {
                            state.settingRequested("edge", value);
                        }
                    }
                }
            }
            Column {
                width: parent.width
                spacing: 8
                Label { text: Eitr.I18n.tr("Appearance"); color: SettingsInk.gold }
                PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                    kind: "appearance"
                    edge: state.barPosition
                    appearance: state.appearance
                    compact: true
                    choices: ChoiceLists.barAppearances
                    current: state.appearance
                    onChosen: value => {
                        if (view.live) {
                            state.settingRequested("appearance", value);
                        }
                    }
                }
            }
            ControlRow {
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
                    current: state.barScreens
                    onChosen: value => {
                        if (view.live) {
                            state.settingRequested("screens", value);
                        }
                    }
                }
            }
            ControlRow {
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
                    current: state.clockFormat
                    onChosen: value => {
                        if (view.live) {
                            state.settingRequested("clock", value);
                        }
                    }
                }
            }
            Column {
                width: parent.width
                spacing: 8
                Label { text: Eitr.I18n.tr("Media style"); color: SettingsInk.gold }
                PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                    kind: "media"
                    edge: state.barPosition
                    appearance: state.appearance
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
                    current: state.mediaStyle
                    onChosen: value => {
                        if (view.live) {
                            state.settingRequested("mediaStyle", value);
                        }
                    }
                }
            }
            ControlRow {
                text: Eitr.I18n.tr("Blur strength (shared)")
                description: Eitr.I18n.tr("Adjust blur across the desktop.")
                foreground: view.foreground
                ChoiceLevel {
                    foreground: view.foreground
                    accent: view.accent
                    choices: state.terminalAppearanceChoices["blur-strength"] || []
                    current: state.terminalAppearance["blur-strength"] || ""
                    accessibleName: Eitr.I18n.tr("Blur strength (shared)")
                    onChosen: value => state.run(state.terminalWriteRef, ["python3", state.terminalScript, "set", "blur-strength", value])
                }
            }
            ControlRow {
                text: Eitr.I18n.tr("Workspace style")
                description: Eitr.I18n.tr("Choose how workspaces appear in the bar.")
                foreground: view.foreground
                ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
                    foreground: view.foreground
                    choices: workspaceHelper.summary.choices || []
                    current: state.workspaceStyle
                    onChosen: value => {
                        if (view.live) {
                            state.workspaceStyleRequested(value);
                        }
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Behavior")
            foreground: view.foreground
            visible: view.page === "bar"
            ToggleRow {
                text: Eitr.I18n.tr("Auto-hide")
                description: Eitr.I18n.tr("Hide the bar until you reach its screen edge.")
                foreground: view.foreground
                accent: view.accent
                checked: state.barAutoHide
                onToggled: checked => {
                    if (view.live) {
                        state.settingRequested("autohide", checked ? "yes" : "no");
                    }
                }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Dock")
                description: Eitr.I18n.tr("Show the application dock.")
                foreground: view.foreground
                accent: view.accent
                checked: state.barDock
                onToggled: checked => {
                    if (view.live) {
                        state.settingRequested("dock", checked ? "yes" : "no");
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
                        state.settingRequested("reduceMotion", checked ? "yes" : "no");
                    }
                }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Keep expanded")
                description: Eitr.I18n.tr("Keep the centered bar expanded.")
                foreground: view.foreground
                accent: view.accent
                checked: state.bar.pinned === "yes"
                onToggled: checked => {
                    if (view.live) {
                        state.settingRequested("pinned", checked ? "yes" : "no");
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Window gaps")
            foreground: view.foreground
            visible: view.page === "windows"
            Column {
                width: parent.width
                spacing: 8
                Label { text: Eitr.I18n.tr("Window gaps"); color: SettingsInk.gold }
                PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                    kind: "gaps"
                    edge: state.barPosition
                    appearance: state.appearance
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
            ToggleRow {
                text: Eitr.I18n.tr("Reduce motion")
                description: Eitr.I18n.tr("Minimise decorative movement.")
                foreground: view.foreground
                accent: view.accent
                checked: DesktopStyle.reduceMotion
                onToggled: checked => {
                    if (view.live) {
                        state.settingRequested("reduceMotion", checked ? "yes" : "no");
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Lockscreen")
            foreground: view.foreground
            visible: view.page === "lockscreen"
            Column {
                width: parent.width
                spacing: 8
                Label { text: Eitr.I18n.tr("Design"); color: SettingsInk.gold }
                PictureChoices { foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent; gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface; line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true;
                    kind: "lockscreen"
                    edge: state.barPosition
                    appearance: state.appearance
                    compact: false
                    choices: state.lockscreens
                    current: state.lockscreen
                    onChosen: value => {
                        if (view.live) {
                            state.run(state.lockscreenWriteRef, ["python3", state.lockscreenScript, "select", value]);
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
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Notifications")
            foreground: view.foreground
            visible: view.page === "notifications"
            ToggleRow {
                text: Eitr.I18n.tr("Do Not Disturb")
                description: Eitr.I18n.tr("Pause notification popups.")
                foreground: view.foreground
                accent: view.accent
                checked: !!view.notifications && view.notifications.doNotDisturb
                onToggled: checked => {
                    if (view.live) {
                        if (view.notifications)
                            view.notifications.toggleDnd();
                    }
                }
            }
            ToggleRow {
                text: Eitr.I18n.tr("Crash Notifications")
                description: Eitr.I18n.tr("Show help notifications when a program crashes.")
                foreground: view.foreground
                accent: view.accent
                checked: notificationState.enabled
                onToggled: checked => {
                    if (view.live) {
                        if (!notificationState.operation.running)
                            notificationState.operation.running = true;
                    }
                }
            }
            EventSoundSettings {
                width: parent.width
                foreground: view.foreground
                accent: view.accent
                live: view.live
                hasBattery: view.active && view.page === "notifications" && PowerService.battery.available
            }
        }
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
        Label {
            visible: view.page === "notifications" && notificationState.error !== ""
            text: notificationState.error
        }
        Label {
            visible: state.actionError !== ""
            text: state.actionError
        }
        Label {
            visible: themeModel.error !== ""
            text: themeModel.error
        }
        Label {
            visible: wallpaperModel.error !== ""
            text: wallpaperModel.error
        }
        Label {
            visible: fontHelper.error !== ""
            text: fontHelper.error
        }
        Label {
            visible: barHelper.error !== ""
            text: barHelper.error
        }
        Label {
            visible: workspaceHelper.error !== ""
            text: workspaceHelper.error
        }
        Label {
            visible: Object.keys(state.styleErrors).length > 0
            text: Object.values(state.styleErrors).join("\n")
        }
        PanelButton {
            objectName: "settings-page-handbook"
            width: 160
            text: Eitr.I18n.tr("Learn more")
            foreground: view.foreground
            onClicked: if (view.live)
                Quickshell.execDetached(["bash", Eitr.Paths.code("quickshell/desktop-bar/scripts/handbook.sh"), "open", view.page === "focus" ? "focus" : view.page === "bar" ? "desktop-bar" : view.page === "notifications" ? "control-center" : "appearance"])
        }
    }
}
