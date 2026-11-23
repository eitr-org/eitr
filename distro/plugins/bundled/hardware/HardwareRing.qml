// SPDX-License-Identifier: MIT
// Copyright (c) 2026 The Eitr project
pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: root
    property real progress: 0
    property bool hasValue: true
    property color ringColor: "#74a8dc"
    property color trackColor: Qt.rgba(1, 1, 1, 0.16)
    property real strokeWidth: 3.5
    property string centerText: ""
    property color centerColor: "#ffffff"
    property string centerFontFamily: ""
    property real centerFontPixelSize: 10

    readonly property real clamped: hasValue ? Math.max(0, Math.min(1, progress)) : 0

    onClampedChanged: canvas.requestPaint()
    onHasValueChanged: canvas.requestPaint()
    onRingColorChanged: canvas.requestPaint()
    onTrackColorChanged: canvas.requestPaint()
    onStrokeWidthChanged: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true
        onPaint: {
            const ctx = getContext("2d");
            const size = Math.min(width, height);
            ctx.reset();
            if (size <= 2) return;
            const cx = width / 2;
            const cy = height / 2;
            const stroke = Math.max(1.5, Math.min(root.strokeWidth, size / 4));
            const radius = Math.max(1, (size - stroke) / 2);

            ctx.lineWidth = stroke;
            ctx.lineCap = "round";

            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2, false);
            ctx.strokeStyle = root.trackColor;
            ctx.stroke();

            if (root.hasValue && root.clamped > 0.002) {
                const start = -Math.PI / 2;
                ctx.beginPath();
                ctx.arc(cx, cy, radius, start, start + Math.PI * 2 * root.clamped, false);
                ctx.strokeStyle = root.ringColor;
                ctx.stroke();
            }
        }
    }

    Text {
        anchors.centerIn: parent
        visible: root.centerText !== ""
        text: root.centerText
        textFormat: Text.PlainText
        color: root.centerColor
        font.family: root.centerFontFamily
        font.pixelSize: root.centerFontPixelSize
        font.weight: Font.DemiBold
        font.features: ({"tnum": 1})
    }
}
