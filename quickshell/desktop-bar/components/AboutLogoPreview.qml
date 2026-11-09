import ".."
import QtQuick
import Eitr as Eitr

Rectangle {
    id: picture
    property string value: "emblem"
    property color foreground: "#68aa87"
    property color background: "#10231c"
    color: background
    onForegroundChanged: canvas.requestPaint()
    Canvas {
        id: canvas
        anchors.fill: parent
        anchors.margins: 4
        readonly property string source: "file://" + Eitr.Paths.code("fastfetch/assets/" + (picture.value === "runes" ? "eitr-runes.png" : "eitr-logo.png"))
        onSourceChanged: loadImage(source)
        Component.onCompleted: loadImage(source)
        onImageLoaded: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            const context = getContext("2d");
            context.reset();
            if (!isImageLoaded(source)) return;
            const ratio = picture.value === "runes" ? 456 / 480 : 1;
            const imageHeight = Math.min(height, width / ratio);
            const imageWidth = imageHeight * ratio;
            context.drawImage(source, (width - imageWidth) / 2, (height - imageHeight) / 2, imageWidth, imageHeight);
            context.globalCompositeOperation = "source-in";
            context.fillStyle = picture.foreground;
            context.fillRect(0, 0, width, height);
        }
    }
}
