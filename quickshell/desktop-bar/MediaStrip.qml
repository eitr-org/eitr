import Eitr as Eitr
import Quickshell
import QtQuick
import "PanelStyle.js" as PanelStyle
import Quickshell.Services.Mpris
import "MediaModel.js" as MediaModel

Item {
    id: media
    required property color foreground
    required property color background
    property real availableWidth: 260
    property var players: Mpris.players.values
    readonly property var eligiblePlayers: players.filter(p => p && MediaModel.eligible(p))
    readonly property var player: eligiblePlayers.find(p => p.isPlaying) || eligiblePlayers[0] || null
    readonly property bool playing: !!player && player.isPlaying
    readonly property string title: player ? [player.trackArtist, player.trackTitle].filter(Boolean).join(" - ") || player.identity : ""
    property real pulse: 0
    signal detailsRequested()

    visible: player !== null && availableWidth >= controls.width + 20
    width: visible ? controls.width + 20 : 0
    height: 24

    Row {
        id: controls
        height: parent.height
        spacing: 1
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
            spacing: 2
            Repeater {
                model: 3
                Rectangle {
                    required property int index
                    anchors.verticalCenter: parent.verticalCenter
                    width: 3
                    height: media.playing ? 4 + (Math.sin(media.pulse + index * 1.7) + 1) * 4 : 3
                    radius: 1
                    color: media.foreground
                    opacity: media.playing ? 1 : 0.55
                }
            }
        }
    }
    NumberAnimation on pulse { from: 0; to: Math.PI * 2; duration: 1500; loops: Animation.Infinite; running: media.visible && media.playing }

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
