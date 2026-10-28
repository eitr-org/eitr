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
    property real pulse: 0
    readonly property bool audioActive: active && visible && enabled && opacity > 0 && playing
    readonly property bool hasAudioFrame: audioActive && SpectrumProvider.hasFrame
    readonly property var levels: audio.spectrum
    signal detailsRequested()
    width: 26
    height: 24

    function level(index) {
        if (!playing) return 0;
        if (hasAudioFrame) return Math.max(0, Math.min(1, levels[index] || 0));
        return (Math.sin(pulse + index * 1.7) + 1) / 2;
    }
    SpectrumConsumer {
        id: audio
        active: indicator.audioActive
        bars: indicator.style === "line" ? 16 : 7
        frameRate: 30
        smoothing: false
        onSpectrumChanged: if (wave.visible && indicator.active) wave.requestPaint()
    }
    Timer {
        interval: Math.ceil(1000 / 30)
        repeat: true
        running: indicator.audioActive && !indicator.hasAudioFrame && !DesktopStyle.reduceMotion
        onTriggered: indicator.pulse = (indicator.pulse + Math.PI * 2 / 45) % (Math.PI * 2)
    }
    onHasAudioFrameChanged: if (wave.visible && active) wave.requestPaint()
    onActiveChanged: if (wave.visible && active) wave.requestPaint()
    onPulseChanged: if (wave.visible && active) wave.requestPaint()
    onPlayingChanged: if (wave.visible) wave.requestPaint()
    onForegroundChanged: if (wave.visible) wave.requestPaint()
    Row {
        anchors.centerIn: parent
        visible: indicator.style !== "line"
        height: 14
        spacing: 1
        Repeater {
            model: indicator.style === "line" ? 0 : 7
            Rectangle {
                required property int index
                anchors.verticalCenter: parent.verticalCenter
                width: 2.75
                height: AudioLevels.height(indicator.level(index))
                Behavior on height { NumberAnimation { duration: DesktopStyle.motionDuration(70) } }
                radius: 1
                color: indicator.foreground
                opacity: indicator.playing ? 1 : 0.55
            }
        }
    }
    Canvas {
        id: wave
        anchors.centerIn: parent
        width: 26
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
