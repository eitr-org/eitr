import ".."
import QtQuick
import QtQuick.Shapes

// The website's card surface for library windows: warm base, a faint crimson
// glow from the top edge and the site's film grain.
Rectangle {
    color: SiteStyle.card
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: -1
            fillGradient: RadialGradient {
                centerX: parent.width / 2; centerY: 0; centerRadius: Math.max(parent.width, 1) * 0.6
                focalX: centerX; focalY: centerY
                GradientStop { position: 0; color: SiteStyle.glow }
                GradientStop { position: 1; color: "transparent" }
            }
            PathRectangle { width: parent.width; height: parent.height }
        }
    }
    Image {
        anchors.fill: parent
        source: "../assets/site/grain.png"
        fillMode: Image.Tile
        opacity: SiteStyle.grainOpacity
        smooth: false
    }
}
