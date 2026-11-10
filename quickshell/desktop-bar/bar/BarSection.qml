import ".."
import QtQuick

Rectangle {
    required property string edge
    required property color background
    radius: DesktopStyle.radius(6)
    topLeftRadius: edge === "top" || edge === "left" ? 0 : radius
    topRightRadius: edge === "top" || edge === "right" ? 0 : radius
    bottomLeftRadius: edge === "bottom" || edge === "left" ? 0 : radius
    bottomRightRadius: edge === "bottom" || edge === "right" ? 0 : radius
    property bool glow: false
    property real glowProgress: 1
    property color glowAccent: "transparent"
    color: background
    BarGlow { visible: glow; revealProgress: glowProgress; accent: glowAccent; cornerRadius: parent.radius }
}
