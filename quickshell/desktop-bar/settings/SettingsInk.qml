pragma Singleton
import ".."
import QtQuick
QtObject {
    property color background: SiteStyle.card
    readonly property color gold: SettingsPalette.gold
    readonly property string runes: "Noto Sans Runic"
}
