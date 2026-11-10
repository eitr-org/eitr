import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

Item {
    id: picture
    property string layout: "unified"
    property string edge: "top"
    property string appearance: "solid"
    property color background: "#20242c"
    property color foreground: "#eeeeee"
    property color accent: foreground
    property color gold: foreground
    property real zoom: 1
    property bool scenery: true
    readonly property real corner: DesktopStyle.radius(3)
    readonly property bool vertical: edge === "left" || edge === "right"
    readonly property color surface: appearance === "website" ? SiteStyle.bg : appearance === "transparent" ? Qt.alpha(foreground, 0.15) : background
    readonly property color ink: appearance === "website" ? SiteStyle.bronze : foreground

    Rectangle {
        anchors.fill: parent
        visible: picture.scenery
        color: Qt.tint(picture.background, Qt.alpha(picture.accent, 0.18))
    }
    Item {
        id: scene
        width: picture.width / picture.zoom
        height: picture.height / picture.zoom
        scale: picture.zoom
        transformOrigin: Item.TopLeft
        readonly property real length: picture.vertical ? height : width
        readonly property bool compactVertical: picture.vertical && length < 120
        readonly property real depth: compactVertical ? 18 : 22
        readonly property real clockSize: picture.vertical ? (compactVertical ? 26 : 34) : 48
        readonly property real gap: 6
        readonly property real inset: picture.layout === "islands" || picture.layout === "dynamic" || picture.layout === "drop" ? 4 : 0
        readonly property real across: picture.edge === "bottom" ? height - depth - inset : picture.edge === "right" ? width - depth - inset : inset
        // Slots describe both the silhouette and the content; the clock owns the midpoint.
        readonly property var slots: {
            const center = (length - clockSize) / 2;
            if (picture.layout === "centered" || picture.layout === "drop") return [{kind: "clock", start: center, extent: clockSize}];
            if (picture.layout === "dynamic") return [
                {kind: "logo", start: center - gap - depth, extent: depth},
                {kind: "clock", start: center, extent: clockSize},
                {kind: "status", start: center + clockSize + gap, extent: depth}];
            const workspaceSize = picture.vertical ? (compactVertical ? 13 : 20) : 32;
            const logoSize = compactVertical ? 14 : depth;
            return [
                {kind: "logo", start: compactVertical ? 0 : 4, extent: logoSize},
                {kind: "workspaces", start: compactVertical ? 18 : 4 + depth + gap, extent: workspaceSize},
                {kind: "clock", start: center, extent: clockSize},
                {kind: "status", start: length - depth - 4, extent: depth}];
        }
        Canvas {
            id: surfaces
            anchors.fill: parent
            property var slots: scene.slots
            property real corner: picture.corner
            onCornerChanged: requestPaint()
            property color surface: picture.surface
            property string layout: picture.layout
            property string edge: picture.edge
            onSlotsChanged: requestPaint()
            onSurfaceChanged: requestPaint()
            onLayoutChanged: requestPaint()
            onEdgeChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                const context = getContext("2d");
                context.reset();
                context.fillStyle = surface;
                // Only silhouettes change edge orientation. Content stays upright.
                if (picture.edge === "bottom") { context.translate(0, height); context.scale(1, -1); }
                if (picture.edge === "left") context.transform(0, 1, 1, 0, 0, 0);
                if (picture.edge === "right") context.transform(0, 1, -1, 0, width, 0);
                function pill(start, extent, inset, radius) {
                    context.beginPath();
                    context.roundedRect(start, inset, extent, scene.depth, radius, radius);
                    context.fill();
                }
                function tab(start, extent) {
                    const slope = 9;
                    context.beginPath();
                    context.moveTo(start - slope, 0);
                    context.lineTo(start, scene.depth);
                    context.lineTo(start + extent, scene.depth);
                    context.lineTo(start + extent + slope, 0);
                    context.closePath(); context.fill();
                }
                if (layout === "unified") pill(0, scene.length, 0, corner);
                else if (layout === "notch") {
                    context.fillRect(0, 0, scene.length, 3);
                    tab(0, scene.slots[1].start + scene.slots[1].extent);
                    tab(scene.slots[2].start, scene.clockSize);
                    tab(scene.slots[3].start, scene.depth + 4);
                } else if (layout === "centered") tab(scene.slots[0].start, scene.clockSize);
                else for (const slot of scene.slots) pill(slot.start, slot.extent, scene.inset, Math.min(slot.extent, scene.depth) / 2);
            }
        }
        Repeater {
            model: scene.slots
            Item {
                id: slot
                required property var modelData
                x: picture.vertical ? scene.across : modelData.start
                y: picture.vertical ? modelData.start : scene.across
                width: picture.vertical ? scene.depth : modelData.extent
                height: picture.vertical ? modelData.extent : scene.depth
                EitrLogo {
                    anchors.centerIn: parent
                    visible: slot.modelData.kind === "logo"
                    slotWidth: Math.round(18 * picture.zoom)
                    height: 24 * picture.zoom
                    iconSize: Math.round((scene.compactVertical ? 12 : 14) * picture.zoom)
                    scale: 1 / picture.zoom
                    foreground: picture.ink; background: picture.surface
                    enabled: false
                }
                Grid {
                    anchors.centerIn: parent
                    visible: slot.modelData.kind === "workspaces"
                    columns: picture.vertical ? 1 : 3
                    spacing: scene.compactVertical ? 2 : 4
                    Repeater {
                        model: 3
                        Rectangle {
                            required property int index
                            antialiasing: true
                            width: scene.compactVertical ? 3 : 4; height: width; radius: width / 2
                            color: picture.ink
                            opacity: index === 0 ? 1 : 0.4
                        }
                    }
                }
                Text {
                    anchors.centerIn: parent
                    visible: slot.modelData.kind === "clock"
                    text: picture.vertical ? "12\n34" : "12:34"
                    horizontalAlignment: Text.AlignHCenter
                    color: picture.ink
                    font.family: DesktopFonts.family; font.pixelSize: scene.compactVertical ? 9 : 10
                    lineHeight: 0.9
                }
                Item {
                    anchors.centerIn: parent
                    visible: slot.modelData.kind === "status"
                    width: 16; height: 16
                    TextMetrics { id: metrics; font: status.font; text: status.text }
                    Text {
                        id: status
                        text: "󰖩"; color: picture.ink
                        font.family: PanelStyle.fontFamily; font.pixelSize: 12
                        x: (parent.width - metrics.tightBoundingRect.width) / 2 - metrics.tightBoundingRect.x
                        y: (parent.height - metrics.tightBoundingRect.height) / 2 - baselineOffset - metrics.tightBoundingRect.y
                    }
                }
            }
        }
    }
}
