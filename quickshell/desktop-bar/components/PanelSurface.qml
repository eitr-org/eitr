import ".."
import QtQuick
import QtQuick.Shapes
import QtQuick.Effects
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
    // A Dynamic island draws this panel's surface; content appears once it has grown.
    readonly property bool morphed: !!hostWindow.morphIsland || !!hostWindow.morphPill
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
    // A Dynamic card keeps a strip on its bar side for the previous/next panel buttons.
    readonly property real navigationBand: hostWindow.navigationBand || 0
    // A panel may ask for less space around its content (the media card uses half).
    property real paddingScale: hostWindow.paddingScale !== undefined ? hostWindow.paddingScale : 1
    readonly property real leftPadding: outerGaps[3] * PanelStyle.contentGapMultiplier * paddingScale + (edge === "left" ? navigationBand : 0)
    readonly property real rightPadding: outerGaps[1] * PanelStyle.contentGapMultiplier * paddingScale + (edge === "right" ? navigationBand : 0)
    readonly property real topPadding: outerGaps[0] * PanelStyle.contentGapMultiplier * paddingScale + (edge === "top" ? navigationBand : 0)
    readonly property real bottomPadding: outerGaps[2] * PanelStyle.contentGapMultiplier * paddingScale + (edge === "bottom" ? navigationBand : 0)
    // An optional picture filling the whole sheet (to its edges, cut to its shape),
    // drawn over the surface colour and under the content.
    property Item backdrop: null
    // A thin rim of the surface colour left around the backdrop.
    property real backdropInset: hostWindow.backdropInset !== undefined ? hostWindow.backdropInset : 0
    onBackdropChanged: if (backdrop) backdrop.parent = backdropHost
    readonly property alias contentItem: contents
    default property alias panelContent: contents.data

    // The sheet's outline: two inward curves join it to the bar; the outer corners stay
    // rounded as it unfolds (see PanelOutline.qml, which draws it).
    // With an inset, the sheet's body shrunk on every side with all corners rounded (a backdrop's mask).
    function outlinePath(w, h, inset) {
        if (w <= 0 || h <= 0) return "";
        var r = Math.min(surface.contentInset, w / 4, h / 2);
        var reversed = surface.edge === "bottom" || surface.edge === "left";
        var startInset = !surface.edgeJoins || (reversed ? surface.flushTrailing : surface.flushLeading) ? 0 : r;
        var endInset = !surface.edgeJoins || (reversed ? surface.flushLeading : surface.flushTrailing) ? 0 : r;
        var corner = Math.min(DesktopStyle.radius(surface.contentInset), (w-startInset-endInset) / 2, h / 2);
        if (inset > 0) {
            var left = startInset + inset, right = w - endInset - inset, bottom = h - inset;
            var round = Math.max(0, Math.min(corner - inset, (right - left) / 2, bottom / 2));
            if (right <= left || bottom <= 0) return "";
            var top = inset;
            round = Math.max(0, Math.min(round, (bottom - top) / 2));
            return "M " + (left+round) + " " + top + " L " + (right-round) + " " + top + " Q " + right + " " + top + " " + right + " " + (top+round)
                + " L " + right + " " + (bottom-round) + " Q " + right + " " + bottom + " " + (right-round) + " " + bottom
                + " L " + (left+round) + " " + bottom + " Q " + left + " " + bottom + " " + left + " " + (bottom-round)
                + " L " + left + " " + (top+round) + " Q " + left + " " + top + " " + (left+round) + " " + top + " Z";
        }
        return "M 0 0 L " + w + " 0 Q " + (w-endInset) + " 0 " + (w-endInset) + " " + endInset
            + " L " + (w-endInset) + " " + (h-corner) + " Q " + (w-endInset) + " " + h + " " + (w-endInset-corner) + " " + h
            + " L " + (startInset+corner) + " " + h + " Q " + startInset + " " + h + " " + startInset + " " + (h-corner)
            + " L " + startInset + " " + startInset + " Q " + startInset + " 0 0 0 Z";
    }

    data: [Item {
        id: reveal
        width: surface.vertical ? surface.width * surface.progress : surface.width
        height: surface.vertical ? surface.height : surface.height * surface.progress
        x: surface.edge === "right" ? surface.width - width : 0
        y: surface.edge === "bottom" ? surface.height - height : 0
        clip: true

        PanelOutline { surface: surface; frame: reveal }

        Rectangle {
            anchors.fill: parent
            visible: surface.detached && !surface.morphed
            radius: DesktopStyle.radius(PanelStyle.cornerRadius)
            color: surface.color
        }

        Item {
            id: backdropMask
            anchors.fill: parent
            visible: false
            layer.enabled: true
            PanelOutline { surface: surface; frame: reveal; fill: "white"; inset: surface.backdropInset; visible: !surface.detached && !surface.morphed }
            Rectangle {
                anchors.fill: parent
                anchors.margins: surface.backdropInset
                visible: surface.detached || surface.morphed
                // Islands and Dynamic grow a card with 20 px corners into the panel.
                radius: Math.max(0, (surface.morphed ? 20 : DesktopStyle.radius(PanelStyle.cornerRadius)) - surface.backdropInset)
                color: "white"
            }
        }
        // The backdrop is drawn through a layer cut to the mask, which Qt redraws whenever
        // the picture or the sheet changes (a panel switched in mid-fold included).
        Item {
            anchors.fill: parent
            visible: !!surface.backdrop
            opacity: surface.morphed ? Math.max(0, surface.progress * 2 - 1) : 1
            layer.enabled: visible
            layer.effect: MultiEffect { maskEnabled: true; maskSource: backdropMask; maskThresholdMin: 0.5; maskSpreadAtMin: 1 }
            Item {
                id: backdropHost
                x: surface.edge === "right" ? reveal.width - surface.width : 0
                y: surface.edge === "bottom" ? reveal.height - surface.height : 0
                width: surface.width; height: surface.height
            }
        }

        Item {
            id: contents
            objectName: "panelContentFrame"
            width: Math.max(0, surface.width - surface.leftPadding - surface.rightPadding - (surface.vertical ? 0 : surface.leadingBodyInset + surface.trailingBodyInset))
            height: Math.max(0, surface.height - surface.topPadding - surface.bottomPadding - (surface.vertical ? surface.leadingBodyInset + surface.trailingBodyInset : 0))
            x: surface.leftPadding + (surface.vertical ? 0 : surface.leadingBodyInset) + (surface.edge === "right" ? reveal.width - surface.width : 0)
            y: surface.topPadding + (surface.vertical ? surface.leadingBodyInset : 0) + (surface.edge === "bottom" ? reveal.height - surface.height : 0)
            opacity: surface.morphed ? Math.max(0, surface.progress * 2 - 1) : Math.min(1, surface.progress * 2)
        }
    }]
}
