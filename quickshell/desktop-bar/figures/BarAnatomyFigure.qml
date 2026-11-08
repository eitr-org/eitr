import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The Full bar along the top of a desktop, with its parts labelled. Static example
// state: the first workspace active, music playing, the right-side icons shown.
Item {
    id: figure
    readonly property real minimumWidth: 680
    readonly property color ink: SettingsPalette.foreground
    readonly property color surface: SettingsPalette.background
    readonly property color accent: SettingsPalette.accent
    readonly property real slot: 24
    implicitHeight: screen.y + screen.height
    // The centre of an item in the bar, in figure coordinates.
    function along(item, row) { return bar.x + row.x + item.x + item.width / 2; }
    readonly property real barTop: screen.y + 3
    readonly property real barBottom: screen.y + bar.height - 3

    component Glyph: Text {
        width: figure.slot; height: figure.slot
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        color: figure.ink
        font.family: DesktopFonts.family; font.pixelSize: 16
    }
    Rectangle {
        id: screen
        y: 58
        width: parent.width; height: 120
        radius: DesktopStyle.radius(10)
        color: Qt.tint(figure.surface, Qt.alpha(figure.accent, 0.14))
        border.width: 1; border.color: SettingsPalette.line
        clip: true
        Rectangle {
            id: bar
            width: parent.width; height: 32
            color: figure.surface
            Rectangle { y: parent.height - 1; width: parent.width; height: 1; color: SettingsPalette.line }
            Row {
                id: left
                x: 8; anchors.verticalCenter: parent.verticalCenter
                spacing: 4
                EitrLogo { id: logo; slotWidth: figure.slot; iconSize: 20; foreground: figure.ink; background: figure.surface; enabled: false; anchors.verticalCenter: parent.verticalCenter }
                Glyph { id: overview; text: "󰕮" }
                Row {
                    id: workspaces
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2
                    Repeater {
                        model: 5
                        WorkspaceMarker {
                            required property int index
                            style: "Runes"; label: String(index + 1); active: index === 0
                            width: figure.slot - 2; height: figure.slot
                            foreground: figure.ink; accent: figure.accent; selectedForeground: figure.surface
                        }
                    }
                }
                Item { width: 6; height: 1 }
                Row {
                    id: monitors
                    Glyph { text: "\uF080" }
                    Glyph { text: "󰍛" }
                    Glyph { text: "󱫗" }
                }
            }
            Row {
                id: middle
                x: (bar.width - clock.width) / 2 - media.width - spacing
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12
                Item {
                    id: media
                    width: 44; height: figure.slot
                    MediaPreview {
                        anchors.centerIn: parent
                        width: 88; height: 48; scale: 0.5
                        foreground: figure.ink; gold: figure.ink; raised: "transparent"
                    }
                }
                Text {
                    id: clock
                    height: figure.slot; verticalAlignment: Text.AlignVCenter
                    text: "12:34 PM"
                    color: figure.ink
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.bold: true
                }
                Text {
                    id: weather
                    height: figure.slot; verticalAlignment: Text.AlignVCenter
                    text: "󰖙 18°"
                    color: figure.ink
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
            }
            Row {
                id: right
                x: bar.width - width - 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4
                Glyph { id: toggle; text: "›"; font.pixelSize: 21 }
                Row {
                    id: status
                    Glyph { text: "󰖩" }
                    Glyph { text: "󰂯" }
                    Glyph { text: "󰕾" }
                    Glyph { text: "󰌌" }
                    Glyph { text: "󰚰" }
                    Glyph { text: "󰁹" }
                }
                Glyph { id: bell; text: "󰂜" }
            }
        }
    }
    FigureCallout { targetX: figure.along(logo, left); targetY: figure.barTop; labelX: targetX - 6; labelY: 46; side: "top"; text: Eitr.I18n.tr("Control Center") }
    FigureCallout { targetX: figure.along(workspaces, left); targetY: figure.barTop; labelX: targetX + 12; labelY: 20; side: "top"; text: Eitr.I18n.tr("Workspaces") }
    FigureCallout { targetX: figure.along(media, middle); targetY: figure.barTop; labelX: targetX - 10; labelY: 46; side: "top"; text: Eitr.I18n.tr("Media") }
    FigureCallout { targetX: figure.along(toggle, right); targetY: figure.barTop; labelX: targetX - 16; labelY: 46; side: "top"; text: Eitr.I18n.tr("Show icons") }
    FigureCallout { targetX: figure.along(bell, right); targetY: figure.barTop; labelX: targetX; labelY: 20; side: "top"; text: Eitr.I18n.tr("Notifications") }
    FigureCallout { targetX: figure.along(overview, left); targetY: figure.barBottom; labelX: targetX - 14; labelY: screen.y + 44; side: "bottom"; text: Eitr.I18n.tr("Overview") }
    FigureCallout { targetX: figure.along(monitors, left); targetY: figure.barBottom; labelX: targetX + 10; labelY: screen.y + 44; side: "bottom"; text: [Eitr.I18n.tr("AI Usage"), Eitr.I18n.tr("Hardware"), Eitr.I18n.tr("Idle Lock")].join("\n") }
    FigureCallout { targetX: bar.x + middle.x + clock.x + clock.width; targetY: figure.barBottom; labelX: targetX + 52; labelY: screen.y + 44; side: "bottom"; text: Eitr.I18n.tr("Clock") + " · " + Eitr.I18n.tr("Weather") }
    FigureCallout { targetX: figure.along(status, right); targetY: figure.barBottom; labelX: targetX; labelY: screen.y + 44; side: "bottom"; text: Eitr.I18n.tr("Status icons") }
}
