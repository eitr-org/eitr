import Eitr as Eitr
import Quickshell
import QtQuick
import Quickshell.Services.Mpris
import "MediaModel.js" as MediaModel

Item {
    id: media
    required property color foreground
    required property color background
    property real availableWidth: 260
    property real itemSpacing: 1
    property real indicatorSpacing: 6
    property var players: Mpris.players.values
    readonly property var eligiblePlayers: players.filter(player => player && MediaModel.eligible(player))
    readonly property var player: eligiblePlayers.find(player => player.isPlaying) || eligiblePlayers[0] || null
    readonly property bool playing: !!player && player.isPlaying
    readonly property string title: player ? [player.trackArtist, player.trackTitle].filter(Boolean).join(" - ") || player.identity : ""
    property string mediaStyle: "bars"
    property bool audioEnabled: true
    readonly property bool hasAudioFrame: playbackIndicator.hasAudioFrame
    readonly property var levels: playbackIndicator.levels
    readonly property bool cavaFailed: SpectrumProvider.failed
    signal detailsRequested()

    visible: player !== null && availableWidth >= controls.width + indicatorSpacing + playbackIndicator.width
    width: visible ? controls.width + indicatorSpacing + playbackIndicator.width : 0
    height: 24

    Row {
        id: controls
        x: playbackIndicator.width + media.indicatorSpacing
        height: parent.height
        spacing: media.itemSpacing
        MediaControl {
            text: "󰒮"
            tooltip: Eitr.I18n.tr("Previous")
            available: !!media.player && media.player.canControl && media.player.canGoPrevious
            onTriggered: media.player.previous()
        }
        MediaControl {
            text: media.playing ? "󰏤" : "󰐊"
            tooltip: media.playing ? Eitr.I18n.tr("Pause") : Eitr.I18n.tr("Play")
            available: !!media.player && media.player.canControl && media.player.canTogglePlaying
            onTriggered: media.player.togglePlaying()
        }
        MediaControl {
            text: "󰒭"
            tooltip: Eitr.I18n.tr("Next")
            available: !!media.player && media.player.canControl && media.player.canGoNext
            onTriggered: media.player.next()
        }
    }
    MediaIndicator {
        id: playbackIndicator
        style: media.mediaStyle
        playing: media.playing
        active: media.audioEnabled && media.visible && media.enabled && media.opacity > 0
        foreground: media.foreground
        background: media.background
        title: media.title
        onDetailsRequested: media.detailsRequested()
    }

    component MediaControl: Item {
        id: control
        required property string text
        required property string tooltip
        property bool available: true
        signal triggered()
        width: 18
        height: 24
        activeFocusOnTab: true
        enabled: available
        Keys.onReturnPressed: if (available) triggered()
        Keys.onSpacePressed: if (available) triggered()
        Text {
            anchors.fill: parent
            text: control.text
            color: media.foreground
            opacity: control.available ? 1 : 0.4
            font.family: DesktopFonts.family
            font.pixelSize: 15
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        MouseArea { id: controlMouse; anchors.fill: parent; hoverEnabled: true; enabled: control.available; cursorShape: Qt.PointingHandCursor; onClicked: control.triggered() }
        BarTooltip { target: control; hovered: controlMouse.containsMouse; text: control.tooltip; foreground: media.foreground; background: media.background }
    }
}
