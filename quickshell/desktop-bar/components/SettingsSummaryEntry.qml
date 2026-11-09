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
        ControlRow {
            SettingsTarget {
                objectName: {
                    const setting = Catalog.settings.find(candidate => candidate.page === entry.context.page && candidate.label === actionRow.modelData.title);
                    return setting ? "setting-" + setting.id : "";
                }
            }
            id: actionRow
            required property var modelData
            readonly property bool picks: (modelData.options || []).length > 0
            property string selection: (modelData.options || [])[0] || ""
            text: modelData.label || Eitr.I18n.tr(modelData.title)
            description: Eitr.I18n.tr(modelData.detail || "")
            foreground: entry.context.foreground
            controlWidth: picks ? Math.min(360, width * 0.5) : 120
            Row {
                anchors.right: parent.right
                spacing: 8
                ChoiceDropdown {
                    visible: actionRow.picks
                    width: visible ? actionRow.controlWidth - 128 : 0
                    foreground: entry.context.foreground; background: entry.context.background; gold: SettingsInk.gold
                    choices: (actionRow.modelData.options || []).map(option => ({value: option, label: option}))
                    current: actionRow.selection
                    onChosen: value => actionRow.selection = value
                }
                PanelButton {
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
