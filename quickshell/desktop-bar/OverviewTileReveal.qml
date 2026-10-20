import QtQuick

Item {
    id: reveal
    property bool opened: false
    property int order: 0
    property real elapsed: 0
    readonly property real phase: Math.max(0, Math.min(1, (elapsed - order * 55) / 260))
    readonly property real progress: opened ? 1 - Math.pow(1 - phase, 3) : 0
    opacity: progress
    scale: 0.96 + progress * 0.04
    transform: Translate { y: 12 * (1 - reveal.progress) }

}
