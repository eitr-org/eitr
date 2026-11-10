import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Walker's Settings menu in miniature, drawn after its shared row layout: the search
// field, submenu rows ending in ">" listed first, then actions with a description
// below their title. The rows match elephant/menu-rows/settings.json.
Item {
    id: figure
    readonly property real minimumWidth: 560
    readonly property color ink: SettingsPalette.foreground
    readonly property real labels: 170
    readonly property real menuLeft: Math.max(0, (width - menu.width - labels) / 2)
    implicitHeight: menu.height
    // The vertical centre of a row in figure coordinates: submenu rows are 32 px, actions 44 px.
    function rowMiddle(index) {
        const submenus = entries.filter(entry => !entry.description).length;
        const above = Math.min(index, submenus) * 34 + Math.max(0, index - submenus) * 46;
        return menu.y + rows.y + above + (index < submenus ? 16 : 22);
    }
    readonly property var entries: [
        {text: Eitr.I18n.tr("Devices"), icon: "\u{F0379}"},
        {text: Eitr.I18n.tr("Desktop"), icon: "\u{EBCF}"},
        {text: Eitr.I18n.tr("Apps & Keys"), icon: "\u{F030C}"},
        {text: Eitr.I18n.tr("Accounts & Security"), icon: "\u{F0483}"},
        {text: Eitr.I18n.tr("System"), icon: "\u{F013}"},
        {text: Eitr.I18n.tr("Control Center"), icon: "\u{F0493}", description: Eitr.I18n.tr("Open quick toggles, media and tools")},
        {text: Eitr.I18n.tr("Dotfiles"), icon: "\u{E5FC}", description: Eitr.I18n.tr("Open your configuration folder in an editor")}
    ]

    Rectangle {
        id: menu
        x: figure.menuLeft
        width: 430; height: rows.y + rows.height + 10
        radius: DesktopStyle.radius(8)
        color: SettingsPalette.background
        border.width: 1; border.color: SettingsPalette.line
        Rectangle {
            id: search
            x: 10; y: 10; width: parent.width - 20; height: 40
            radius: DesktopStyle.radius(6)
            color: Qt.alpha(figure.ink, 0.05)
            border.width: 1; border.color: Qt.alpha(SettingsInk.gold, 0.5)
            Text {
                x: 12; anchors.verticalCenter: parent.verticalCenter
                text: "Search..."
                color: figure.ink; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: 16
            }
        }
        Column {
            id: rows
            x: 10; y: search.y + search.height + 8
            width: parent.width - 20
            spacing: 2
            Repeater {
                model: figure.entries
                Rectangle {
                    id: row
                    required property var modelData
                    required property int index
                    readonly property bool submenu: !modelData.description
                    width: rows.width; height: submenu ? 32 : 44
                    radius: DesktopStyle.radius(6)
                    color: index === 0 ? Qt.alpha(SettingsPalette.accent, 0.22) : "transparent"
                    Text {
                        x: 8; width: 22; anchors.verticalCenter: parent.verticalCenter
                        horizontalAlignment: Text.AlignHCenter
                        text: row.modelData.icon; color: figure.ink
                        font.family: DesktopFonts.family; font.pixelSize: 16
                    }
                    Column {
                        x: 40; width: parent.width - x - 30; anchors.verticalCenter: parent.verticalCenter
                        Text { width: parent.width; text: row.modelData.text; elide: Text.ElideRight; color: figure.ink; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                        Text { visible: !row.submenu; width: parent.width; text: row.modelData.description || ""; elide: Text.ElideRight; color: figure.ink; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                    }
                    Text {
                        visible: row.submenu
                        anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
                        text: ">"; color: figure.ink; opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                    }
                }
            }
        }
    }
    readonly property real labelX: menu.x + menu.width + 30
    FigureCallout { targetX: menu.x + menu.width - 14; targetY: menu.y + search.y + search.height / 2; labelX: figure.labelX; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Search") }
    FigureCallout { targetX: menu.x + menu.width - 6; targetY: figure.rowMiddle(0); labelX: figure.labelX; labelY: targetY + 10; side: "right"; text: Eitr.I18n.tr("Selected row") }
    FigureCallout { targetX: menu.x + menu.width - 6; targetY: figure.rowMiddle(3); labelX: figure.labelX; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Submenu") }
    FigureCallout { targetX: menu.x + menu.width - 30; targetY: figure.rowMiddle(6) + 8; labelX: figure.labelX; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Action and description") }
}
