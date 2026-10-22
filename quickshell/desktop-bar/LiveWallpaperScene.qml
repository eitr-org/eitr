import QtQuick

// The layers of a live wallpaper at a given moment (see LiveWallpaper.qml):
// the sky, the website's northern lights (shaders/aurora.frag) and the ring.
// The sky and lights cover the screen like Hyprpaper; on screens wider than
// 16:9 the ring fits the height instead and keeps its place 70% across, as the
// theme's backgrounds-ultrawide pictures do, so it is never cut off.
Item {
    id: scene
    property string motion: ""
    // Seconds of motion so far; the shader drifts its curtains from it.
    property real time: 0
    readonly property bool ready: sky.status === Image.Ready && ring.status === Image.Ready
    clip: true

    Item {
        id: stage
        // The layers' pixel size (themes/norse/references/generate-wallpapers.py).
        readonly property real fit: Math.max(scene.width / 3840, scene.height / 2160)
        width: 3840 * fit
        height: 2160 * fit
        anchors.centerIn: parent

        Image { id: sky; anchors.fill: parent; source: scene.motion ? scene.motion + "sky.png" : ""; smooth: true }
        // The curtains are soft, so half resolution looks the same at a quarter of the cost.
        ShaderEffect {
            width: parent.width / 2
            height: parent.height / 2
            scale: 2
            transformOrigin: Item.TopLeft
            fragmentShader: Qt.resolvedUrl("shaders/aurora.frag.qsb")
            property real time: scene.time % 3600
            property real aspect: width / Math.max(1, height)
            // The runestone wallpaper's and the website's aurora colours.
            property color lime: "#c2ee5a"
            property color green: "#3fe39a"
            property color magenta: "#e04fc3"
            property color violet: "#9b5ce6"
        }
    }
    Image {
        id: ring
        readonly property bool wide: scene.width * 9 > scene.height * 16
        // The ring's centre in its layer (themes/norse/references/generate-wallpapers.py).
        readonly property real across: 0.7
        width: wide ? height * 16 / 9 : stage.width
        height: wide ? scene.height : stage.height
        x: wide ? scene.width * across - width * across : stage.x
        y: wide ? 0 : stage.y
        source: scene.motion ? scene.motion + "ring.png" : ""
        smooth: true
    }
}
