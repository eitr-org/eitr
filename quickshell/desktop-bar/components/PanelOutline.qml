import ".."
import QtQuick
import QtQuick.Shapes

// A panel sheet's outline (PanelSurface.outlinePath), rotated for the bar's edge and
// sized to the unfolding frame. PanelSurface draws it in its colour and masks a backdrop with it.
Shape {
    id: outline
    required property Item surface
    required property Item frame
    property color fill: surface.color
    property real inset: 0
    width: surface.vertical ? frame.height : frame.width
    height: surface.vertical ? frame.width : frame.height
    x: surface.edge === "bottom" || surface.edge === "right" ? frame.width : 0
    y: surface.edge === "bottom" || surface.edge === "left" ? frame.height : 0
    transform: Rotation {
        angle: outline.surface.edge === "bottom" ? 180 : outline.surface.edge === "left" ? -90 : outline.surface.edge === "right" ? 90 : 0
    }
    antialiasing: true
    visible: !surface.detached
    // Scene-graph geometry stays reactive even while hidden; unlike a
    // Canvas texture, it cannot miss a theme/color repaint request.
    ShapePath {
        strokeWidth: -1
        fillColor: outline.fill
        PathSvg { path: outline.surface.outlinePath(outline.width, outline.height, outline.inset) }
    }
}
