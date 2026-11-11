import "../.."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Widgets
import Quickshell.Services.Mpris
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle

// Drop's Media page: the cover in a circle, ringed by bars that
// follow the music; beside it the song, its lyrics when the player sends them, the
// controls and a plain progress bar.
Item {
    id: page
    required property var player
    required property color foreground
    required property color accent
    required property color background
    required property bool active
    readonly property bool playing: !!player && player.isPlaying
    readonly property real length: player && player.lengthSupported ? Math.max(1, player.length) : 0
    readonly property string lyricsText: player && player.metadata ? String(player.metadata["xesam:asText"] || "") : ""
    property real position: 0
    implicitHeight: 268

    function timeLabel(seconds) {
        const value = Math.max(0, Math.floor(seconds || 0));
        return Math.floor(value / 60) + ":" + String(value % 60).padStart(2, "0");
    }
    Timer {
        interval: 250; repeat: true; running: page.active && !!page.player; triggeredOnStart: true
        onTriggered: if (!seek.pressed) page.position = page.player.position
    }
    SpectrumConsumer {
        id: audio
        active: page.active && page.playing
        bars: 48
        frameRate: 30
        smoothing: true
        onSpectrumChanged: ring.requestPaint()
    }

    // The cover and its ring of bars, mirrored left and right so it stays balanced.
    Item {
        id: disc
        width: 268; height: page.height
        Canvas {
            id: ring
            anchors.centerIn: parent
            width: 268; height: 268
            readonly property real radius: 56
            // Bars reach up to their full length; quiet bands are lifted a little so the ring
            // moves with the song rather than only on its loudest beats.
            readonly property real reach: 66
            // The bands sit around the circle in a fixed scattered order, so neighbouring bars
            // differ and the ring looks lively instead of a smooth bass-to-treble sweep.
            readonly property var order: {
                const positions = Array.from({length: 48}, (unused, index) => index);
                let seed = 7;
                for (let index = positions.length - 1; index > 0; index--) {
                    seed = (seed * 9301 + 49297) % 233280;
                    const other = Math.floor(seed / 233280 * (index + 1));
                    [positions[index], positions[other]] = [positions[other], positions[index]];
                }
                return positions;
            }
            onPaint: {
                const context = getContext("2d");
                context.reset();
                const levels = audio.spectrum, count = order.length, centre = width / 2;
                context.strokeStyle = page.accent;
                context.lineCap = "round";
                context.lineWidth = 6;
                for (let index = 0; index < count; index++) {
                    const raw = audio.active && levels.length ? levels[Math.min(levels.length - 1, order[index])] : 0;
                    const level = Math.min(1, Math.pow(raw, 0.8) * 1.25);
                    const angle = -Math.PI / 2 + (index + 0.5) / count * Math.PI * 2;
                    const inner = radius + 9, outer = inner + 2 + level * reach;
                    context.beginPath();
                    context.moveTo(centre + Math.cos(angle) * inner, centre + Math.sin(angle) * inner);
                    context.lineTo(centre + Math.cos(angle) * outer, centre + Math.sin(angle) * outer);
                    context.stroke();
                }
            }
            Component.onCompleted: requestPaint()
        }
        ClippingRectangle {
            id: cover
            anchors.centerIn: parent
            width: 2 * ring.radius; height: width; radius: width / 2
            color: Qt.alpha(page.foreground, 0.08)
            Image {
                id: art
                anchors.fill: parent
                source: page.player ? page.player.trackArtUrl : ""
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                sourceSize.width: 2 * width
            }
            Text {
                anchors.centerIn: parent
                visible: art.status !== Image.Ready
                text: "󰝚"; color: page.accent
                font.family: DesktopFonts.family; font.pixelSize: 48
            }
        }
    }

    Item {
        id: side
        x: disc.width + 10; width: page.width - x - 6; height: page.height
        Column {
            id: song
            width: parent.width; y: 6
            spacing: 2
            Text {
                width: parent.width; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; textFormat: Text.PlainText
                text: page.player ? page.player.trackTitle || page.player.identity : ""
                color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 16; font.weight: Font.Bold
            }
            Text {
                width: parent.width; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; textFormat: Text.PlainText
                text: page.player ? [page.player.trackArtist, page.player.trackAlbum].filter(Boolean).join(" · ") : ""
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
        }
        DropLyrics {
            id: lyrics
            anchors { top: song.bottom; topMargin: 10; bottom: controls.top; bottomMargin: 10 }
            width: parent.width
            visible: available
            text: page.lyricsText; position: page.position
            foreground: page.foreground; accent: page.accent
        }
        Text {
            anchors.centerIn: lyrics
            visible: !lyrics.available
            text: page.player ? page.player.identity : ""
            color: page.foreground; opacity: 0.4
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            font.capitalization: Font.AllUppercase; font.letterSpacing: 1.4
        }

        Row {
            id: controls
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: seek.top; anchors.bottomMargin: 12
            spacing: 14
            Repeater {
                model: [
                    {glyph: "󰒝", action: "shuffle"},
                    {glyph: "󰒮", action: "previous"},
                    {glyph: "", action: "togglePlaying"},
                    {glyph: "󰒭", action: "next"},
                    {glyph: "󰑖", action: "loop"}
                ]
                Rectangle {
                    id: control
                    required property var modelData
                    readonly property bool main: modelData.action === "togglePlaying"
                    readonly property var player: page.player
                    readonly property bool available: !!player && player.canControl && (
                        modelData.action === "shuffle" ? player.shuffleSupported
                        : modelData.action === "loop" ? player.loopSupported
                        : modelData.action === "previous" ? player.canGoPrevious
                        : modelData.action === "next" ? player.canGoNext : player.canTogglePlaying)
                    readonly property bool lit: !!player && (modelData.action === "shuffle" ? player.shuffle
                        : modelData.action === "loop" ? player.loopState !== MprisLoopState.None : false)
                    width: main ? 48 : 34; height: width; radius: main ? DesktopStyle.radius(14) : width / 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: main ? page.accent : Qt.alpha(page.foreground, press.containsMouse && available ? 0.12 : 0)
                    opacity: available ? 1 : 0.35
                    scale: press.pressed && available ? 0.9 : 1
                    Behavior on scale { NumberAnimation { duration: DesktopStyle.motionDuration(140); easing.type: Easing.OutBack } }
                    Text {
                        anchors.centerIn: parent
                        text: control.main ? (page.playing ? "󰏤" : "󰐊")
                            : control.modelData.action === "loop" && control.player && control.player.loopState === MprisLoopState.Track ? "󰑘" : control.modelData.glyph
                        color: control.main ? PanelStyle.readableInk(page.accent, page.foreground, page.background)
                            : control.lit ? page.accent : page.foreground
                        font.family: DesktopFonts.family; font.pixelSize: control.main ? 22 : 17
                    }
                    MouseArea {
                        id: press
                        anchors.fill: parent
                        hoverEnabled: true; enabled: control.available; cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            const player = control.player;
                            if (control.modelData.action === "shuffle") player.shuffle = !player.shuffle;
                            else if (control.modelData.action === "loop")
                                player.loopState = player.loopState === MprisLoopState.None ? MprisLoopState.Playlist
                                    : player.loopState === MprisLoopState.Playlist ? MprisLoopState.Track : MprisLoopState.None;
                            else player[control.modelData.action]();
                        }
                    }
                }
            }
        }

        // A plain progress bar: drag or click to seek.
        Item {
            id: seek
            anchors.bottom: parent.bottom; anchors.bottomMargin: 4
            width: parent.width; height: 30
            readonly property bool pressed: drag.pressed
            property real dragValue: 0
            readonly property bool canSeek: !!page.player && page.player.canControl && page.player.canSeek && page.player.positionSupported && page.length > 0
            readonly property real fraction: page.length > 0 ? Math.max(0, Math.min(1, (pressed ? dragValue : page.position) / page.length)) : 0
            Rectangle {
                id: track
                y: 4; width: parent.width; height: 4; radius: 2
                color: Qt.alpha(page.foreground, 0.15)
                Rectangle { width: parent.width * seek.fraction; height: parent.height; radius: 2; color: page.accent }
                Rectangle {
                    x: parent.width * seek.fraction - width / 2; anchors.verticalCenter: parent.verticalCenter
                    width: drag.containsMouse || seek.pressed ? 12 : 8; height: width; radius: width / 2
                    color: page.accent
                    Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
                }
            }
            Text {
                y: 14; text: page.timeLabel(seek.pressed ? seek.dragValue : page.position)
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: 11; font.features: PanelStyle.tabularFigures
            }
            Text {
                y: 14; anchors.right: parent.right
                text: page.length > 0 ? page.timeLabel(page.length) : "--:--"
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: 11; font.features: PanelStyle.tabularFigures
            }
            MouseArea {
                id: drag
                width: parent.width; height: 14
                enabled: seek.canSeek; hoverEnabled: true
                cursorShape: seek.canSeek ? Qt.PointingHandCursor : Qt.ArrowCursor
                preventStealing: true
                function valueAt(mouseX) { return Math.max(0, Math.min(1, mouseX / width)) * page.length; }
                onPressed: function(mouse) { seek.dragValue = valueAt(mouse.x); }
                onPositionChanged: function(mouse) { if (pressed) seek.dragValue = valueAt(mouse.x); }
                onReleased: { page.player.position = seek.dragValue; page.position = seek.dragValue; }
            }
        }
    }
}
