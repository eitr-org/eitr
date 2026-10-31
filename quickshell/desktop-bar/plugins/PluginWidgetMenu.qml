import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: menu
    required property color foreground
    required property color background
    property bool aboveWindows: false
    property string surface: "none"
    property var entries: []
    signal action(string action)
    signal selected(string id)
    spacing: PanelStyle.selectionRowGap
    readonly property var actions: [
        {id: "edit", text: Eitr.I18n.tr("Edit position")},
        {id: "smaller", text: Eitr.I18n.tr("Size: Smaller")},
        {id: "larger", text: Eitr.I18n.tr("Size: Larger")},
        {id: "full", text: Eitr.I18n.tr("Full width")},
        {id: "panel", text: Eitr.I18n.tr("Background: Panel"), checked: surface === "panel"},
        {id: "none", text: Eitr.I18n.tr("Background: Transparent"), checked: surface === "none"},
        {id: "layer", text: Eitr.I18n.tr("Show above windows"), checked: aboveWindows}]
    Repeater {
        model: menu.actions.concat(menu.entries.map(entry => ({id: entry.id, text: entry.text, checked: entry.checked, plugin: true})),
            [{id: "remove", text: Eitr.I18n.tr("Remove from desktop")}])
        PanelButton {
            required property var modelData
            width: menu.width; height: PanelStyle.selectionRowHeight
            flat: true
            foreground: menu.foreground; textAlignment: Text.AlignLeft
            text: (modelData.checked ? "✓ " : "") + modelData.text
            onClicked: modelData.plugin ? menu.selected(modelData.id) : menu.action(modelData.id)
        }
    }
}
