import ".."
import QtQuick
import "../ChoiceLists.js" as ChoiceLists

// The five bar layouts side by side with their names: the compact picture
// cards of Settings > Desktop Bar, unselected. Hovering a card unfolds its layout.
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
