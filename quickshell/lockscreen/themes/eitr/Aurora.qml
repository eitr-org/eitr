import QtQuick
import QtQuick.Effects
import Qt5Compat.GraphicalEffects

Item {
    id: sky
    property real time: 0
    property bool light: false
    property var palette: ["#c2ee5a", "#3fe39a", "#e04fc3", "#9b5ce6"]
    opacity: light ? 0.58 : 1
    layer.enabled: light
    ShaderEffect {
        id: curtains
        // As the live wallpaper draws it (LiveWallpaperScene.qml): the curtains are soft,
        // so half resolution looks the same at a quarter of the cost.
        width: parent.width / 2
        height: parent.height / 2
        scale: 2
        transformOrigin: Item.TopLeft
        visible: false
        layer.enabled: true
        property real time: sky.time % 3600
        property real aspect: width / Math.max(1, height)
        property color lime: sky.palette[0]
        property color green: sky.palette[1]
        property color magenta: sky.palette[2]
        property color violet: sky.palette[3]
        fragmentShader: Qt.resolvedUrl("../../../desktop-bar/shaders/aurora.frag.qsb")
    }
    // On black the curtains glow brighter and more saturated than on the wallpaper.
    MultiEffect {
        anchors.fill: parent
        visible: !sky.light
        source: curtains
        saturation: 0.4
        brightness: 0.15
    }
    // Preserve a visible pigment on pale themes, using the shared curtain's alpha.
    ColorOverlay {
        anchors.fill: parent
        visible: sky.light
        source: curtains
        color: Qt.darker(sky.palette[3], 1.8)
    }
}
