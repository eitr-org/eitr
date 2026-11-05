import ".."
import QtQuick

ThemedPopup {
    id: menu
    required property var player
    // The player is between songs: keep showing the last one.
    property bool hold: false
    centered: true
    paddingScale: 0.5
    backdropInset: 3
    implicitWidth: 380
    implicitHeight: card.implicitHeight + verticalContentInset
    // The cover fills the whole sheet, edge to edge, darkened so the controls stay readable.
    backdrop: Item {
        anchors.fill: parent
        visible: card.hasCover
        Image {
            anchors.fill: parent
            source: card.coverSource
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            sourceSize.width: Math.ceil(width * Screen.devicePixelRatio)
        }
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0; color: Qt.rgba(0, 0, 0, 0.45) }
                GradientStop { position: 1; color: Qt.rgba(0, 0, 0, 0.7) }
            }
        }
    }
    MediaCard {
        id: card
        anchors.fill: parent
        ownCover: false
        player: menu.player; hold: menu.hold; active: menu.opened
        foreground: menu.foreground; accent: menu.accent
    }
}
