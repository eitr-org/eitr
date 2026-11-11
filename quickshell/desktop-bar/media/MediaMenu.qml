import ".."
import QtQuick

// The Media panel: the same page as Drop's dashboard (the cover ringed by bars that follow the
// music, the song, its lyrics, controls and progress).
ThemedPopup {
    id: menu
    required property var player
    required property var host
    centered: true
    implicitWidth: 580
    implicitHeight: page.implicitHeight + verticalContentInset
    MediaPage {
        id: page
        anchors.fill: parent
        player: menu.player; host: menu.host
        // The music's bars and lyric lookups start once the panel has unfolded.
        active: menu.opened && menu.revealProgress >= 1
        foreground: menu.foreground; accent: menu.accent; background: menu.background
    }
}
