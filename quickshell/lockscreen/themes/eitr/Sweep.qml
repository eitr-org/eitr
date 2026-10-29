import QtQuick
import QtQuick.Shapes
import "Spectrum.js" as Spectrum

// Pure presentation: its host decides when the session is already unlocked.
// Two styles share one timeline. "bifrost": a beam drops down the middle of the
// screen, then splits into two beams that race apart to the left and right.
// "lightning": the website's hold-to-strike bolt (website/src/scripts/realm/
// mjolnir-charge.ts) hits the centre of the screen, and the lockscreen burns away
// from there like paper (shaders/burn.frag draws the frame
// from `source`). For the Bifröst, hosts show the lockscreen only outside
// [leftEdge, rightEdge], so it opens like a gate; for lightning both edges are 0
// and the width, so hosts show nothing and the burn draws the frame itself.
Item {
    id: sweep
    property real progress: 0
    property var spectrum: Spectrum.colors(false)
    property string style: "bifrost"
    readonly property bool lightning: style === "lightning"
    readonly property real drop: 0.32
    readonly property real beamWidth: Math.max(60, width * 0.06)
    readonly property real fall: Math.min(1, progress / drop)
    readonly property real spread: progress <= drop ? 0 : Math.pow((progress - drop) / (1 - drop), 1.6)
    readonly property real opening: spread * (width / 2 + beamWidth)
    readonly property real leftEdge: lightning ? 0 : Math.max(0, width / 2 - opening)
    readonly property real rightEdge: lightning ? width : Math.min(width, width / 2 + opening)
    // The lockscreen frame the lightning burns away (a texture provider).
    property var source: null

    component Beam: Rectangle {
        width: sweep.beamWidth
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "transparent" }
            GradientStop { position: 0.18; color: Qt.alpha(sweep.spectrum[0], 0.15) }
            GradientStop { position: 0.32; color: Qt.alpha(sweep.spectrum[0], 0.8) }
            GradientStop { position: 0.40; color: sweep.spectrum[1] }
            GradientStop { position: 0.46; color: sweep.spectrum[2] }
            GradientStop { position: 0.52; color: sweep.spectrum[3] }
            GradientStop { position: 0.58; color: sweep.spectrum[4] }
            GradientStop { position: 0.64; color: sweep.spectrum[5] }
            GradientStop { position: 0.72; color: Qt.alpha(sweep.spectrum[6], 0.8) }
            GradientStop { position: 1; color: "transparent" }
        }
    }
    // Falling: the beam's leading edge comes down from the top, with a bright head.
    Beam {
        visible: !sweep.lightning && sweep.progress <= sweep.drop
        x: (sweep.width - width) / 2
        height: sweep.height * (1 - Math.pow(1 - sweep.fall, 3))
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom
            width: parent.width * 0.7; height: width * 0.6; radius: width / 2
            color: "#fff4d6"; opacity: 0.55
        }
    }
    // Opening: two beams at the edges of the revealed desktop.
    Beam {
        visible: !sweep.lightning && sweep.progress > sweep.drop
        x: sweep.width / 2 - sweep.opening - width / 2
        height: sweep.height
    }
    Beam {
        visible: !sweep.lightning && sweep.progress > sweep.drop
        x: sweep.width / 2 + sweep.opening - width / 2
        height: sweep.height
    }

    // Lightning, as on the website: a jagged bolt from a random point at the top to
    // the centre (boltPath in website/src/scripts/realm/motion.ts), re-rolled once so
    // it flickers.
    property var bolts: []
    property real seed: 0
    function jagged(x1, y1, x2, y2, roughness) {
        const points = [[x1, y1]];
        const steps = 14;
        const length = Math.hypot(x2 - x1, y2 - y1);
        for (let index = 1; index < steps; index++) {
            const t = index / steps;
            const sway = (Math.random() - 0.5) * length * roughness * Math.sin(Math.PI * t);
            points.push([x1 + (x2 - x1) * t + sway, y1 + (y2 - y1) * t + (Math.random() - 0.5) * 8]);
        }
        points.push([x2, y2]);
        return "M " + points.map(point => point[0] + " " + point[1]).join(" L ");
    }
    function strikeShape() {
        const x = width / 2, y = height / 2;
        const top = x + (Math.random() - 0.5) * 320 * scale;
        bolts = [jagged(top, -10, x, y, 0.22), jagged(top, -10, x, y, 0.22)];
        seed = Math.random() * 100;
    }
    // A fresh bolt whenever the strike starts or the screen size settles.
    onLightningChanged: if (lightning) strikeShape()
    onVisibleChanged: if (visible && lightning) strikeShape()
    onWidthChanged: if (lightning) strikeShape()
    onHeightChanged: if (lightning) strikeShape()
    Component.onCompleted: if (lightning) strikeShape()
    // The website draws at CSS pixels on a 1080p-ish page; scale with the screen.
    readonly property real scale: Math.max(1, height / 1080)
    // Timeline (820 ms): the bolt shows for ~420 ms with its flash in the first 90 ms;
    // the burn starts once it has landed and spreads faster and faster.
    readonly property real milliseconds: progress * 820
    readonly property real hit: 0.15
    readonly property real burn: lightning && progress > hit ? Math.pow((progress - hit) / (1 - hit), 1.7) : 0
    component Bolt: Shape {
        id: shape
        property string path: ""
        property real core: 4.5
        property color glow: Qt.rgba(170 / 255, 205 / 255, 1, 1)
        property color color: "white"
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: Qt.alpha(shape.glow, 0.18); strokeWidth: shape.core * 8
            fillColor: "transparent"; joinStyle: ShapePath.RoundJoin; capStyle: ShapePath.RoundCap
            PathSvg { path: shape.path }
        }
        ShapePath {
            strokeColor: Qt.alpha(shape.glow, 0.5); strokeWidth: shape.core * 3
            fillColor: "transparent"; joinStyle: ShapePath.RoundJoin; capStyle: ShapePath.RoundCap
            PathSvg { path: shape.path }
        }
        ShapePath {
            strokeColor: shape.color; strokeWidth: shape.core
            fillColor: "transparent"; joinStyle: ShapePath.RoundJoin; capStyle: ShapePath.RoundCap
            PathSvg { path: shape.path }
        }
    }
    // The lockscreen burning away from the centre.
    ShaderEffect {
        anchors.fill: parent
        visible: sweep.lightning && sweep.source !== null
        property var source: sweep.source
        property size size: Qt.size(width, height)
        property point centre: Qt.point(width / 2, height / 2)
        // Starts just below zero so nothing burns until the bolt lands; ends past the corners.
        property real radius: -height * 0.12 + sweep.burn * (Math.hypot(width, height) / 2 + height * 0.3)
        property real seed: sweep.seed
        fragmentShader: Qt.resolvedUrl("shaders/burn.frag.qsb")
    }
    // The bolt: the first shape, then the re-rolled second one from 140 ms; it fades by 420 ms.
    Repeater {
        model: sweep.lightning ? sweep.bolts : []
        Bolt {
            required property var modelData
            required property int index
            path: modelData
            core: 4.5 * sweep.scale
            visible: index === 0 || sweep.milliseconds > 140
            opacity: Math.max(0, 1 - sweep.milliseconds / 420)
        }
    }
    // The burst where it lands: a small warm-white flare that grows and fades over ~230 ms.
    Rectangle {
        visible: sweep.lightning
        readonly property real flare: Math.min(1, sweep.milliseconds / 140)
        width: sweep.height * 0.12 * (0.3 + 0.7 * flare); height: width; radius: width / 2
        x: (sweep.width - width) / 2; y: (sweep.height - height) / 2
        color: "#fff1d0"
        opacity: Math.max(0, 0.8 - sweep.milliseconds / 290)
    }
    // The website's flash: a faint white wash for the first 90 ms.
    Rectangle {
        anchors.fill: parent
        visible: sweep.lightning
        color: "white"
        opacity: sweep.milliseconds < 90 ? 0.18 * (1 - sweep.milliseconds / 90) : 0
    }
}
