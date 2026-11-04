import QtQuick

// A profile picture drawn as a circle. Without one (or when it cannot be read) it shows the
// initial on an accent circle, or nothing at all when showInitial is off, as on the
// lockscreen. Canvas clipping works with every scene graph renderer, including software
// rendering on the login screen of machines without 3D drivers.
Item {
    id: avatar
    property url source: ""
    property string initial: ""
    property bool showInitial: true
    property color accent: "white"
    property color background: "black"
    property real size: 64
    width: size
    height: size
    readonly property bool hasImage: canvas.loaded
    visible: hasImage || showInitial
    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: avatar.accent
        visible: !avatar.hasImage
        Text {
            anchors.centerIn: parent
            text: avatar.initial
            color: avatar.background
            font.pixelSize: avatar.size * 0.44
        }
    }
    Canvas {
        id: canvas
        anchors.fill: parent
        visible: loaded
        property url current: ""
        property bool loaded: false
        function show(url) {
            if (current.toString() !== "") unloadImage(current);
            current = url;
            loaded = false;
            if (url.toString() === "") requestPaint();
            else if (isImageLoaded(url)) imageLoaded();
            else loadImage(url);
        }
        onImageLoaded: {
            loaded = current.toString() !== "" && isImageLoaded(current) && !isImageError(current);
            requestPaint();
        }
        onWidthChanged: requestPaint()
        onPaint: {
            const context = getContext("2d");
            context.reset();
            if (!loaded) return;
            context.beginPath();
            context.arc(width / 2, height / 2, width / 2, 0, 2 * Math.PI);
            context.clip();
            context.drawImage(current, 0, 0, width, height);
        }
        Component.onCompleted: show(avatar.source)
    }
    onSourceChanged: canvas.show(source)
}
