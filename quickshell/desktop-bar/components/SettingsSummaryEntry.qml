import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../settings/SettingsCatalog.js" as Catalog

// One helper item on a System page: its detail line, then a row per action with the
// action's button (and its choice list, when it needs one) at the row's right edge.
Column {
    id: entry
    required property var item
    required property var context
    width: parent ? parent.width : 0
    spacing: 5
    SettingsText {
        visible: text !== ""
        text: Eitr.I18n.tr(entry.item.detail || "Unavailable")
        color: Qt.alpha(entry.context.foreground, PanelStyle.secondaryTextOpacity)
        font.pixelSize: PanelStyle.captionSize
    }
    Repeater {
        model: entry.item.controls || (entry.item.actionMenu ? [entry.item] : [])
        Item {
            id: actionRow
            required property var modelData
            readonly property bool picks: (modelData.options || []).length > 0
            property string selection: (modelData.options || [])[0] || ""
            readonly property string title: modelData.label || Eitr.I18n.tr(modelData.title)
            width: entry.width
            height: picks ? choiceRow.height : plainRow.height
            SettingsTarget {
                objectName: {
                    const setting = Catalog.settings.find(candidate => candidate.page === entry.context.page && candidate.label === actionRow.modelData.title);
                    return setting ? "setting-" + setting.id : "";
                }
            }
            ControlRow {
                id: plainRow
                visible: !actionRow.picks
                width: parent.width
                text: actionRow.title
                description: Eitr.I18n.tr(actionRow.modelData.detail || "")
                foreground: entry.context.foreground
                controlWidth: 120
                PanelButton {
                    anchors.right: parent.right
                    width: 120
                    text: Eitr.I18n.tr("Open")
                    foreground: entry.context.foreground
                    available: !entry.context.helper.busy
                    onClicked: entry.context.runControl(actionRow.modelData, "")
                }
            }
            // A choice list uses the outlined dropdown, its title on the border, with Open beside it.
            Row {
                id: choiceRow
                visible: actionRow.picks
                width: parent.width
                spacing: 8
                ChoiceDropdown {
                    id: choice
                    width: Math.min(460, choiceRow.width - 128)
                    floatingLabel: actionRow.title
                    helperText: Eitr.I18n.tr(actionRow.modelData.detail || "")
                    foreground: entry.context.foreground; background: entry.context.background; gold: SettingsInk.gold
                    choices: (actionRow.modelData.options || []).map(option => ({value: option, label: option}))
                    current: actionRow.selection
                    onChosen: value => actionRow.selection = value
                }
                PanelButton {
                    y: choice.labelRoom
                    width: 120
                    text: Eitr.I18n.tr("Open")
                    foreground: entry.context.foreground
                    available: !entry.context.helper.busy && (!["Remove Folder", "Set Existing SSH Key"].includes(actionRow.modelData.title) || actionRow.selection !== "")
                    onClicked: entry.context.runControl(actionRow.modelData, actionRow.selection)
                }
            }
        }
    }
}
