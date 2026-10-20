import QtQuick

// Normal notifications glow in the theme accent, critical ones in the theme's
// critical colour; low-priority ones have no glow.
Item {
    id: glow
    property int urgency: 1
    property color accent: "white"
    property bool shown: true
    readonly property color tint: urgency === 2 ? DesktopStyle.criticalColor : accent
    readonly property bool active: shown && urgency >= 1
    property real cornerRadius: 6
    // Inward Gaussian falloff: every band stays inside the card's own bounds.
    // No shadow texture, outside blur, input handler, or extra layout space.
    readonly property int depth: Math.min(14, Math.floor(Math.min(width, height) / 2))
    Repeater {
        model: glow.active ? glow.depth : 0
        Rectangle {
            required property int index
            objectName: "priorityGlowBand"
            x: index; y: index
            width: Math.max(0, glow.width - index * 2)
            height: Math.max(0, glow.height - index * 2)
            radius: Math.max(0, glow.cornerRadius - index)
            color: "transparent"
            antialiasing: true
            border.width: 1
            border.color: Qt.alpha(glow.tint, 0.12 * Math.exp(-index * index / 40))
        }
    }
}
