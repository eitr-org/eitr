import Eitr as Eitr
import Quickshell
import "AudioLevels.js" as AudioLevels
import QtQuick
import "PanelStyle.js" as PanelStyle
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
    property real pulse: 0
    property bool audioEnabled: true
    readonly property bool audioActive: audioEnabled && visible && enabled && opacity > 0 && playing
    readonly property bool cavaFailed: SpectrumProvider.failed
    readonly property bool hasAudioFrame: audioActive && SpectrumProvider.hasFrame
    readonly property var levels: audioActive ? audio.spectrum : [0, 0, 0, 0]
    SpectrumConsumer { id: audio; active: media.audioActive; bars: 4; frameRate: 30; smoothing: false }
    signal detailsRequested()

    visible: player !== null && availableWidth >= controls.width + indicatorSpacing + playbackIndicator.width
    width: visible ? controls.width + indicatorSpacing + playbackIndicator.width : 0
    height: 24

    Row {
        id: controls
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
    Item {
        id: playbackIndicator
        anchors.right: parent.right
        width: 14
        height: parent.height
        MouseArea {
            id: indicatorMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: function(mouse) {
                if (mouse.button === Qt.RightButton)
                    Quickshell.execDetached(["bash", Eitr.Paths.code("walker/scripts/actions/tools/music-visualizer.sh")]);
                else
                    media.detailsRequested();
            }
        }
        BarTooltip {
            target: playbackIndicator
            hovered: indicatorMouse.containsMouse
            text: media.title
            foreground: media.foreground
            background: media.background
        }
        Row {
            anchors.centerIn: parent
            height: 14
            spacing: 1
            Repeater {
                model: 4
                Rectangle {
                    required property int index
                    anchors.verticalCenter: parent.verticalCenter
                    width: 2.75
                    height: !media.playing ? 3 : media.hasAudioFrame ? AudioLevels.height(media.levels[index]) : 4 + (Math.sin(media.pulse + index * 1.7) + 1) * 4
                    Behavior on height { NumberAnimation { duration: 70 } }
                    radius: 1
                    color: media.foreground
                    opacity: media.playing ? 1 : 0.55
                }
            }
        }
    }
    NumberAnimation on pulse { from: 0; to: Math.PI * 2; duration: 1500; loops: Animation.Infinite; running: media.audioActive && !media.hasAudioFrame }

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
