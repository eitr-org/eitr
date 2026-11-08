import ".."
import QtQuick
import Eitr as Eitr
import "../ChoiceLists.js" as ChoiceLists

// Window gaps and corners side by side: the compact picture cards of Settings > Windows,
// with the current choices marked.
Column {
    id: figure
    readonly property real minimumWidth: 480
    spacing: 8
    component Choices: PictureChoices {
        width: figure.width
        foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent
        gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface
        line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true
        compact: true
    }
    component Heading: Text {
        color: SettingsInk.gold
        font.family: SiteStyle.carved; font.pixelSize: 12; font.capitalization: Font.AllUppercase; font.letterSpacing: 1.3
    }
    Heading { text: Eitr.I18n.tr("Window gaps") }
    Choices { kind: "gaps"; choices: ChoiceLists.windowGaps; current: DesktopStyle.gaps }
    Item { width: 1; height: 6 }
    Heading { text: Eitr.I18n.tr("Corners") }
    Choices { kind: "corners"; choices: DesktopStyle.options; current: DesktopStyle.corners }
}
