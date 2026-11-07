import ".."
import QtQuick

Canvas {
    property color gold: foreground
    id: picture
    property string layout: "unified"
    property string edge: "top"
    property string appearance: "solid"
    property bool expanded: false
    property real reveal: expanded ? 1 : 0
    Behavior on reveal { NumberAnimation { duration: DesktopStyle.motionDuration(320) } }
    property color background: "#20242c"
    property color foreground: "#eeeeee"
    property color accent: foreground
    readonly property real corner: DesktopStyle.radius(3)
    // Draws the same picture larger: the scene is laid out in width/zoom by height/zoom.
    property real zoom: 1
    // Paints its own sky and hill behind the bar; off when a picture sits underneath.
    property bool scenery: true
    onLayoutChanged: requestPaint()
    onEdgeChanged: requestPaint()
    onAppearanceChanged: requestPaint()
    onRevealChanged: requestPaint()
    onBackgroundChanged: requestPaint()
    onForegroundChanged: requestPaint()
    onAccentChanged: requestPaint()
    onCornerChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onZoomChanged: requestPaint()
    onSceneryChanged: requestPaint()
    onPaint: {
        const context = getContext("2d");
        context.reset();
        context.scale(zoom, zoom);
        const width = picture.width / zoom;
        const height = picture.height / zoom;
        if (scenery) {
            context.fillStyle = Qt.tint(background, Qt.alpha(accent, 0.18));
            context.fillRect(0, 0, width, height);
            context.fillStyle = Qt.alpha(accent, 0.13);
            context.beginPath(); context.moveTo(0, height); context.lineTo(width * 0.48, height * 0.22); context.lineTo(width, height); context.fill();
        }
        const vertical = edge === "left" || edge === "right";
        const length = vertical ? Math.max(180, height) : width;
        const depth = 15;
        context.save();
        if (edge === "bottom") { context.translate(0, height); context.scale(1, -1); }
        if (edge === "left") { context.transform(0, 1, 1, 0, 0, 0); }
        if (edge === "right") { context.transform(0, 1, -1, 0, width, 0); }
        if (vertical) context.scale(height / length, 1);
        const surface = appearance === "website" ? SiteStyle.bg : appearance === "transparent" ? Qt.alpha(foreground, 0.15) : background;
        const ink = appearance === "website" ? SiteStyle.bronze : foreground;
        function rounded(start, extent, inset, radius) {
            context.fillStyle = surface;
            context.beginPath(); context.roundedRect(start, inset, extent, depth, radius, radius); context.fill();
        }
        function clock(center, inset) {
            context.save();
            if (edge === "bottom") { context.translate(center, inset + 8); context.scale(1, -1); context.translate(-center, -inset - 8); }
            context.fillStyle = ink; context.font = "7px sans-serif";
            context.textAlign = "center"; context.fillText(vertical ? "◷" : "12:34", center, inset + 10);
            context.restore();
        }
        function marks(start, inset) {
            context.fillStyle = ink; context.font = "9px sans-serif"; context.textAlign = "left"; context.fillText("ᛖ", start, inset + 11);
            for (let index = 0; index < 3; index++) { context.beginPath(); context.arc(start + 15 + index * 5, inset + 8, 1.3, 0, 7); context.fill(); }
        }
        function status(start, inset) {
            context.strokeStyle = ink; context.lineWidth = 1;
            context.strokeRect(start, inset + 5, 7, 5);
            context.fillStyle = ink; context.fillRect(start + 11, inset + 5, 2, 6);
        }
        function slope(start, end) {
            context.fillStyle = surface;
            context.beginPath(); context.moveTo(start - 11, 0); context.lineTo(start, depth); context.lineTo(end, depth); context.lineTo(end + 11, 0); context.closePath(); context.fill();
        }
        if (layout === "dynamic") {
            const extent = 34 + reveal * 18;
            rounded(length / 2 - extent / 2, extent, 4, 8);
            rounded(length / 2 - extent / 2 - 21, 17, 4, 8);
            rounded(length / 2 + extent / 2 + 4, 24, 4, 8);
            clock(length / 2, 4);
            context.fillStyle = ink; context.font = "9px sans-serif"; context.fillText("ᛖ", length / 2 - extent / 2 - 12, 15);
            status(length / 2 + extent / 2 + 9, 4);
        } else if (layout === "islands") {
            rounded(3, 15, 4, 8); rounded(21, 23, 4, 8);
            rounded(47, 17, 4, 8); rounded(length / 2 - 17, 34, 4, 8); rounded(length / 2 + 20, 17, 4, 8); rounded(length - 27, 24, 4, 8);
            context.fillStyle = ink; context.font = "9px sans-serif"; context.fillText("ᛖ", 7, 15);
            for (let index = 0; index < 3; index++) { context.fillRect(27 + index * 5, 11, 2, 2); }
            context.fillStyle = ink; context.fillRect(53, 10, 4, 4); context.fillRect(length / 2 + 26, 10, 4, 4);
            clock(length / 2, 4); status(length - 22, 4);
        } else if (layout === "centered") {
            const extent = Math.min(length - 26, 34 + reveal * 92);
            slope(length / 2 - extent / 2, length / 2 + extent / 2);
            clock(length / 2, 0);
            if (reveal > 0.65) { marks(length / 2 - extent / 2 + 3, 0); status(length / 2 + extent / 2 - 18, 0); }
        } else {
            if (layout === "notch") {
                context.fillStyle = surface; context.fillRect(0, 0, length, 3);
                slope(0, 36); slope(length / 2 - 17, length / 2 + 17); slope(length - 24, length);
            } else rounded(0, length, 0, corner);
            marks(5, 0); clock(length / 2, 0); status(length - 20, 0);
        }
        context.restore();
    }
}
