import ".."
import QtQuick
import QtQuick.Shapes
import "../PanelStyle.js" as PanelStyle

Item {
    id: surface
    required property var hostWindow
    property color color: hostWindow.background
    property string edge: hostWindow.barEdge
    readonly property int contentInset: PanelStyle.surfaceInset
    readonly property bool vertical: edge === "left" || edge === "right"
    readonly property real progress: hostWindow.revealProgress
    readonly property bool detached: !!hostWindow.detached
    readonly property bool flushLeading: hostWindow.touchesLeadingEdge !== undefined
        ? hostWindow.touchesLeadingEdge : vertical ? hostWindow.y <= 0 : hostWindow.x <= 0
    readonly property bool flushTrailing: hostWindow.touchesTrailingEdge !== undefined
        ? hostWindow.touchesTrailingEdge : !!hostWindow.parent && (vertical
            ? hostWindow.y + hostWindow.height >= hostWindow.parent.height
            : hostWindow.x + hostWindow.width >= hostWindow.parent.width)
    // Concave joins inset the painted body except at a flush screen edge, or
    // when the host meets its edge with straight sides (edgeJoins: false).
    // Pad relative to that body, not the larger rectangular attachment area.
    readonly property bool edgeJoins: hostWindow.edgeJoins !== false
    readonly property int leadingBodyInset: detached || flushLeading || !edgeJoins ? 0 : contentInset
    readonly property int trailingBodyInset: detached || flushTrailing || !edgeJoins ? 0 : contentInset
    readonly property var outerGaps: hostWindow.hostWindow && hostWindow.hostWindow.outerGaps
        ? hostWindow.hostWindow.outerGaps : [12, 12, 12, 12]
    // Keep the sheet attached to the bar; only its content gains the window gap.
    readonly property real leftPadding: outerGaps[3] * PanelStyle.contentGapMultiplier
    readonly property real rightPadding: outerGaps[1] * PanelStyle.contentGapMultiplier
    readonly property real topPadding: outerGaps[0] * PanelStyle.contentGapMultiplier
    readonly property real bottomPadding: outerGaps[2] * PanelStyle.contentGapMultiplier
    default property alias panelContent: contents.data

    data: [Item {
        id: reveal
        width: surface.vertical ? surface.width * surface.progress : surface.width
        height: surface.vertical ? surface.height : surface.height * surface.progress
        x: surface.edge === "right" ? surface.width - width : 0
        y: surface.edge === "bottom" ? surface.height - height : 0
        clip: true

        Shape {
            id: outline
            width: surface.vertical ? reveal.height : reveal.width
            height: surface.vertical ? reveal.width : reveal.height
            x: surface.edge === "bottom" || surface.edge === "right" ? reveal.width : 0
            y: surface.edge === "bottom" || surface.edge === "left" ? reveal.height : 0
            transform: Rotation {
                angle: surface.edge === "bottom" ? 180 : surface.edge === "left" ? -90 : surface.edge === "right" ? 90 : 0
            }
            antialiasing: true
            visible: !surface.detached
            // Scene-graph geometry stays reactive even while hidden; unlike a
            // Canvas texture, it cannot miss a theme/color repaint request.
            ShapePath {
                strokeWidth: -1
                fillColor: surface.color
                PathSvg { path: {
                var w = outline.width;
                var h = outline.height;
                if (w <= 0 || h <= 0) return "";
                var r = Math.min(surface.contentInset, w / 4, h / 2);
                var reversed = surface.edge === "bottom" || surface.edge === "left";
                var startInset = !surface.edgeJoins || (reversed ? surface.flushTrailing : surface.flushLeading) ? 0 : r;
                var endInset = !surface.edgeJoins || (reversed ? surface.flushLeading : surface.flushTrailing) ? 0 : r;
                var corner = Math.min(DesktopStyle.radius(surface.contentInset), (w-startInset-endInset) / 2, h / 2);
                // The two inward curves join the sheet to the bar; the outer
                // corners remain rounded as the sheet unfolds.
                return "M 0 0 L " + w + " 0 Q " + (w-endInset) + " 0 " + (w-endInset) + " " + endInset
                    + " L " + (w-endInset) + " " + (h-corner) + " Q " + (w-endInset) + " " + h + " " + (w-endInset-corner) + " " + h
                    + " L " + (startInset+corner) + " " + h + " Q " + startInset + " " + h + " " + startInset + " " + (h-corner)
                    + " L " + startInset + " " + startInset + " Q " + startInset + " 0 0 0 Z";
                } }
            }
        }

        Rectangle {
            anchors.fill: parent
            visible: surface.detached
            radius: DesktopStyle.radius(PanelStyle.cornerRadius)
            color: surface.color
        }

        Item {
            id: contents
            objectName: "panelContentFrame"
            width: Math.max(0, surface.width - surface.leftPadding - surface.rightPadding - (surface.vertical ? 0 : surface.leadingBodyInset + surface.trailingBodyInset))
            height: Math.max(0, surface.height - surface.topPadding - surface.bottomPadding - (surface.vertical ? surface.leadingBodyInset + surface.trailingBodyInset : 0))
            x: surface.leftPadding + (surface.vertical ? 0 : surface.leadingBodyInset) + (surface.edge === "right" ? reveal.width - surface.width : 0)
            y: surface.topPadding + (surface.vertical ? surface.leadingBodyInset : 0) + (surface.edge === "bottom" ? reveal.height - surface.height : 0)
            opacity: Math.min(1, surface.progress * 2)
        }
    }]
}
