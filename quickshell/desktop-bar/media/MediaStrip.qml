import ".."
import Eitr as Eitr
import Quickshell
import QtQuick
import Quickshell.Services.Mpris
import "../MediaModel.js" as MediaModel

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
    // Between songs a player clears its track, and Chromium even drops its player and
    // registers a new one. The strip (and a media panel attached to it) stays for that
    // gap instead of vanishing on Next or Previous.
    // Shown at once when a player appears; hidden only after it has been gone for 3 s.
    property bool present: false
    readonly property bool between: present && !player
    onPlayerChanged: {
        if (player) { gap.stop(); present = true; }
        else if (present) gap.restart();
    }
    Component.onCompleted: present = !!player
    Timer { id: gap; interval: 3000; onTriggered: media.present = !!media.player }
    readonly property bool playing: !!player && player.isPlaying
    readonly property string title: player ? [player.trackArtist, player.trackTitle].filter(Boolean).join(" - ") || player.identity : ""
    property string mediaStyle: "bars"
    // The bar's host, for the online lyrics setting.
    property var host: null
    // Dragging the wave to the left swaps it for the line being sung; only dragging the line
    // either way swaps it back (pausing or changing song keeps it), or the player going away.
    property bool lyricsOpen: false
    onPresentChanged: if (!present) lyricsOpen = false
    readonly property real lyricsWidth: Math.max(80, Math.min(360, availableWidth - controls.width - indicatorSpacing, lyric.naturalWidth + 8))
    property real indicatorReveal: lyricsOpen ? lyricsWidth : playbackIndicator.width
    Behavior on indicatorReveal { NumberAnimation { duration: DesktopStyle.motionDuration(240); easing.type: Easing.OutCubic } }
    property bool audioEnabled: true
    readonly property bool hasAudioFrame: playbackIndicator.hasAudioFrame
    readonly property var levels: playbackIndicator.levels
    readonly property bool cavaFailed: SpectrumProvider.failed
    signal detailsRequested()

    visible: present && availableWidth >= controls.width + indicatorSpacing + playbackIndicator.width
    width: visible ? controls.width + indicatorSpacing + indicatorReveal : 0
    height: 24

    Row {
        id: controls
        x: media.indicatorReveal + media.indicatorSpacing
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
        visible: !media.lyricsOpen && media.indicatorReveal <= width + 0.5
        onDraggedLeft: if (media.host && media.playing) media.lyricsOpen = true
        style: media.mediaStyle
        playing: media.playing
        active: media.audioEnabled && media.visible && media.enabled && media.opacity > 0
        foreground: media.foreground
        background: media.background
        title: media.title
        onDetailsRequested: media.detailsRequested()
    }

    LyricLine {
        id: lyric
        visible: media.lyricsOpen
        width: media.indicatorReveal; height: parent.height
        clip: true
        host: media.host; player: media.player; active: media.lyricsOpen
        foreground: media.foreground
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            property real pressX: 0
            property bool dragged: false
            onPressed: mouse => { pressX = mouse.x; dragged = false; }
            onPositionChanged: mouse => {
                if (!pressed || dragged || Math.abs(mouse.x - pressX) < 16) return;
                dragged = true;
                media.lyricsOpen = false;
            }
            onClicked: if (!dragged) media.detailsRequested()
        }
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
        readonly property bool motion: !DesktopStyle.reduceMotion
        // A press flashes a soft light behind the icon, which sinks and springs back.
        Rectangle {
            id: flash
            anchors.centerIn: parent
            width: 22 * spread; height: width; radius: width / 2
            property real spread: 0
            color: Qt.alpha(media.foreground, 0.3)
            opacity: 0
            ParallelAnimation {
                id: flashAnimation
                NumberAnimation { target: flash; property: "spread"; from: 0.3; to: 1; duration: 360; easing.type: Easing.OutCubic }
                NumberAnimation { target: flash; property: "opacity"; from: 1; to: 0; duration: 460; easing.type: Easing.InQuad }
            }
        }
        Item {
            anchors.fill: parent
            scale: controlMouse.pressed && control.available ? 0.8 : 1
            Behavior on scale { enabled: control.motion; NumberAnimation { duration: 160; easing.type: Easing.OutBack } }
            Text {
                id: glyph
                anchors.fill: parent
                property string shown: control.text
                text: shown
                color: media.foreground
                opacity: control.available ? 1 : 0.4
                font.family: DesktopFonts.family
                font.pixelSize: 15
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                // Play and pause swap by shrinking away while the new icon grows in.
                SequentialAnimation {
                    id: swap
                    NumberAnimation { target: glyph; property: "scale"; to: 0.3; duration: 90; easing.type: Easing.InQuad }
                    ScriptAction { script: glyph.shown = control.text }
                    NumberAnimation { target: glyph; property: "scale"; from: 0.3; to: 1; duration: 180; easing.type: Easing.OutBack }
                }
            }
        }
        onTextChanged: {
            if (!motion || !visible) { swap.stop(); glyph.shown = text; return; }
            swap.restart();
        }
        MouseArea {
            id: controlMouse
            anchors.fill: parent; hoverEnabled: true; enabled: control.available; cursorShape: Qt.PointingHandCursor
            onPressed: if (control.motion) flashAnimation.restart()
            onClicked: control.triggered()
        }
        BarTooltip { target: control; hovered: controlMouse.containsMouse; text: control.tooltip; foreground: media.foreground; background: media.background }
    }
}
