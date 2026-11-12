import ".."
import QtQuick
import QtQuick.Layouts
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The Control Center's General page in miniature, built from its own tiles, dividers
// and buttons, with its sections labelled on the right. Static example state.
Item {
    id: figure
    readonly property real minimumWidth: 600
    readonly property color ink: SettingsPalette.foreground
    readonly property color accent: SettingsPalette.accent
    readonly property real zoom: 0.82
    // Page buttons are labelled on the left, the General page's sections on the right.
    readonly property real leftLabels: Math.max(150, (width - panel.width * zoom) / 2)
    readonly property real rightLabels: panel.x + panel.width * zoom + 34
    implicitHeight: panel.height * zoom
    // A point near the right end of a content row, and a row's vertical centre, in figure coordinates.
    function rightOf(item) { return panel.x + (content.x + content.width) * zoom - 6; }
    function middleOf(item) { return (content.y + item.y + item.height / 2) * zoom; }

    component Tile: ControlCenterTile {
        toggle: true
        foreground: figure.ink; accent: figure.accent
        accentInk: PanelStyle.readableInk(figure.accent, figure.ink, SettingsPalette.background)
    }
    component Action: PanelButton {
        required property string title
        required property string glyph
        Layout.fillWidth: true; Layout.preferredWidth: 1; height: 34
        textSize: 12; iconSize: 16
        text: title; leadingIcon: glyph; foreground: figure.ink; textAlignment: Text.AlignLeft
    }
    component Level: Row {
        required property string glyph
        required property real level
        width: parent.width; spacing: 10
        Text { width: 30; height: 30; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; text: parent.glyph; color: figure.ink; font.family: DesktopFonts.family; font.pixelSize: 16 }
        PanelSlider { width: parent.width - 90; from: 0; to: 100; value: parent.level; foreground: figure.ink; accent: figure.accent }
        Text { width: 40; height: 30; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter; text: parent.level + "%"; color: figure.ink; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
    }

    Rectangle {
        id: panel
        x: figure.leftLabels
        width: 380; height: content.y + content.height + 16
        scale: figure.zoom; transformOrigin: Item.TopLeft
        radius: DesktopStyle.radius(12)
        color: SettingsPalette.background
        border.width: 1; border.color: SettingsPalette.line
        Column {
            id: pages
            x: 12; y: 16; spacing: 10
            Repeater {
                model: ["", "󰏖", "󱁤"]
                PanelButton {
                    required property string modelData
                    required property int index
                    width: 34; height: 34; icon: true; textSize: 12; iconSize: 20
                    text: modelData; selected: index === 0; foreground: figure.ink
                    EitrLogo { visible: parent.index === 0; anchors.centerIn: parent; slotWidth: 22; iconSize: 20; foreground: figure.ink; background: SettingsPalette.background; enabled: false }
                }
            }
            PanelButton { id: settingsButton; width: 34; height: 34; icon: true; iconSize: 20; text: "󰒓"; foreground: figure.ink }
        }
        Rectangle { x: pages.x + pages.width + 10; y: 12; width: 1; height: panel.height - 24; color: Qt.alpha(figure.ink, PanelStyle.dividerAlpha) }
        Column {
            id: content
            x: pages.x + pages.width + 22; y: 16
            width: panel.width - x - 16
            spacing: 12
            PanelHeading { text: Eitr.I18n.tr("General"); rune: "general"; foreground: figure.ink; accent: figure.accent }
            PanelDivider { id: connectivity; width: parent.width; text: Eitr.I18n.tr("Connectivity"); foreground: figure.ink }
            GridLayout {
                id: radios
                width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
                Tile { title: Eitr.I18n.tr("WiFi"); glyph: "󰖩"; selected: true }
                Tile { title: Eitr.I18n.tr("Bluetooth"); glyph: "󰂯"; selected: true }
                Tile { title: Eitr.I18n.tr("Airplane"); glyph: "󰀝" }
            }
            PanelDivider { id: quick; width: parent.width; text: Eitr.I18n.tr("Quick Actions"); foreground: figure.ink }
            GridLayout {
                id: toggles
                width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
                Tile { title: Eitr.I18n.tr("Idle Lock"); glyph: "󱫖"; selected: true }
                Tile { title: Eitr.I18n.tr("Do Not Disturb"); glyph: "󰂛" }
                Tile { title: Eitr.I18n.tr("Night Light"); glyph: "󰖔" }
            }
            PanelDivider { id: sound; width: parent.width; text: Eitr.I18n.tr("Sound"); foreground: figure.ink }
            Level { id: volume; glyph: "󰕾"; level: 60 }
            Level { glyph: "󰍬"; level: 80 }
            PanelDivider { id: power; width: parent.width; text: Eitr.I18n.tr("Power"); foreground: figure.ink }
            GridLayout {
                id: session
                width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
                Action { title: Eitr.I18n.tr("Lock"); glyph: "\uF023" }
                Action { title: Eitr.I18n.tr("Power…"); glyph: "\uF011" }
            }
        }
    }
    FigureCallout { targetX: panel.x + pages.x * figure.zoom + 2; targetY: (pages.y + 60) * figure.zoom; labelX: figure.leftLabels - 34; labelY: targetY; side: "left"; text: Eitr.I18n.tr("Pages") }
    FigureCallout { targetX: panel.x + pages.x * figure.zoom + 2; targetY: (pages.y + settingsButton.y + 17) * figure.zoom; labelX: figure.leftLabels - 34; labelY: targetY + 24; side: "left"; text: Eitr.I18n.tr("All settings") }
    FigureCallout { targetX: figure.rightOf(radios); targetY: (content.y + radios.y + 18) * figure.zoom; labelX: figure.rightLabels; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Connectivity") }
    FigureCallout { targetX: figure.rightOf(toggles); targetY: figure.middleOf(toggles); labelX: figure.rightLabels; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Quick Actions") }
    FigureCallout { targetX: figure.rightOf(volume); targetY: figure.middleOf(volume) + 10; labelX: figure.rightLabels; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Sound") }
    FigureCallout { targetX: figure.rightOf(session); targetY: figure.middleOf(session); labelX: figure.rightLabels; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Power") }
}
