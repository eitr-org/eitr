import Eitr as Eitr
import Quickshell
import QtQuick
import "AudioLevels.js" as AudioLevels

Item {
    id: indicator
    property string style: "bars"
    property bool playing: false
    property bool active: true
    required property color foreground
    required property color background
    property string title: ""
    readonly property bool audioActive: active && visible && enabled && opacity > 0 && playing
    readonly property bool hasAudioFrame: audioActive && SpectrumProvider.hasFrame
    readonly property var levels: audio.spectrum
    signal detailsRequested()
    width: 30
    height: 24

    function level(index) {
        // No invented motion: without real audio frames the indicator rests flat.
        if (!playing || !hasAudioFrame) return 0;
        return Math.max(0, Math.min(1, levels[index] || 0));
    }
    SpectrumConsumer {
        id: audio
        active: indicator.audioActive
        bars: indicator.style === "line" ? 16 : 8
        frameRate: 30
        smoothing: false
        onSpectrumChanged: if (wave.visible && indicator.active) wave.requestPaint()
    }
    onHasAudioFrameChanged: if (wave.visible && active) wave.requestPaint()
    onActiveChanged: if (wave.visible && active) wave.requestPaint()
    onPlayingChanged: if (wave.visible) wave.requestPaint()
    onForegroundChanged: if (wave.visible) wave.requestPaint()
    Row {
        anchors.centerIn: parent
        visible: indicator.style !== "line"
        height: 14
        spacing: 1
        Repeater {
            model: indicator.style === "line" ? 0 : 8
            Rectangle {
                required property int index
                anchors.verticalCenter: parent.verticalCenter
                width: 2.75
                height: AudioLevels.height(indicator.level(index))
                radius: 1
                color: indicator.foreground
                opacity: indicator.playing ? 1 : 0.55
            }
        }
    }
    Canvas {
        id: wave
        anchors.centerIn: parent
        width: 30
        height: 16
        visible: indicator.style === "line"
        opacity: indicator.playing ? 1 : 0.55
        onVisibleChanged: if (visible) requestPaint()
        onPaint: {
            const context = getContext("2d");
            context.clearRect(0, 0, width, height);
            context.strokeStyle = indicator.foreground;
            context.lineWidth = 1.5;
            context.lineCap = "round";
            context.beginPath();
            let previousX = 1;
            let previousY = height / 2;
            context.moveTo(previousX, previousY);
            for (let index = 0; index < 16; index++) {
                const nextX = 1 + index * (width - 2) / 15;
                const nextY = height / 2 + (index % 2 ? 1 : -1) * indicator.level(index) * 6;
                const middleX = (previousX + nextX) / 2;
                context.bezierCurveTo(middleX, previousY, middleX, nextY, nextX, nextY);
                previousX = nextX;
                previousY = nextY;
            }
            context.stroke();
        }
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: function(event) {
            if (event.button === Qt.RightButton)
                Quickshell.execDetached(["bash", Eitr.Paths.code("walker/scripts/actions/tools/music-visualizer.sh")]);
            else indicator.detailsRequested();
        }
    }
    BarTooltip { target: indicator; hovered: mouse.containsMouse; text: indicator.title; foreground: indicator.foreground; background: indicator.background }
}
