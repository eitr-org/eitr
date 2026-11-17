import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The Clock's chronograph face: one turn is an hour, with 60 ticks on the bezel.
// Pages add coloured rings (one per timer), arcs (focus and break), lap notches and
// the hand. With `adjustable` the hand is dragged round like a kitchen timer, adding
// an hour each time it passes the top; the wheel and arrow keys move it a minute.
// Children are placed in the centre of the face.
Item {
    id: dial
    required property color foreground
    required property color accent
    // {progress (0-1), color}; the first ring is the outermost.
    property var rings: []
    // {from, to (fractions of the turn), color}.
    property var arcs: []
    // Fractions of the turn marked with a small dot on the bezel.
    property var notches: []
    property bool showHand: false
    property real hand: 0
    property bool adjustable: false
    // The length set by dragging: the hand's exact turn while dragging, and in whole
    // minutes (0 to 12 hours).
    property real turned: 0
    readonly property int minutes: Math.round(turned)
    readonly property int maximumMinutes: 720
    readonly property real size: Math.min(width, height)
    readonly property real handPosition: adjustable ? (turned % 60) / 60 : hand
    default property alias centre: middle.data

    function setMinutes(value) { turned = Math.max(0, Math.min(maximumMinutes, Math.round(value))); }
    // A pointer position as a fraction of the turn, clockwise from the top.
    function fractionAt(pointerX, pointerY) {
        const angle = Math.atan2(pointerX - width / 2, height / 2 - pointerY);
        return (angle / (Math.PI * 2) + 1) % 1;
    }

    onRingsChanged: face.requestPaint()
    onArcsChanged: face.requestPaint()
    onNotchesChanged: face.requestPaint()
    onShowHandChanged: face.requestPaint()
    onHandPositionChanged: face.requestPaint()
    onAdjustableChanged: face.requestPaint()
    onForegroundChanged: face.requestPaint()
    onAccentChanged: face.requestPaint()

    Canvas {
        id: face
        anchors.centerIn: parent
        width: dial.size; height: dial.size
        onWidthChanged: requestPaint()
        onPaint: {
            const context = getContext("2d");
            context.reset();
            const centre = width / 2;
            const outer = centre - 4;
            const at = (fraction, radius) => [centre + Math.sin(fraction * Math.PI * 2) * radius, centre - Math.cos(fraction * Math.PI * 2) * radius];
            const arc = (radius, from, to) => {
                context.beginPath();
                context.arc(centre, centre, radius, -Math.PI / 2 + from * Math.PI * 2, -Math.PI / 2 + to * Math.PI * 2);
                context.stroke();
            };
            context.lineCap = "round";

            context.beginPath();
            context.arc(centre, centre, outer, 0, Math.PI * 2);
            context.fillStyle = Qt.alpha(dial.foreground, 0.03);
            context.fill();
            context.lineWidth = 1;
            context.strokeStyle = Qt.alpha(dial.foreground, 0.18);
            context.stroke();

            // Minute ticks, longer every five minutes.
            for (let minute = 0; minute < 60; minute += 1) {
                const major = minute % 5 === 0;
                const start = at(minute / 60, outer - 8);
                const end = at(minute / 60, outer - (major ? 20 : 13));
                context.beginPath();
                context.moveTo(start[0], start[1]);
                context.lineTo(end[0], end[1]);
                context.lineWidth = major ? 2 : 1;
                context.strokeStyle = Qt.alpha(dial.foreground, major ? 0.55 : 0.22);
                context.stroke();
            }
            context.font = "12px '" + DesktopFonts.family + "'";
            context.textAlign = "center";
            context.textBaseline = "middle";
            context.fillStyle = Qt.alpha(dial.foreground, 0.5);
            for (const minute of [0, 15, 30, 45]) {
                const point = at(minute / 60, outer - 34);
                context.fillText(String(minute), point[0], point[1]);
            }

            // Focus and break arcs just inside the ticks.
            context.lineWidth = 6;
            for (const entry of dial.arcs) {
                context.strokeStyle = entry.color;
                arc(outer - 48, entry.from, entry.to);
            }

            // One ring per timer, outermost first.
            let radius = outer - 48;
            for (const ring of dial.rings) {
                context.lineWidth = 5;
                context.strokeStyle = Qt.alpha(dial.foreground, 0.08);
                arc(radius, 0, 1);
                if (ring.progress > 0) {
                    context.strokeStyle = ring.color;
                    arc(radius, 0, Math.max(0.01, Math.min(1, ring.progress)));
                }
                radius -= 11;
            }

            for (const fraction of dial.notches) {
                const point = at(fraction, outer - 4);
                context.beginPath();
                context.arc(point[0], point[1], 3, 0, Math.PI * 2);
                context.fillStyle = dial.accent;
                context.fill();
            }

            if (dial.showHand || dial.adjustable) {
                const tip = at(dial.handPosition, outer - 16);
                // The hand starts outside the centre so it never crosses the time.
                const tail = at(dial.handPosition, middle.width / 2 + 6);
                context.beginPath();
                context.moveTo(tail[0], tail[1]);
                context.lineTo(tip[0], tip[1]);
                context.lineWidth = 2;
                context.strokeStyle = dial.accent;
                context.stroke();
                context.beginPath();
                context.arc(tip[0], tip[1], dial.adjustable ? 8 : 4, 0, Math.PI * 2);
                context.fillStyle = dial.accent;
                context.fill();
            }
        }
    }

    Item {
        id: middle
        anchors.centerIn: parent
        width: dial.size * 0.56; height: width
    }

    MouseArea {
        anchors.fill: face
        enabled: dial.adjustable
        // The centre keeps its own buttons; only the outer ring turns the hand.
        property real previous: 0
        function onRing(mouse) {
            return Math.hypot(mouse.x - width / 2, mouse.y - height / 2) > middle.width / 2;
        }
        cursorShape: dial.adjustable && containsMouse ? Qt.OpenHandCursor : Qt.ArrowCursor
        hoverEnabled: true
        onPressed: mouse => {
            if (!onRing(mouse)) { mouse.accepted = false; return; }
            const fraction = dial.fractionAt(mouse.x + face.x, mouse.y + face.y);
            dial.turned = Math.min(dial.maximumMinutes, Math.floor(dial.turned / 60) * 60 + fraction * 60);
            previous = fraction;
        }
        onPositionChanged: mouse => {
            if (!pressed) return;
            const fraction = dial.fractionAt(mouse.x + face.x, mouse.y + face.y);
            let step = fraction - previous;
            if (step > 0.5) step -= 1;
            if (step < -0.5) step += 1;
            previous = fraction;
            const next = dial.turned + step * 60;
            // Dragging back past zero stops at zero instead of wrapping to the end.
            if (next < 0) { dial.setMinutes(0); return; }
            dial.turned = Math.min(dial.maximumMinutes, next);
        }
        onReleased: dial.setMinutes(dial.minutes)
        onWheel: wheel => dial.setMinutes(dial.minutes + (wheel.angleDelta.y > 0 ? 1 : -1))
    }
}
