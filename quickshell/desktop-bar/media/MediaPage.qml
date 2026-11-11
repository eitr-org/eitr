import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Widgets
import Quickshell.Services.Mpris
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The Media panel and Drop's Media page: the cover in a circle, ringed by bars that
// follow the music; beside it the song, its lyrics when the player sends them, the
// controls and a plain progress bar. Lyrics come from the player, or from LRCLIB once the
// lyrics button has asked and been allowed.
Item {
    id: page
    required property var player
    required property color foreground
    required property color accent
    required property color background
    required property bool active
    readonly property bool playing: !!player && player.isPlaying
    readonly property real length: player && player.lengthSupported ? Math.max(1, player.length) : 0
    // The lyrics button first asks before any song is looked up online.
    property bool asking: false
    onActiveChanged: if (!active) asking = false
    required property var host
    LyricsSource { id: lyricsSource; host: page.host; player: page.player; active: page.active }
    property real position: 0
    implicitHeight: 290

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
        bars: 32
        frameRate: 30
        smoothing: true
        onSpectrumChanged: ring.requestPaint()
    }

    // The cover and its ring of bars, mirrored left and right so it stays balanced.
    Item {
        id: disc
        width: 268; height: page.height
        // A soft halo behind the ring, painted once (and again only when the colour changes).
        Canvas {
            id: halo
            anchors.centerIn: parent
            width: 268; height: 268
            readonly property color tint: page.accent
            onTintChanged: requestPaint()
            onPaint: {
                const context = getContext("2d");
                context.reset();
                const centre = width / 2, glow = context.createRadialGradient(centre, centre, ring.radius - 6, centre, centre, ring.radius + 44);
                glow.addColorStop(0, Qt.alpha(tint, 0));
                glow.addColorStop(0.35, Qt.alpha(tint, 0.18));
                glow.addColorStop(1, Qt.alpha(tint, 0));
                context.fillStyle = glow;
                context.fillRect(0, 0, width, height);
            }
            Component.onCompleted: requestPaint()
        }
        Canvas {
            id: ring
            anchors.centerIn: parent
            width: 268; height: 268
            readonly property real radius: 72
            readonly property int count: 64
            // Rounded stubs set against the cover; neighbouring bars rise together in smooth
            // clusters, at most about half the cover's radius.
            readonly property real reach: 34
            onPaint: {
                const context = getContext("2d");
                context.reset();
                const levels = audio.spectrum, centre = width / 2;
                // Each frame is scaled to its loudest band and the quieter ones pushed down, so
                // the ring pulses with the beat instead of standing at an even height.
                const sampled = Array.from({length: count}, (unused, index) => audio.active && levels.length ? levels[Math.floor(index * levels.length / count)] : 0);
                const peak = Math.max(0.3, ...sampled);
                const raw = sampled.map(level => Math.pow(level / peak, 1.8) * Math.min(1, peak * 1.6));
                context.strokeStyle = page.accent;
                context.lineCap = "round";
                context.lineWidth = 4.5;
                for (let index = 0; index < count; index++) {
                    const level = (raw[(index + count - 1) % count] + 2 * raw[index] + raw[(index + 1) % count]) / 4;
                    const angle = Math.PI / 2 + (index + 0.5) / count * Math.PI * 2;
                    const inner = radius + 5, outer = inner + 3 + Math.min(1, level * 1.1) * reach;
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
        MediaLyrics {
            id: lyrics
            anchors { top: song.bottom; topMargin: 10; bottom: controls.top; bottomMargin: 10 }
            width: parent.width
            visible: available && !page.asking
            text: lyricsSource.text; position: page.position
            foreground: page.foreground; accent: page.accent
        }
        Text {
            anchors.centerIn: lyrics
            width: lyrics.width
            horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
            visible: !lyrics.available && !page.asking
            text: lyricsSource.state === "loading" ? Eitr.I18n.tr("Looking for lyrics…")
                : lyricsSource.state === "none" ? Eitr.I18n.tr("No lyrics found for this song")
                : lyricsSource.state === "unavailable" ? Eitr.I18n.tr("Lyrics are unavailable right now")
                : page.player ? page.player.identity : ""
            color: page.foreground; opacity: 0.45
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            font.capitalization: lyricsSource.state === "" ? Font.AllUppercase : Font.MixedCase
            font.letterSpacing: lyricsSource.state === "" ? 1.4 : 0
        }
        // Asked once, before anything is sent anywhere.
        Column {
            anchors.centerIn: lyrics
            width: lyrics.width
            visible: page.asking
            spacing: 10
            Text {
                width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
                text: Eitr.I18n.tr("Find lyrics on LRCLIB? The title, artist and album of each song you play are sent to lrclib.net.")
                color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8
                PanelButton {
                    width: 84; height: 28; outlined: true
                    text: Eitr.I18n.tr("Not now"); foreground: page.foreground
                    onClicked: page.asking = false
                }
                PanelButton {
                    width: 84; height: 28; selected: true
                    text: Eitr.I18n.tr("Turn on"); foreground: page.foreground
                    onClicked: { page.asking = false; lyricsSource.setOnline(true); }
                }
            }
        }

        Row {
            id: controls
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: seek.top; anchors.bottomMargin: 10
            spacing: 6
            Repeater {
                model: [
                    {glyph: "󰒝", action: "shuffle"},
                    {glyph: "󰒮", action: "previous"},
                    {glyph: "", action: "togglePlaying"},
                    {glyph: "󰒭", action: "next"},
                    {glyph: "󰑖", action: "loop"},
                    {glyph: "󰍡", action: "lyrics"}
                ]
                Rectangle {
                    id: control
                    required property var modelData
                    readonly property bool main: modelData.action === "togglePlaying"
                    readonly property var player: page.player
                    readonly property bool available: !!player && player.canControl && (
                        modelData.action === "shuffle" ? player.shuffleSupported
                        : modelData.action === "loop" ? player.loopSupported
                        : modelData.action === "lyrics" ? true
                        : modelData.action === "previous" ? player.canGoPrevious
                        : modelData.action === "next" ? player.canGoNext : player.canTogglePlaying)
                    readonly property bool lit: !!player && (modelData.action === "shuffle" ? player.shuffle
                        : modelData.action === "loop" ? player.loopState !== MprisLoopState.None
                        : modelData.action === "lyrics" ? lyricsSource.online || page.asking : false)
                    width: main ? 46 : 32; height: width; radius: main ? DesktopStyle.radius(14) : width / 2
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
                            if (control.modelData.action === "lyrics") {
                                if (lyricsSource.online) lyricsSource.setOnline(false);
                                else page.asking = !page.asking;
                            } else if (control.modelData.action === "shuffle") player.shuffle = !player.shuffle;
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
