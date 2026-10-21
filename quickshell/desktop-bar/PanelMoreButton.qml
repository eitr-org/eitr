import Eitr as Eitr
import QtQuick
import QtQuick.Controls.Basic
import "PanelStyle.js" as PanelStyle

// The "…" button of a panel header: rarer actions live here, with names, so the
// header keeps one primary control. Each action is {title, glyph, available, run}.
PanelButton {
    id: more
    required property color background
    property var actions: []
    readonly property alias popup: list
    width: 34; height: 32
    icon: true; compactIconBackground: true
    text: "\u{F01D8}"
    selected: list.opened
    Accessible.name: Eitr.I18n.tr("More actions")
    onClicked: list.opened ? list.close() : list.open()
    HoverHandler { id: moreHover }
    BarTooltip { target: more; hovered: moreHover.hovered && !list.opened; text: Eitr.I18n.tr("More actions"); foreground: more.foreground; background: more.background }

    Popup {
        id: list
        y: more.height + 6
        x: more.width - width
        width: 260
        padding: 6
        // Outside the button only: a press on "…" itself must not close the menu
        // just before its click toggles it open again.
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        onOpened: rows.forceActiveFocus()
        background: Rectangle {
            radius: DesktopStyle.radius(PanelStyle.controlRadius + 4)
            color: more.background
            border.width: 1
            border.color: Qt.alpha(more.foreground, PanelStyle.selectionBorderAlpha)
        }
        contentItem: Column {
            id: rows
            spacing: 2
            Repeater {
                model: more.actions
                PanelButton {
                    required property var modelData
                    width: rows.width; height: PanelStyle.selectionRowHeight
                    text: modelData.title; leadingIcon: modelData.glyph || ""
                    textSize: PanelStyle.bodySize; iconSize: 16
                    textAlignment: Text.AlignLeft; flat: true
                    available: modelData.available !== false
                    foreground: more.foreground
                    onClicked: { list.close(); modelData.run(); }
                }
            }
        }
    }
}
