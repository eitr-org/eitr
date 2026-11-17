pragma ComponentBehavior: Bound
import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// Compact live schematic of the desktop bar showing how the four icon zones sit around the clock.
Rectangle {
    id: strip
    required property var zones
    required property color foreground
    required property color surface
    required property color accent
    required property color gold
    property color line: Qt.alpha(foreground, PanelStyle.dividerAlpha)
    property string hoveredId: ""
    property string grabbedId: ""
    property var hiddenIds: ({})

    function visibleZone(name) {
        const list = (zones && zones[name]) || [];
        return list.filter(entry => !hiddenIds[entry.id]);
    }

    implicitHeight: 42
    implicitWidth: 640
    height: 42
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: Qt.rgba(surface.r, surface.g, surface.b, 0.94)
    border.width: 1
    border.color: Qt.alpha(foreground, 0.16)
    clip: true

    Item {
        id: inner
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10

        Row {
            id: leftCluster
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            spacing: 4

            // Fixed chrome: logo, Overview and sample workspace markers.
            Text {
                text: "ᛖ"
                color: Qt.alpha(strip.foreground, 0.72)
                font.family: DesktopFonts.family
                font.pixelSize: 13
                font.bold: true
                width: 18; height: 22
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                text: "󰕮"
                color: Qt.alpha(strip.foreground, 0.56)
                font.family: DesktopFonts.family
                font.pixelSize: 13
                width: 18; height: 22
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Repeater {
                model: ["1", "2"]
                delegate: Rectangle {
                    required property string modelData
                    required property int index
                    width: 18; height: 18
                    radius: DesktopStyle.radius(5)
                    anchors.verticalCenter: parent.verticalCenter
                    color: index === 0 ? Qt.alpha(strip.accent, 0.35) : Qt.alpha(strip.foreground, 0.08)
                    Text {
                        anchors.centerIn: parent
                        text: parent.modelData
                        color: Qt.alpha(strip.foreground, index === 0 ? 0.95 : 0.6)
                        font.family: DesktopFonts.family
                        font.pixelSize: 10
                        font.bold: true
                    }
                }
            }
            Rectangle {
                visible: leftPreviewRow.visible
                width: 1; height: 14
                anchors.verticalCenter: parent.verticalCenter
                color: strip.line
            }
            ZoneRow {
                id: leftPreviewRow
                entries: strip.visibleZone("left")
            }
        }

        ZoneRow {
            id: clockStartPreviewRow
            anchors.right: clockBadge.left
            anchors.rightMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            entries: strip.visibleZone("clockStart")
        }

        Rectangle {
            id: clockBadge
            anchors.centerIn: parent
            height: 22
            width: clockText.implicitWidth + 14
            radius: DesktopStyle.radius(6)
            color: Qt.alpha(strip.foreground, 0.08)
            Text {
                id: clockText
                anchors.centerIn: parent
                text: "12:34"
                color: strip.foreground
                font.family: DesktopFonts.family
                font.pixelSize: 12
                font.bold: true
            }
        }

        ZoneRow {
            id: clockEndPreviewRow
            anchors.left: clockBadge.right
            anchors.leftMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            entries: strip.visibleZone("clockEnd")
        }

        ZoneRow {
            id: rightPreviewRow
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            entries: strip.visibleZone("right")
        }
    }

    component ZoneRow: Row {
        property var entries: []
        visible: entries.length > 0
        spacing: 2
        anchors.verticalCenter: parent.verticalCenter

        Repeater {
            model: entries
            delegate: Rectangle {
                required property var modelData
                readonly property bool isHighlighted: modelData.id === strip.grabbedId || modelData.id === strip.hoveredId
                width: 20; height: 22
                radius: DesktopStyle.radius(5)
                color: modelData.id === strip.grabbedId
                    ? Qt.alpha(strip.gold, 0.28)
                    : isHighlighted ? Qt.alpha(strip.foreground, 0.14) : "transparent"
                border.width: modelData.id === strip.grabbedId ? 1 : 0
                border.color: strip.gold
                Text {
                    anchors.centerIn: parent
                    text: parent.modelData.glyph || "󰐱"
                    color: parent.isHighlighted ? strip.gold : strip.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: 13
                    font.bold: true
                }
            }
        }
    }
}
