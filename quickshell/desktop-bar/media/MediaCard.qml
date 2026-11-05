import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

// The playing track over its cover: player name, title and artist, a seek bar whose
// played part carries waves from the real audio spectrum, and previous/play/next.
Rectangle {
    id: card
    required property var player
    required property color foreground
    required property color accent
    property bool active: false
    property bool compact: false
    // Draw the cover behind the card; off when the panel already fills its sheet with it.
    property bool ownCover: true
    readonly property alias coverSource: cover.source
    property real position: 0
    readonly property real unit: compact ? 0.82 : 1
    readonly property bool hasCover: cover.status === Image.Ready
    // Text and controls sit on the darkened cover; without one they follow the theme.
    readonly property color ink: hasCover ? "white" : foreground
    readonly property bool playing: !!player && player.isPlaying
    // Between songs the player can vanish for a moment; with hold set the card keeps
    // showing the last song instead of flashing "No media playing".
    property bool hold: false
    readonly property var live: player ? {
        identity: player.identity,
        line: [player.trackTitle || player.identity, player.trackArtist].filter(part => !!part).join("  •  "),
        cover: player.trackArtUrl,
        length: player.lengthSupported ? Math.max(1, player.length) : 0
    } : null
    property var last: null
    onLiveChanged: if (live) last = live
    readonly property var shown: live || (hold ? last : null)
    readonly property real length: shown ? shown.length : 0
    readonly property bool canSeek: !!player && player.canControl && player.canSeek && player.positionSupported && length > 0
    implicitHeight: Math.round(152 * unit)
    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
    color: ownCover ? Qt.alpha(foreground, 0.06) : "transparent"
    clip: true
    function timeLabel(seconds) {
        let value = Math.max(0, Math.floor(seconds || 0));
        const hours = Math.floor(value / 3600);
        const clock = String(Math.floor(value / 60) % 60).padStart(2, "0") + ":" + String(value % 60).padStart(2, "0");
        return hours ? hours + ":" + clock : clock;
    }
    Timer {
        interval: 500; repeat: true; running: card.active && !!card.player
        triggeredOnStart: true
        onTriggered: if (!seek.pressed) card.position = card.player.position
    }

    Image {
        id: cover
        anchors.fill: parent
        source: card.shown ? card.shown.cover : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        sourceSize.width: Math.ceil(width * Screen.devicePixelRatio)
        visible: card.ownCover && card.hasCover
    }
    Rectangle {
        anchors.fill: parent
        visible: card.ownCover && card.hasCover
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.rgba(0, 0, 0, 0.45) }
            GradientStop { position: 1; color: Qt.rgba(0, 0, 0, 0.7) }
        }
    }

    Text {
        x: Math.round(10 * card.unit); y: Math.round(6 * card.unit)
        width: parent.width - 2 * x
        text: card.shown ? card.shown.identity : ""
        elide: Text.ElideRight
        color: card.ink; opacity: 0.85
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.bold: true
    }
    // Title and artist, centred; a line too long to fit scrolls slowly instead of being cut.
    Item {
        id: trackLine
        anchors.horizontalCenter: parent.horizontalCenter
        y: Math.round(26 * card.unit)
        width: parent.width - Math.round(20 * card.unit)
        height: track.implicitHeight
        clip: true
        readonly property bool scrolls: track.implicitWidth > width
        readonly property real gap: 48
        Row {
            id: marquee
            x: trackLine.scrolls ? 0 : (trackLine.width - track.implicitWidth) / 2
            spacing: trackLine.gap
            Text {
                id: track
                textFormat: Text.PlainText
                text: card.shown ? card.shown.line : Eitr.I18n.tr("No media playing")
                color: card.ink
                font.family: DesktopFonts.family; font.pixelSize: card.compact ? PanelStyle.bodySize : PanelStyle.headingSize; font.bold: true
            }
            Text {
                visible: trackLine.scrolls
                text: track.text; color: track.color; font: track.font; textFormat: Text.PlainText
            }
            NumberAnimation on x {
                running: trackLine.scrolls && card.active && !DesktopStyle.reduceMotion
                from: 0; to: -(track.implicitWidth + trackLine.gap)
                duration: Math.max(1, (track.implicitWidth + trackLine.gap) * 28)
                loops: Animation.Infinite
                onRunningChanged: if (!running) marquee.x = Qt.binding(() => trackLine.scrolls ? 0 : (trackLine.width - track.implicitWidth) / 2)
            }
        }
    }

    Item {
        id: seek
        readonly property real inset: Math.round(10 * card.unit)
        readonly property real waveHeight: Math.round(14 * card.unit)
        readonly property bool pressed: drag.pressed
        property real dragValue: 0
        readonly property real fraction: card.length > 0 ? Math.max(0, Math.min(1, (pressed ? dragValue : card.position) / card.length)) : 0
        x: inset; width: parent.width - 2 * inset
        y: Math.round(48 * card.unit); height: waveHeight + 16
        readonly property real trackY: waveHeight + 8
        readonly property real filled: width * fraction

        SpectrumConsumer {
            id: audio
            active: card.active && card.playing && card.visible
            // No more bands or frames than the bar's indicator uses, so opening the card
            // never restarts the shared analyzer (and the indicator with it).
            bars: 10
            frameRate: 30
            onSpectrumChanged: waves.requestPaint()
        }
        Canvas {
            id: waves
            width: parent.width; height: seek.trackY
            // No invented motion: without real audio frames the played part stays flat.
            readonly property bool live: audio.active && SpectrumProvider.hasFrame && audio.spectrum.length > 0
            onLiveChanged: { heights = [0, 0, 0]; requestPaint(); }
            onWidthChanged: requestPaint()
            Connections { target: seek; function onFilledChanged() { waves.requestPaint(); } }
            // Each layer is a few broad hills drifting along the played part; one band of
            // the spectrum (bass, middle, treble) sets how tall that layer stands.
            readonly property var layers: [
                {color: Qt.alpha(card.accent, 0.6), from: 0, to: 0.3, centres: [0.2, 0.55, 0.85], speed: 0.21, scale: 1},
                {color: Qt.alpha(Qt.lighter(card.accent, 1.45), 0.45), from: 0.3, to: 0.65, centres: [0.35, 0.7], speed: -0.17, scale: 0.85},
                {color: Qt.rgba(1, 1, 1, 0.28), from: 0.65, to: 1, centres: [0.1, 0.45, 0.78], speed: 0.13, scale: 0.7}
            ]
            property var heights: [0, 0, 0]
            function bandLevel(levels, from, to) {
                const first = Math.floor(from * levels.length), last = Math.max(first + 1, Math.floor(to * levels.length));
                let sum = 0;
                for (let index = first; index < last; index++) sum += Math.min(1, levels[index] || 0);
                return sum / (last - first);
            }
            onPaint: {
                const context = getContext("2d");
                context.clearRect(0, 0, width, height);
                const span = seek.filled;
                if (!live || span < 12) return;
                const seconds = Date.now() / 1000;
                const levels = audio.spectrum;
                const next = [];
                layers.forEach(function(layer, number) {
                    // Rise quickly with the music and settle slowly, so the hills breathe.
                    const target = Math.min(1, waves.bandLevel(levels, layer.from, layer.to) * 1.6);
                    const previous = waves.heights[number] || 0;
                    const level = previous + (target - previous) * (target > previous ? 0.5 : 0.12);
                    next.push(level);
                    context.fillStyle = layer.color;
                    context.beginPath();
                    context.moveTo(0, height);
                    const steps = Math.max(8, Math.round(span / 4));
                    for (let step = 0; step <= steps; step++) {
                        const along = step / steps;
                        let hill = 0;
                        layer.centres.forEach(function(centre, index) {
                            const drift = centre + 0.12 * Math.sin(seconds * layer.speed * Math.PI * 2 + index * 2.1);
                            const distance = (along - drift) / 0.14;
                            hill += Math.exp(-distance * distance);
                        });
                        // The hills taper into the track at both ends of the played part.
                        const envelope = Math.sin(Math.PI * along);
                        context.lineTo(along * span, height - Math.min(1, hill) * level * seek.waveHeight * layer.scale * envelope);
                    }
                    context.lineTo(span, height);
                    context.closePath();
                    context.fill();
                });
                heights = next;
            }
        }
        Rectangle {
            y: seek.trackY - height / 2; x: seek.filled + thumb.width / 2
            width: Math.max(0, parent.width - x); height: Math.round(5 * card.unit); radius: height / 2
            color: Qt.alpha(card.ink, 0.35)
        }
        Rectangle {
            y: seek.trackY - height / 2
            width: seek.filled; height: Math.round(5 * card.unit); radius: height / 2
            color: card.accent
        }
        Rectangle {
            id: thumb
            visible: card.length > 0
            width: Math.round(18 * card.unit); height: width; radius: width / 2
            x: seek.filled - width / 2; y: seek.trackY - height / 2
            color: card.accent
            border.width: 2; border.color: card.ink
            Rectangle {
                anchors.centerIn: parent; z: -1
                width: parent.width * 1.9; height: width; radius: width / 2
                color: Qt.alpha(card.accent, 0.28)
            }
        }
        MouseArea {
            id: drag
            anchors.fill: parent
            enabled: card.canSeek
            cursorShape: card.canSeek ? Qt.PointingHandCursor : Qt.ArrowCursor
            function valueAt(mouseX) { return Math.max(0, Math.min(1, mouseX / width)) * card.length; }
            onPressed: function(mouse) { seek.dragValue = valueAt(mouse.x); }
            onPositionChanged: function(mouse) { if (pressed) seek.dragValue = valueAt(mouse.x); }
            onReleased: { card.player.position = seek.dragValue; card.position = seek.dragValue; }
        }
    }
    Text {
        x: seek.x; y: seek.y + seek.height + 2
        text: card.timeLabel(seek.pressed ? seek.dragValue : card.position)
        color: card.ink; opacity: 0.7
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
    Text {
        anchors.right: parent.right; anchors.rightMargin: seek.inset; y: seek.y + seek.height + 2
        text: card.length > 0 ? card.timeLabel(card.length) : "--:--"
        color: card.ink; opacity: 0.7
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom; anchors.bottomMargin: Math.round(3 * card.unit)
        spacing: Math.round(18 * card.unit)
        Repeater {
            // A fixed model: rebuilding it on play/pause would recreate the buttons mid-effect.
            model: [
                {glyph: "󰒮", allowed: "canGoPrevious", action: "previous"},
                {glyph: "", allowed: "canTogglePlaying", action: "togglePlaying"},
                {glyph: "󰒭", allowed: "canGoNext", action: "next"}
            ]
            Rectangle {
                id: control
                required property var modelData
                readonly property bool toggles: modelData.action === "togglePlaying"
                readonly property bool available: !!card.player && card.player.canControl && card.player[modelData.allowed]
                readonly property string glyph: toggles ? (card.playing ? "󰏤" : "󰐊") : modelData.glyph
                readonly property bool motion: !DesktopStyle.reduceMotion
                width: Math.round(44 * card.unit); height: width; radius: width / 2
                color: Qt.alpha(card.ink, press.pressed && available ? 0.32 : press.containsMouse && available ? 0.24 : 0.14)
                Behavior on color { enabled: control.motion; ColorAnimation { duration: 120 } }
                opacity: available ? 1 : 0.4
                // Pressed, the button sinks a little and springs back.
                scale: press.pressed && available ? 0.9 : 1
                Behavior on scale { enabled: control.motion; NumberAnimation { duration: 160; easing.type: Easing.OutBack } }
                Accessible.role: Accessible.Button
                Accessible.name: modelData.action === "previous" ? Eitr.I18n.tr("Previous track")
                    : modelData.action === "next" ? Eitr.I18n.tr("Next track")
                    : card.playing ? Eitr.I18n.tr("Pause") : Eitr.I18n.tr("Play")

                // A soft light spreads from the click and fades. It grows toward the
                // button's centre as it widens, so it always stays inside the circle.
                Rectangle {
                    id: ripple
                    property point origin: Qt.point(control.width / 2, control.height / 2)
                    property real spread: 0
                    readonly property real size: control.width * spread
                    width: size; height: size; radius: size / 2
                    x: origin.x + (control.width / 2 - origin.x) * spread - size / 2
                    y: origin.y + (control.height / 2 - origin.y) * spread - size / 2
                    color: Qt.alpha(card.ink, 0.35)
                    opacity: 0
                    ParallelAnimation {
                        id: rippleAnimation
                        NumberAnimation { target: ripple; property: "spread"; from: 0.15; to: 1; duration: 420; easing.type: Easing.OutCubic }
                        NumberAnimation { target: ripple; property: "opacity"; from: 1; to: 0; duration: 520; easing.type: Easing.InQuad }
                    }
                }
                // The icon swaps by shrinking away while the new one grows in.
                Text {
                    id: icon
                    anchors.centerIn: parent
                    property string shown: control.glyph
                    text: shown
                    color: card.ink
                    font.family: DesktopFonts.family; font.pixelSize: Math.round(20 * card.unit)
                    SequentialAnimation {
                        id: swap
                        ParallelAnimation {
                            NumberAnimation { target: icon; property: "scale"; to: 0.4; duration: 90; easing.type: Easing.InQuad }
                            NumberAnimation { target: icon; property: "opacity"; to: 0; duration: 90 }
                        }
                        ScriptAction { script: icon.shown = control.glyph }
                        ParallelAnimation {
                            NumberAnimation { target: icon; property: "scale"; from: 0.4; to: 1; duration: 180; easing.type: Easing.OutBack }
                            NumberAnimation { target: icon; property: "opacity"; to: 1; duration: 140 }
                        }
                    }
                }
                onGlyphChanged: {
                    if (!motion || !visible) { swap.stop(); icon.scale = 1; icon.opacity = 1; icon.shown = glyph; return; }
                    swap.restart();
                }
                MouseArea {
                    id: press
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: control.available
                    cursorShape: Qt.PointingHandCursor
                    onPressed: function(mouse) {
                        if (!control.motion) return;
                        ripple.origin = Qt.point(mouse.x, mouse.y);
                        rippleAnimation.restart();
                    }
                    onClicked: card.player[control.modelData.action]()
                }
            }
        }
    }
}
