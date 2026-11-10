import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// One placed desktop widget in Control Center > Plugins: which display it is on, Edit
// position and Remove, then its settings as visible controls. The desktop right-click
// menu (PluginWidgetMenu) offers the same actions.
Rectangle {
    id: card
    required property var entry
    required property string monitor
    required property string monitorLabel
    required property color foreground
    required property color background
    required property color accent
    readonly property var placement: (PluginRegistry.placements.widgets || []).find(placement => placement.plugin === entry.plugin && placement.id === entry.id && placement.monitor === monitor)
    readonly property bool aboveWindows: !!placement && !!placement.aboveWindows
    readonly property string surface: PluginRegistry.widgetSurface(Object.assign({}, entry, {geometry: placement}))
    readonly property var options: PluginRegistry.widgetMenus[PluginRegistry.menuKey(entry, monitor)] || []
    readonly property bool editing: PluginRegistry.editing && PluginRegistry.editTarget !== null && PluginRegistry.editTarget.plugin === entry.plugin
        && PluginRegistry.editTarget.id === entry.id && PluginRegistry.editTarget.monitor === monitor
    function act(action) { PluginRegistry.widgetAction(entry.plugin, entry.id, monitor, action, false); }

    // A text button sized to its label, so translations never clip.
    component LabelButton: PanelButton {
        width: Math.max(56, labelMetrics.advanceWidth + 24)
        foreground: card.foreground
        TextMetrics { id: labelMetrics; text: parent.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
    }

    width: parent ? parent.width : 0
    implicitHeight: content.implicitHeight + 2 * PanelStyle.selectionActionInset
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: Qt.alpha(foreground, PanelStyle.selectionAlpha(false, false))
    border.width: PanelStyle.selectionBorderWidth(false)
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)

    Column {
        id: content
        x: PanelStyle.selectionActionInset; y: PanelStyle.selectionActionInset
        width: card.width - 2 * x
        spacing: PanelStyle.selectionRowGap
        Item {
            width: parent.width; height: PanelStyle.selectionRowHeight
            Text {
                x: PanelStyle.selectionInset - PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter
                text: "󰍹"; color: card.foreground
                font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
            }
            Text {
                x: PanelStyle.selectionTextInset - PanelStyle.selectionActionInset
                width: actions.x - x - PanelStyle.selectionActionGap
                anchors.verticalCenter: parent.verticalCenter
                text: card.monitorLabel; textFormat: Text.PlainText; elide: Text.ElideRight
                color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            }
            Row {
                id: actions
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                spacing: PanelStyle.selectionActionGap
                LabelButton {
                    text: card.editing ? Eitr.I18n.tr("Done") : Eitr.I18n.tr("Edit position")
                    onClicked: {
                        const wasEditing = card.editing;
                        PluginRegistry.editTarget = {plugin: card.entry.plugin, id: card.entry.id, monitor: card.monitor};
                        PluginRegistry.editing = !wasEditing;
                    }
                }
                PanelButton {
                    width: 24; height: 24; icon: true; text: "󰅖"; foreground: card.foreground
                    readonly property string label: Eitr.I18n.tr("Remove from desktop")
                    Accessible.name: label
                    onClicked: PluginRegistry.change("unplace", card.entry, card.monitor, null)
                    HoverHandler { id: removeHover }
                    BarTooltip { target: parent; hovered: removeHover.hovered; text: parent.label; foreground: card.foreground; background: card.background }
                }
            }
        }
        ControlRow {
            visible: card.options.length > 0
            text: Eitr.I18n.tr("Style"); description: ""; foreground: card.foreground
            Flow {
                width: parent.width; spacing: PanelStyle.selectionActionGap
                Repeater {
                    model: card.options
                    LabelButton {
                        required property var modelData
                        text: modelData.text; selected: !!modelData.checked; outlined: !modelData.checked
                        onClicked: PluginRegistry.widgetAction(card.entry.plugin, card.entry.id, card.monitor, modelData.id, true)
                    }
                }
            }
        }
        ControlRow {
            text: Eitr.I18n.tr("Background"); description: ""; foreground: card.foreground
            ChoiceSegmented {
                width: parent.width; foreground: card.foreground
                choices: [{id: "panel", label: Eitr.I18n.tr("Panel")}, {id: "none", label: Eitr.I18n.tr("Transparent")}]
                current: card.surface
                onChosen: value => PluginRegistry.change("surface", card.entry, card.monitor, null, value)
            }
        }
        ControlRow {
            text: Eitr.I18n.tr("Size"); description: ""; foreground: card.foreground
            Row {
                spacing: PanelStyle.selectionActionGap
                LabelButton { text: "−"; outlined: true; Accessible.name: Eitr.I18n.tr("Smaller"); onClicked: card.act("smaller") }
                LabelButton { text: "+"; outlined: true; Accessible.name: Eitr.I18n.tr("Larger"); onClicked: card.act("larger") }
                LabelButton { text: Eitr.I18n.tr("Full width"); outlined: true; onClicked: card.act("full") }
            }
        }
        ToggleRow {
            width: parent.width
            text: Eitr.I18n.tr("Show above windows")
            description: ""
            foreground: card.foreground; accent: card.accent
            checked: card.aboveWindows
            onToggled: PluginRegistry.change("toggle-layer", card.entry, card.monitor, null)
        }
    }
}
