import ".."
import QtQuick

// A small ring beside the clock that fills as the running timer or focus phase goes on.
Canvas {
    id: ring
    property color foreground
    width: 14; height: 14
    readonly property real progress: FocusTimer.progress
    onProgressChanged: requestPaint()
    onForegroundChanged: requestPaint()
    onPaint: {
        const context = getContext("2d");
        context.reset();
        context.lineWidth = 2; context.lineCap = "round";
        context.strokeStyle = Qt.alpha(foreground, 0.3);
        context.beginPath(); context.arc(7, 7, 5.5, 0, Math.PI * 2); context.stroke();
        context.strokeStyle = foreground;
        context.beginPath(); context.arc(7, 7, 5.5, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.max(0.02, progress)); context.stroke();
    }
}
