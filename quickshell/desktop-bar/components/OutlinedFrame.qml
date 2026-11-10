import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// The outlined field style shared by dropdowns and text fields: a rounded border with a
// label inside while the field is empty, which moves into a gap in the top border when the
// field holds a value or is in use. The gap is drawn, not painted over, so whatever is
// behind the field shows through it.
Item {
    id: outline
    property string label: ""
    property bool raised: false
    property bool active: false
    required property color foreground
    property color accent: foreground
    readonly property real lineWidth: active ? 2 : 1
    readonly property color lineColor: active ? accent : Qt.alpha(foreground, 0.32)
    readonly property real gapStart: raised && label !== "" ? caption.x - 4 : 0
    readonly property real gapEnd: raised && label !== "" ? caption.x + caption.implicitWidth + 4 : 0
    onLineWidthChanged: frame.requestPaint()
    onLineColorChanged: frame.requestPaint()
    onGapEndChanged: frame.requestPaint()
    onWidthChanged: frame.requestPaint()
    onHeightChanged: frame.requestPaint()
    Canvas {
        id: frame
        anchors.fill: parent
        onPaint: {
            const context = getContext("2d");
            context.reset();
            const inset = outline.lineWidth / 2;
            const radius = Math.min(DesktopStyle.radius(PanelStyle.controlRadius + 2), height / 2);
            const left = inset, top = inset, right = width - inset, bottom = height - inset;
            context.beginPath();
            context.moveTo(outline.gapEnd > 0 ? outline.gapEnd : left + radius, top);
            context.lineTo(right - radius, top);
            context.arcTo(right, top, right, top + radius, radius);
            context.lineTo(right, bottom - radius);
            context.arcTo(right, bottom, right - radius, bottom, radius);
            context.lineTo(left + radius, bottom);
            context.arcTo(left, bottom, left, bottom - radius, radius);
            context.lineTo(left, top + radius);
            context.arcTo(left, top, left + radius, top, radius);
            if (outline.gapEnd > 0) context.lineTo(outline.gapStart, top);
            context.lineWidth = outline.lineWidth;
            context.strokeStyle = outline.lineColor;
            context.stroke();
        }
    }
    Text {
        id: caption
        x: 14
        y: outline.raised ? -implicitHeight / 2 : (parent.height - implicitHeight) / 2
        text: outline.label
        color: outline.active ? outline.accent : outline.foreground
        opacity: outline.raised ? 0.85 : 0.62
        font.family: DesktopFonts.family
        font.pixelSize: outline.raised ? PanelStyle.captionSize : PanelStyle.bodySize
        Behavior on y { NumberAnimation { duration: DesktopStyle.motionDuration(120); easing.type: Easing.OutCubic } }
    }
}
