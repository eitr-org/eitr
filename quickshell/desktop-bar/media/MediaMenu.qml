import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

ThemedPopup {
    id: menu
    required property var player
    centered: true
    implicitWidth: 450
    implicitHeight: 214 + verticalContentInset
    PanelHeading { id: heading; width: parent.width; text: Eitr.I18n.tr("Media"); foreground: menu.foreground; accent: menu.accent; rune: "media" }
    MediaCard {
        anchors { top: heading.bottom; topMargin: 12; left: parent.left; right: parent.right; bottom: parent.bottom }
        player: menu.player; active: menu.opened
        cardBackground: false
        foreground: menu.foreground; accent: menu.accent
    }
}
