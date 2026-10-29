import QtQuick
import Qt5Compat.GraphicalEffects

// The night sky behind the aurora: shaders/sky.frag draws a dense starfield and a
// Milky Way band once (it has no time input, so its layer is reused), and a few
// brighter stars on top twinkle slowly. Positions come from the index, so every
// lock shows the same sky. Now and then a shooting star crosses the upper sky.
Item {
    id: sky
    property real time: 0
    property bool twinkle: true

    ShaderEffect {
        anchors.fill: parent
        visible: GraphicsInfo.api !== GraphicsInfo.Software
        layer.enabled: true
        property size size: Qt.size(width, height)
        fragmentShader: Qt.resolvedUrl("shaders/sky.frag.qsb")
    }
    Repeater {
        model: 30
        Rectangle {
            required property int index
            readonly property real across: (index * 0.618034 + 0.11) % 1
            readonly property real down: Math.pow((index * 0.7548777 + 0.31) % 1, 1.5) * 0.7
            readonly property real brightness: 0.5 + ((index * 0.3819660) % 1) * 0.5
            x: across * sky.width
            y: down * sky.height
            width: index % 4 === 0 ? 2.6 : 1.9
            height: width
            radius: width / 2
            color: index % 5 === 0 ? "#dfe8ff" : "#ffffff"
            // A soft glow around the twinkling star.
            RadialGradient {
                // Only one in four twinkling stars glows.
                visible: index % 4 === 0
                anchors.centerIn: parent
                width: parent.width * 4.5; height: width
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.alpha("#e6eeff", 0.45) }
                    GradientStop { position: 0.5; color: "transparent" }
                }
            }
            // Scintillation: quick, gentle shimmer around the star's brightness; it never fades out.
            opacity: sky.twinkle
                ? brightness * (0.82 + 0.1 * Math.sin(sky.time * (7 + index % 4) + index) + 0.08 * Math.sin(sky.time * (11.3 + index % 3) + index * 2.1))
                : brightness * 0.82
        }
    }
    // A shooting star every 6 to 18 seconds: a bright head with a fading tail,
    // falling diagonally across the upper sky in under a second.
    Timer {
        id: nextMeteor
        running: sky.twinkle && sky.visible
        interval: 6000 + Math.random() * 12000
        onTriggered: {
            meteor.launch();
            interval = 6000 + Math.random() * 12000;
            restart();
        }
    }
    Item {
        id: meteor
        property real length: sky.height * 0.16
        property real travel: 0
        property real startX: 0
        property real startY: 0
        property real angle: 30
        function launch() {
            startX = sky.width * (0.1 + Math.random() * 0.75);
            startY = sky.height * (0.02 + Math.random() * 0.25);
            angle = 22 + Math.random() * 22;
            if (Math.random() < 0.5) angle = 180 - angle;
            flight.restart();
        }
        x: startX + Math.cos(angle * Math.PI / 180) * travel * sky.height * 0.45
        y: startY + Math.sin(angle * Math.PI / 180) * travel * sky.height * 0.45
        rotation: angle
        transformOrigin: Item.Left
        opacity: 0
        Rectangle {
            x: -meteor.length; y: -height / 2
            width: meteor.length; height: 2
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: "transparent" }
                GradientStop { position: 1; color: "#eef4ff" }
            }
        }
        Rectangle { x: -2; y: -2; width: 4; height: 4; radius: 2; color: "white" }
        ParallelAnimation {
            id: flight
            NumberAnimation { target: meteor; property: "travel"; from: 0; to: 1; duration: 750; easing.type: Easing.InQuad }
            SequentialAnimation {
                NumberAnimation { target: meteor; property: "opacity"; from: 0; to: 0.95; duration: 120 }
                PauseAnimation { duration: 380 }
                NumberAnimation { target: meteor; property: "opacity"; to: 0; duration: 250 }
            }
        }
    }
}
