import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland

// Short Norse moments drawn over the desktop:
// - lightning: a flash with a thin bolt striking what a screenshot just captured
//   (scripts call it after the capture, so it never appears in the image);
// - ragnarok: Fenrir lunges and his jaws swallow the screen.
Scope {
    id: realm
    required property color accent
    property var defaultScreen: null

    function screenNamed(name) {
        return (Quickshell.screens || []).find(screen => screen && screen.name === name) || null;
    }
    function screenAt(x, y) {
        return (Quickshell.screens || []).find(screen => screen && x >= screen.x && x < screen.x + screen.width
            && y >= screen.y && y < screen.y + screen.height) || null;
    }
    function focusedScreen() {
        var monitor = Hyprland.focusedMonitor;
        return (monitor && screenNamed(monitor.name)) || defaultScreen;
    }

    IpcHandler {
        target: "realm"
        // geometry is slurp's "x,y wxh" in layout coordinates, or empty for the whole monitor.
        function lightning(monitor: string, geometry: string): void {
            if (DesktopStyle.reduceMotion) return;
            var match = /^(-?\d+),(-?\d+) (\d+)x(\d+)$/.exec(geometry.trim());
            var screen = match ? realm.screenAt(Number(match[1]), Number(match[2])) : realm.screenNamed(monitor);
            screen = screen || realm.focusedScreen();
            if (!screen) return;
            var target = match
                ? Qt.rect(Number(match[1]) - screen.x, Number(match[2]) - screen.y, Number(match[3]), Number(match[4]))
                : Qt.rect(0, 0, screen.width, screen.height);
            storm.strike(screen, target);
        }
        function ragnarok(): void { if (!DesktopStyle.reduceMotion) fenrir.summon(realm.focusedScreen()); }
        function status(): string { return JSON.stringify({lightning: storm.visible, ragnarok: fenrir.stage}); }
    }

    PanelWindow {
        id: storm
        property rect target: Qt.rect(0, 0, 0, 0)
        property var points: []
        property var branches: []
        property real flash: 0
        visible: false
        color: "transparent"
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "desktop-lightning"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        // Clicks pass straight through to whatever is underneath.
        mask: Region {}

        // A jagged path from the top of the screen down to the struck point,
        // by repeated midpoint displacement; a couple of short forks split off it.
        function bolt(from, to, roughness, depth) {
            var path = [from, to];
            for (var level = 0; level < depth; level++) {
                var next = [path[0]];
                for (var index = 1; index < path.length; index++) {
                    var start = path[index - 1], end = path[index];
                    var spread = Math.hypot(end.x - start.x, end.y - start.y) * roughness;
                    next.push(Qt.point((start.x + end.x) / 2 + (Math.random() - 0.5) * spread, (start.y + end.y) / 2 + (Math.random() - 0.5) * spread * 0.3), end);
                }
                path = next;
            }
            return path;
        }
        function strike(screen, area) {
            target = area;
            storm.screen = screen;
            var full = area.width >= screen.width && area.height >= screen.height;
            // The bolt lands on the top edge of a selection, or somewhere in the middle third of a full screen.
            var landing = full ? Qt.point(screen.width * (0.33 + Math.random() * 0.34), screen.height * (0.55 + Math.random() * 0.15))
                               : Qt.point(area.x + area.width / 2, Math.max(area.y, 24));
            var origin = Qt.point(landing.x + (Math.random() - 0.5) * screen.width * 0.25, 0);
            points = bolt(origin, landing, 0.55, 6);
            var forks = [];
            for (var count = 0; count < 2; count++) {
                var root = points[Math.floor(points.length * (0.3 + Math.random() * 0.4))];
                var reach = 60 + Math.random() * 120;
                forks.push(bolt(root, Qt.point(root.x + (Math.random() < 0.5 ? -1 : 1) * reach, root.y + reach * 0.8), 0.6, 4));
            }
            branches = forks;
            canvas.requestPaint();
            visible = true;
            flicker.restart();
        }

        Rectangle { anchors.fill: parent; color: "white"; opacity: storm.flash * 0.45 }
        // A brief edge of light around the captured area.
        Rectangle {
            x: storm.target.x; y: storm.target.y; width: storm.target.width; height: storm.target.height
            color: "transparent"; border.width: 2; border.color: "white"
            opacity: storm.flash * 0.8
        }
        Canvas {
            id: canvas
            anchors.fill: parent
            opacity: Math.min(1, storm.flash * 1.6)
            onPaint: {
                var context = getContext("2d");
                context.reset();
                context.lineCap = "round";
                context.lineJoin = "round";
                var trace = (path, width, color) => {
                    if (path.length < 2) return;
                    context.beginPath();
                    context.moveTo(path[0].x, path[0].y);
                    for (var index = 1; index < path.length; index++) context.lineTo(path[index].x, path[index].y);
                    context.lineWidth = width;
                    context.strokeStyle = color;
                    context.stroke();
                };
                var glow = Qt.rgba(realm.accent.r, realm.accent.g, realm.accent.b, 0.35);
                trace(storm.points, 14, glow);
                storm.branches.forEach(fork => trace(fork, 8, glow));
                storm.branches.forEach(fork => trace(fork, 1.4, "white"));
                trace(storm.points, 2.6, "white");
            }
        }
        SequentialAnimation {
            id: flicker
            NumberAnimation { target: storm; property: "flash"; from: 0; to: 1; duration: 40 }
            NumberAnimation { target: storm; property: "flash"; to: 0.2; duration: 70 }
            NumberAnimation { target: storm; property: "flash"; to: 0.85; duration: 40 }
            NumberAnimation { target: storm; property: "flash"; to: 0; duration: 340; easing.type: Easing.OutCubic }
            ScriptAction { script: storm.visible = false }
        }
    }

    PanelWindow {
        id: fenrir
        // idle, fenrir, lunging, biting, swallowed, ending
        property string stage: "idle"
        property bool roaring: false
        visible: stage !== "idle"
        color: "transparent"
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "desktop-ragnarok"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: visible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        readonly property real side: Math.min(width, height)

        function summon(screen) {
            if (stage !== "idle" || !screen) return;
            fenrir.screen = screen;
            stage = "fenrir";
            roaring = false;
            choreography.restart();
        }
        function dismiss() {
            if (stage === "idle" || stage === "ending") return;
            choreography.stop();
            stage = "ending";
            ending.restart();
        }

        Item {
            id: scene
            anchors.fill: parent
            focus: fenrir.visible
            Keys.onEscapePressed: fenrir.dismiss()
            opacity: 0
            MouseArea { anchors.fill: parent; onClicked: fenrir.dismiss() }
            Rectangle { anchors.fill: parent; color: "black"; opacity: 0.85 }

            Image {
                id: face
                width: Math.min(fenrir.side * 0.82, 720)
                height: width
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -height * 0.08
                transformOrigin: Item.Center
                source: Quickshell.shellDir + "/assets/ragnarok/fenrir-bite.png"
                sourceClipRect: Qt.rect(fenrir.roaring ? 640 : 0, 0, 640, 640)
                smooth: true
                mipmap: true
                opacity: 0
                scale: 0.58
            }

            // The screen's own jaws: black gums with ivory teeth, closing from above and below.
            Repeater {
                model: ["upper", "lower"]
                Item {
                    id: jaw
                    required property string modelData
                    readonly property bool upper: modelData === "upper"
                    readonly property real teeth: Math.max(60, Math.min(fenrir.side * 0.18, 220))
                    property real closed: 0
                    x: -fenrir.width * 0.03
                    width: fenrir.width * 1.06
                    height: fenrir.height * 0.56
                    y: upper ? -height * 1.25 * (1 - closed) : fenrir.height - height + height * 1.25 * (1 - closed)
                    visible: closed > 0
                    Rectangle { anchors.fill: parent; color: "#020304" }
                    Canvas {
                        width: parent.width
                        height: jaw.teeth
                        y: jaw.upper ? parent.height - 2 : -height + 2
                        rotation: jaw.upper ? 0 : 180
                        onPaint: {
                            // The website's tooth outline: x and depth in percent of the row.
                            var outline = [[100, 0], [98, 55], [94, 12], [89, 92], [84, 12], [79, 58], [74, 8], [68, 74], [63, 9], [57, 52], [52, 5],
                                           [47, 62], [42, 9], [36, 73], [31, 8], [25, 56], [20, 12], [14, 95], [9, 12], [4, 60]];
                            var context = getContext("2d");
                            context.reset();
                            var enamel = context.createLinearGradient(0, 0, 0, height);
                            enamel.addColorStop(0, "#72818c");
                            enamel.addColorStop(0.45, "#e9e1c9");
                            enamel.addColorStop(1, "#b4b5ab");
                            context.fillStyle = enamel;
                            context.beginPath();
                            context.moveTo(0, 0);
                            outline.forEach(point => context.lineTo(width * point[0] / 100, height * point[1] / 100));
                            context.closePath();
                            context.fill();
                        }
                    }
                    Connections {
                        target: fenrir
                        function onStageChanged() {
                            if (fenrir.stage === "biting") bite.restart();
                            else if (fenrir.stage === "fenrir") jaw.closed = 0;
                        }
                    }
                    NumberAnimation { id: bite; target: jaw; property: "closed"; from: 0; to: 1; duration: 420; easing.type: Easing.InQuad }
                }
            }

            Rectangle { id: darkness; anchors.fill: parent; color: "black"; opacity: 0 }
        }

        SequentialAnimation {
            id: choreography
            ScriptAction { script: { face.opacity = 0; face.scale = 0.58; darkness.opacity = 0; scene.forceActiveFocus(); } }
            ParallelAnimation {
                NumberAnimation { target: scene; property: "opacity"; from: 0; to: 1; duration: 350 }
                NumberAnimation { target: face; property: "opacity"; to: 1; duration: 450 }
                NumberAnimation { target: face; property: "scale"; to: 1; duration: 1200; easing.type: Easing.OutQuint }
                SequentialAnimation {
                    PauseAnimation { duration: 650 }
                    ScriptAction { script: fenrir.roaring = true }
                    PauseAnimation { duration: 400 }
                    ScriptAction { script: fenrir.roaring = false }
                    PauseAnimation { duration: 300 }
                    ScriptAction { script: fenrir.roaring = true }
                    PauseAnimation { duration: 400 }
                }
            }
            ScriptAction { script: fenrir.stage = "lunging" }
            ParallelAnimation {
                SequentialAnimation {
                    NumberAnimation { target: face; property: "scale"; to: 0.92; duration: 170 }
                    NumberAnimation { target: face; property: "scale"; to: 7; duration: 610; easing.type: Easing.InCubic }
                }
                SequentialAnimation {
                    PauseAnimation { duration: 500 }
                    ScriptAction { script: fenrir.stage = "biting" }
                    NumberAnimation { target: face; property: "opacity"; to: 0; duration: 280 }
                }
            }
            PauseAnimation { duration: 170 }
            ScriptAction { script: fenrir.stage = "swallowed" }
            NumberAnimation { target: darkness; property: "opacity"; to: 1; duration: 180 }
            PauseAnimation { duration: 700 }
            ScriptAction { script: fenrir.dismiss() }
        }
        SequentialAnimation {
            id: ending
            NumberAnimation { target: scene; property: "opacity"; to: 0; duration: 600 }
            ScriptAction { script: fenrir.stage = "idle" }
        }
    }
}
