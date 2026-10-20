import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle

Rectangle {
    id: card
    required property var player
    required property color foreground
    required property color accent
    property bool active: false
    property bool cardBackground: true
    property bool compact: false
    property real position: 0
    implicitHeight: compact ? 150 : 170
    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
    color: cardBackground ? Qt.alpha(foreground, 0.06) : "transparent"
    function timeLabel(seconds) {
        let value = Math.max(0, Math.floor(seconds || 0));
        return Math.floor(value / 60) + ":" + String(value % 60).padStart(2, "0");
    }
    Timer {
        interval: 1000; repeat: true; running: card.active && !!card.player
        triggeredOnStart: true
        onTriggered: card.position = card.player.position
    }
    Rectangle {
        x: 12; y: 12; width: card.compact ? 64 : 76; height: width
        radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(card.foreground, 0.08)
        Text { anchors.centerIn: parent; text: "󰝚"; color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: 30 }
        Image { anchors.fill: parent; source: card.player ? card.player.trackArtUrl : ""; fillMode: Image.PreserveAspectFit; asynchronous: true }
    }
    Column {
        x: card.compact ? 90 : 102; y: card.compact ? 12 : 16; width: parent.width - x - 14; spacing: card.compact ? 6 : 8
        Text { width: parent.width; text: card.player ? card.player.trackTitle || card.player.identity : Eitr.I18n.tr("No media playing"); elide: Text.ElideRight; color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: card.compact ? 12 : PanelStyle.bodySize; font.bold: true }
        Text { width: parent.width; text: card.player ? card.player.trackArtist : ""; elide: Text.ElideRight; color: card.foreground; opacity: 0.65; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
        Row {
            spacing: 8
            PanelButton { text: "󰒮"; icon: true; height: card.compact ? 28 : 32; iconSize: card.compact ? 16 : 18; foreground: card.foreground; available: !!card.player && card.player.canControl && card.player.canGoPrevious; onClicked: card.player.previous() }
            PanelButton { text: card.player && card.player.isPlaying ? "󰏤" : "󰐊"; icon: true; height: card.compact ? 28 : 32; iconSize: card.compact ? 16 : 18; foreground: card.foreground; available: !!card.player && card.player.canControl && card.player.canTogglePlaying; onClicked: card.player.togglePlaying() }
            PanelButton { text: "󰒭"; icon: true; height: card.compact ? 28 : 32; iconSize: card.compact ? 16 : 18; foreground: card.foreground; available: !!card.player && card.player.canControl && card.player.canGoNext; onClicked: card.player.next() }
        }
    }
    PanelSlider {
        id: progress
        x: 12; y: card.compact ? 88 : 100; width: parent.width - 24
        foreground: card.foreground; accent: card.accent
        from: 0; to: card.player && card.player.lengthSupported ? Math.max(1, card.player.length) : 1
        enabled: !!card.player && card.player.canControl && card.player.canSeek && card.player.positionSupported && card.player.lengthSupported
        Binding { target: progress; property: "value"; value: card.position; when: !progress.pressed }
        onMoved: card.player.position = value
    }
    Text { x: 14; y: card.compact ? 118 : 136; text: card.timeLabel(card.position); color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    Text { anchors.right: parent.right; anchors.rightMargin: 14; y: card.compact ? 118 : 136; text: card.player && card.player.lengthSupported ? card.timeLabel(card.player.length) : "--:--"; color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
}
