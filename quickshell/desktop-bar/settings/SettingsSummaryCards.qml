import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The cards of the helper-backed System pages: one card per item.
Column {
    id: summary
    required property var context
    readonly property var view: context
    width: parent ? parent.width : 0
    spacing: 12
    Repeater {
        model: ["keybinds", "security", "assistant", "about"].includes(summary.view.page) ? summary.view.matches : []
        ControlCard {
            id: summaryCard
            required property var modelData
            required property int index
            title: Eitr.I18n.tr(modelData.title)
            foreground: summary.view.foreground
            surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
            spacing: 5
            SettingsText {
                visible: summary.view.page === "keybinds" && (summaryCard.index === 0 || summary.view.matches[summaryCard.index - 1].group !== summaryCard.modelData.group)
                text: summaryCard.modelData.group || ""
                font.pixelSize: PanelStyle.captionSize
                color: Qt.alpha(summary.view.foreground, PanelStyle.secondaryTextOpacity)
            }
            SettingsSummaryEntry { item: summaryCard.modelData; context: summary.context }
        }
    }
}
