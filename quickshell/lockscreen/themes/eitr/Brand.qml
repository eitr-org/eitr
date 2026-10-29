import QtQuick
import "Spectrum.js" as Spectrum

Item {
    id: brand
    property url artwork
    property real flow: 0
    property var spectrum: Spectrum.colors(false)
    Image {
        id: maskImage
        anchors.fill: parent
        source: brand.artwork
        sourceSize: Qt.size(width, height)
        fillMode: Image.PreserveAspectFit
        visible: false
    }
    ShaderEffect {
        visible: GraphicsInfo.api !== GraphicsInfo.Software
        anchors.fill: parent
        property var source: maskImage
        property real flow: brand.flow
        property color spectrum0: brand.spectrum[0]
        property color spectrum1: brand.spectrum[1]
        property color spectrum2: brand.spectrum[2]
        property color spectrum3: brand.spectrum[3]
        property color spectrum4: brand.spectrum[4]
        property color spectrum5: brand.spectrum[5]
        property color spectrum6: brand.spectrum[6]
        fragmentShader: Qt.resolvedUrl("shaders/brand.frag.qsb")
    }
    Canvas {
        id: raster
        anchors.fill: parent
        visible: GraphicsInfo.api === GraphicsInfo.Software
        readonly property string cacheKey: brand.artwork + JSON.stringify(brand.spectrum) + width + "x" + height
        onCacheKeyChanged: { unloadImage(brand.artwork); if (width > 0 && height > 0) loadImage(brand.artwork, Qt.size(width, height)); requestPaint(); }
        onImageLoaded: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        Connections {
            target: brand
            function onFlowChanged() { raster.requestPaint(); }
        }
        onPaint: {
            if (!isImageLoaded(brand.artwork)) { loadImage(brand.artwork, Qt.size(width, height)); return; }
            const context = getContext("2d");
            context.reset();
            context.drawImage(brand.artwork, 0, 0, width, height);
            context.globalCompositeOperation = "source-in";
            const start = -brand.flow * width * 2;
            const gradient = context.createLinearGradient(start, 0, start + width * 4, 0);
            for (let cycle = 0; cycle < 2; cycle++) {
                for (let stop = 0; stop < 7; stop++) gradient.addColorStop(cycle * 0.5 + stop / 12, brand.spectrum[stop]);
            }
            context.fillStyle = gradient;
            context.fillRect(0, 0, width, height);
        }
    }
}
