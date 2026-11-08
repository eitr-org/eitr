import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../settings/SettingsIndex.js" as SettingsIndex

// The Settings window in miniature: the shared sidebar with the real page list under
// its rune group captions, and the Sound page's header and cards. Sidebar parts are
// labelled on the left, page parts on the right. Static example state.
Item {
    id: figure
    readonly property real minimumWidth: 620
    readonly property color ink: SettingsPalette.foreground
    readonly property real labels: 124
    readonly property real zoom: Math.min(0.85, (width - 2 * labels) / window.width)
    readonly property real windowLeft: (width - window.width * zoom) / 2
    readonly property real windowRight: windowLeft + window.width * zoom
    implicitHeight: window.height * zoom
    // A point inside the window, in figure coordinates.
    function pointX(x) { return windowLeft + x * zoom; }
    function pointY(y) { return y * zoom; }

    Rectangle {
        id: window
        x: figure.windowLeft
        width: 640; height: 400
        scale: figure.zoom; transformOrigin: Item.TopLeft
        radius: DesktopStyle.radius(12)
        color: SettingsPalette.background
        border.width: 1; border.color: SettingsPalette.line
        clip: true
        FamilySidebar {
            id: sidebar
            x: 14; y: 14; width: 214; height: window.height - 28
            foreground: figure.ink; background: SettingsPalette.background; accent: SettingsPalette.accent
            interactive: false
            subtitle: Eitr.I18n.tr("Settings")
            placeholder: Eitr.I18n.tr("Search settings")
            currentId: "sound"
            entries: SettingsIndex.pages.map(page => {
                const group = SettingsIndex.groupFor(page);
                return {id: page.id, title: Eitr.I18n.tr(page.title), rune: page.rune, group: Eitr.I18n.tr(group.name), groupRune: group.rune};
            })
        }
        Rectangle { x: sidebar.x + sidebar.width + 14; y: 0; width: 1; height: window.height; color: Qt.alpha(figure.ink, PanelStyle.dividerAlpha) }
        Column {
            id: page
            x: sidebar.x + sidebar.width + 32; y: 22
            width: window.width - x - 20
            spacing: 16
            FamilyPageHeader {
                id: header
                foreground: figure.ink
                rune: SettingsIndex.groupFor(SettingsIndex.entry("sound")).rune
                group: Eitr.I18n.tr("Devices")
                title: Eitr.I18n.tr("Sound")
                description: Eitr.I18n.tr("Output, input and event sounds.")
            }
            ControlCard {
                id: outputCard
                title: Eitr.I18n.tr("Output")
                foreground: figure.ink
                surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
                ControlRow {
                    text: Eitr.I18n.tr("Volume"); description: ""
                    foreground: figure.ink
                    PanelSlider { width: parent.width; from: 0; to: 100; value: 60; foreground: figure.ink; accent: SettingsPalette.accent }
                }
            }
            ControlCard {
                id: soundsCard
                title: Eitr.I18n.tr("Event sounds")
                foreground: figure.ink
                surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
                ToggleRow {
                    id: switchRow
                    text: Eitr.I18n.tr("Notification sounds")
                    description: Eitr.I18n.tr("Play a sound with notification popups.")
                    foreground: figure.ink; accent: SettingsPalette.accent
                    checked: true
                }
            }
        }
    }
    FigureCallout { targetX: figure.pointX(sidebar.x + 2); targetY: figure.pointY(sidebar.y + sidebar.searchField.y + sidebar.searchField.height / 2); labelX: figure.windowLeft - 24; labelY: targetY; side: "left"; text: Eitr.I18n.tr("Search") }
    FigureCallout { targetX: figure.pointX(sidebar.x - 4); targetY: figure.pointY(sidebar.y + sidebar.searchField.y + sidebar.searchField.height + 28); labelX: figure.windowLeft - 24; labelY: targetY + 24; side: "left"; text: Eitr.I18n.tr("Rune groups") }
    FigureCallout { targetX: figure.pointX(sidebar.x + 3); targetY: figure.pointY(sidebar.y + sidebar.markerY + sidebar.searchField.y + sidebar.searchField.height + 26); labelX: figure.windowLeft - 24; labelY: targetY + 30; side: "left"; text: Eitr.I18n.tr("Current page") }
    FigureCallout { targetX: figure.pointX(window.width - 30); targetY: figure.pointY(page.y + header.y + 40); labelX: figure.windowRight + 24; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Page header") }
    FigureCallout { targetX: figure.pointX(window.width - 30); targetY: figure.pointY(page.y + outputCard.y + 26); labelX: figure.windowRight + 24; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Cards") }
    FigureCallout { targetX: figure.pointX(window.width - 37); targetY: figure.pointY(page.y + soundsCard.y + 74); labelX: figure.windowRight + 24; labelY: targetY; side: "right"; text: Eitr.I18n.tr("Switch") }
}
