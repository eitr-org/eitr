import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// Fill the icon slot with this overlay. The pill sits on the glyph's top-right corner and may
// overhang the slot; the slot itself never changes size, so bar items do not shift.
Item {
    id: badge
    property int count: 0
    property color accent: "white"
    // A thin ring in the bar's colour cuts the pill out of the glyph it overlaps.
    property color ring: "transparent"
    visible: count > 0

    Rectangle {
        visible: badge.ring.a > 0
        x: pill.x - 1.5; y: pill.y - 1.5
        width: pill.width + 3; height: pill.height + 3
        radius: height / 2
        color: badge.ring
    }
    Rectangle {
        id: pill
        height: 11
        width: Math.max(height, label.implicitWidth + 4)
        x: badge.width / 2 + 3
        y: Math.max(0, Math.floor(badge.height / 2 - 12))
        radius: height / 2
        color: badge.accent

        Text {
            id: label
            anchors.centerIn: parent
            text: badge.count > 99 ? "99+" : String(badge.count)
            color: PanelStyle.readableInk(badge.accent, Qt.rgba(1, 1, 1, 1), Qt.rgba(0, 0, 0, 1))
            font.family: DesktopFonts.family
            font.pixelSize: 9
            font.bold: true
        }
    }
}
