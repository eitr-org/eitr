import ".."
import QtQuick
import "../ChoiceLists.js" as ChoiceLists

// Layout cards share Settings geometry and wrap to fit the reader.
Item {
    id: figure
    readonly property real minimumWidth: 560
    implicitHeight: cards.height
    PictureChoices {
        id: cards
        width: figure.width
        foreground: SettingsPalette.foreground; background: SettingsPalette.background; accent: SettingsPalette.accent
        gold: SettingsPalette.gold; raised: SettingsPalette.raised; surface: SettingsPalette.surface
        line: SettingsPalette.line; muted: SettingsPalette.muted; carved: true
        kind: "layout"
        compact: true
        choices: ChoiceLists.barLayouts
    }
}
