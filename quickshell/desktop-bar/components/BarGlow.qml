import ".."
import QtQuick
import QtQuick.Shapes

// Nested translucent strokes approximate a 16 px Gaussian falloff on both
// scenegraphs. The owning surface covers the inward half of each stroke.
Item {
    id: glow
    required property color accent
    property real revealProgress: 1
    opacity: revealProgress
    property real cornerRadius: 0
    property string outline: {
        const radius = Math.min(cornerRadius, width / 2, height / 2);
        return "M " + radius + " 0 H " + (width - radius)
            + " Q " + width + " 0 " + width + " " + radius
            + " V " + (height - radius) + " Q " + width + " " + height + " " + (width - radius) + " " + height
            + " H " + radius + " Q 0 " + height + " 0 " + (height - radius)
            + " V " + radius + " Q 0 0 " + radius + " 0 Z";
    }
    anchors.fill: parent
    z: -1
    Repeater {
        model: glow.visible ? 16 : 0
        Shape {
            required property int index
            id: halo
            anchors.fill: parent
            antialiasing: true
            // Differences of the Gaussian keep the total boundary opacity at 0.4.
            readonly property real nearAlpha: 0.4 * Math.exp(-index * index / 50)
            readonly property real farAlpha: 0.4 * Math.exp(-(index + 1) * (index + 1) / 50)
            ShapePath {
                fillColor: "transparent"
                strokeColor: Qt.alpha(glow.accent, (halo.nearAlpha - halo.farAlpha) / (1 - halo.farAlpha))
                strokeWidth: (halo.index + 1) * 2
                joinStyle: ShapePath.RoundJoin
                PathSvg { path: glow.outline }
            }
        }
    }
}
