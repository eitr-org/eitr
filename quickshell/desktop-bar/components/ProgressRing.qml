import ".."
import QtQuick

// Shared circular progress ring used by bar indicators, Control Center, and Clock pages.
Canvas {
    id: ring
    property real progress: 0
    property color trackColor: Qt.alpha(accentColor, 0.25)
    property color accentColor: "white"
    property real lineWidth: 6
    property real ringPadding: lineWidth / 2 + 2
    property real minimumArc: 0
    property bool animateProgress: true
    property real renderedProgress: Math.max(0, Math.min(1, progress))

    Behavior on renderedProgress {
        enabled: ring.animateProgress && !DesktopStyle.reduceMotion
        NumberAnimation { duration: DesktopStyle.motionDuration(150); easing.type: Easing.OutQuad }
    }

    onRenderedProgressChanged: requestPaint()
    onTrackColorChanged: requestPaint()
    onAccentColorChanged: requestPaint()
    onLineWidthChanged: requestPaint()
    onRingPaddingChanged: requestPaint()
    onMinimumArcChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        const context = getContext("2d");
        context.reset();
        const size = Math.min(width, height);
        if (size <= 0) return;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.max(1, size / 2 - ring.ringPadding);
        context.lineWidth = ring.lineWidth;
        context.lineCap = "round";
        context.strokeStyle = ring.trackColor;
        context.beginPath();
        context.arc(centerX, centerY, radius, 0, Math.PI * 2);
        context.stroke();
        const clamped = Math.max(0, Math.min(1, ring.renderedProgress));
        const arc = ring.minimumArc > 0 ? Math.max(ring.minimumArc, clamped) : clamped;
        if (arc <= 0) return;
        context.strokeStyle = ring.accentColor;
        context.beginPath();
        context.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * arc);
        context.stroke();
    }
}
