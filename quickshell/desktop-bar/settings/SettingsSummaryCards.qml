import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The cards of the helper-backed System pages: one card per item, or on Git & Cloud one
// card per provider with each identity, profile or context as a row inside it.
Column {
    id: summary
    required property var context
    readonly property var view: context
    readonly property bool grouped: view.page === "git-cloud"
    width: parent ? parent.width : 0
    spacing: 12
    function cards() {
        if (!grouped) return view.matches;
        const groups = [];
        for (const item of view.matches) {
            const key = item.provider || item.menu || item.title;
            let group = groups.find(candidate => candidate.key === key);
            if (!group) {
                group = {key: key, title: item.providerTitle || item.title, entries: []};
                groups.push(group);
            }
            group.entries.push(item);
        }
        return groups;
    }
    Repeater {
        model: ["keybinds", "git-cloud", "security", "assistant", "about"].includes(summary.view.page) ? summary.cards() : []
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
            Repeater {
                model: summaryCard.modelData.entries || [summaryCard.modelData]
                Column {
                    id: entryBlock
                    required property var modelData
                    required property int index
                    width: parent.width
                    spacing: 5
                    Rectangle {
                        visible: summary.grouped && entryBlock.index > 0
                        width: parent.width; height: visible ? 1 : 0
                        color: Qt.alpha(summary.view.foreground, PanelStyle.dividerAlpha)
                    }
                    SettingsText {
                        visible: summary.grouped
                        text: entryBlock.modelData.title
                        textFormat: Text.PlainText
                        topPadding: entryBlock.index > 0 ? 6 : 0
                    }
                    SettingsSummaryEntry { item: entryBlock.modelData; context: summary.context }
                }
            }
        }
    }
}
