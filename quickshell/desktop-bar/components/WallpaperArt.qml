import ".."
import QtQuick

// Artwork cropped to fill a rounded frame. Image cannot clip to a radius, so the
// corners outside it are painted in `surround`, the colour behind the frame.
// Children are drawn over the picture and inside the rounded corners.
Rectangle {
    id: art
    property url source: ""
    property color surround: "transparent"
    readonly property bool loaded: picture.status === Image.Ready
    default property alias content: overlay.data
    clip: true
    Image {
        id: picture
        anchors.fill: parent
        source: art.source
        asynchronous: true
        fillMode: Image.PreserveAspectCrop
        sourceSize: Qt.size(width * Screen.devicePixelRatio, height * Screen.devicePixelRatio)
    }
    Item { id: overlay; anchors.fill: parent }
    Canvas {
        anchors.fill: parent
        property real corner: art.radius
        property color ink: art.surround
        onCornerChanged: requestPaint()
        onInkChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            const context = getContext("2d");
            context.reset(); context.fillStyle = ink;
            context.beginPath(); context.rect(0, 0, width, height);
            context.moveTo(corner, 0); context.quadraticCurveTo(0, 0, 0, corner);
            context.lineTo(0, height - corner); context.quadraticCurveTo(0, height, corner, height);
            context.lineTo(width - corner, height); context.quadraticCurveTo(width, height, width, height - corner);
            context.lineTo(width, corner); context.quadraticCurveTo(width, 0, width - corner, 0);
            context.closePath(); context.fill();
        }
    }
}
