import ".."
import QtQuick
Canvas {
    property color accent: foreground
    property color background: "#20242c"
    property color foreground: "#eeeeee"
    property color raised: Qt.alpha(foreground, 0.08)
    property color gold: foreground
    id: picture
    property string value: "bars"
    readonly property color ink: picture.gold
    onValueChanged: requestPaint()
    onInkChanged: requestPaint()
    onRaisedChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const context = getContext("2d"); context.reset();
        context.fillStyle = picture.raised; context.fillRect(0, 0, width, height);
        context.fillStyle = ink; context.strokeStyle = ink; context.lineWidth = 2;
        context.beginPath();
        for (let index = 0; index < 8; index++) {
            const level = [12, 22, 36, 27, 16, 31, 21, 10][index];
            const position = width / 2 - 36 + index * 10;
            if (value === "bars") context.fillRect(position, (height - level) / 2, 5, level);
            else if (index === 0) context.moveTo(position, height / 2 - level / 2);
            else context.quadraticCurveTo(position - 5, height / 2 + level / 2, position, height / 2 - level / 2);
        }
        if (value === "line") context.stroke();
    }
}
