pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

Column {
    id: manager
    required property color foreground
    required property color background
    required property color accent
    property var installed: PluginRegistry.installed
    property var entries: PluginRegistry.entries
    property string expanded: ""
    spacing: PanelStyle.selectionRowGap
    Flow {
        width: parent.width
        spacing: PanelStyle.selectionActionGap
        PanelButton {
            id: addButton
            width: Math.max(68, addMetrics.width + 20)
            TextMetrics { id: addMetrics; text: addButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
            text: Eitr.I18n.tr("Add Plugin…"); foreground: manager.foreground
            onClicked: PluginRegistry.review("add", "")
        }
        PanelButton {
            id: editButton
            width: Math.max(68, editMetrics.width + 20)
            TextMetrics { id: editMetrics; text: editButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
            text: PluginRegistry.editing ? Eitr.I18n.tr("Done editing widgets") : Eitr.I18n.tr("Edit widgets")
            foreground: manager.foreground
            onClicked: { PluginRegistry.editTarget = null; PluginRegistry.editing = !PluginRegistry.editing; }
        }
    }
    Text {
        visible: manager.installed.length === 0
        text: Eitr.I18n.tr("No plugins installed")
        color: manager.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    Text {
        width: manager.width; wrapMode: Text.Wrap
        text: Eitr.I18n.tr("Above-window widgets are click-through. Use this page or Edit widgets for their options.")
        color: manager.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
    Repeater {
        model: manager.installed
        Rectangle {
            id: card
            required property var modelData
            width: manager.width; height: body.implicitHeight + 20
            color: Qt.alpha(manager.foreground, PanelStyle.selectionAlpha(false, false))
            border.color: Qt.alpha(manager.foreground, PanelStyle.selectionBorderAlpha); border.width: 1
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            Column {
                id: body
                x: PanelStyle.selectionInset; y: PanelStyle.selectionInset
                width: card.width - 2 * PanelStyle.selectionInset
                spacing: PanelStyle.selectionRowGap
                Item {
                    width: body.width; height: 48
                    Image {
                        id: icon
                        width: 40; height: 40; anchors.verticalCenter: parent.verticalCenter
                        source: card.modelData.icon || ""; fillMode: Image.PreserveAspectFit
                        sourceSize.width: 80; sourceSize.height: 80
                    }
                    Text {
                        visible: icon.status !== Image.Ready; width: 40; height: 40
                        text: "󰏖"; color: manager.foreground; font.pixelSize: 28
                        font.family: PanelStyle.fontFamily; horizontalAlignment: Text.AlignHCenter
                    }
                    Column {
                        x: 48; width: Math.max(0, enabledSwitch.x - x - 6)
                        anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionDetailGap
                        Text {
                            width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText
                            text: card.modelData.name; color: manager.foreground
                            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                        }
                        Text {
                            width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText
                            text: card.modelData.author + " · " + card.modelData.version
                            color: manager.foreground; opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                        }
                    }
                    PanelSwitch {
                        id: enabledSwitch
                        anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                        checked: card.modelData.enabled
                        enabled: !card.modelData.blocked || card.modelData.blocked === "disabled"
                        foreground: manager.foreground; accent: manager.accent
                        Accessible.name: Eitr.I18n.tr("Enable plugin")
                        onClicked: PluginRegistry.setEnabled(card.modelData.id, checked)
                    }
                }
                Text {
                    width: parent.width; wrapMode: Text.Wrap; textFormat: Text.PlainText
                    text: card.modelData.description; color: manager.foreground
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                Text {
                    width: parent.width; wrapMode: Text.Wrap
                    text: !card.modelData.enabled ? Eitr.I18n.tr("Disabled") : card.modelData.visualsDisabled ? Eitr.I18n.tr("Visuals disabled after failures") : card.modelData.blocked ? Eitr.I18n.tr("Blocked") : Eitr.I18n.tr("Enabled")
                    color: manager.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
                Flow {
                    width: parent.width
                    spacing: PanelStyle.selectionActionGap
                    PanelButton {
                        id: updateButton
            width: Math.max(68, updateMetrics.width + 20)
                        TextMetrics { id: updateMetrics; text: updateButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                        text: Eitr.I18n.tr("Update"); foreground: manager.foreground; onClicked: PluginRegistry.review("update", card.modelData.id) }
                    PanelButton {
                        id: removeButton
            width: Math.max(68, removeMetrics.width + 20)
                        TextMetrics { id: removeMetrics; text: removeButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                        text: Eitr.I18n.tr("Remove"); foreground: manager.foreground; onClicked: PluginRegistry.review("remove", card.modelData.id) }
                    PanelButton {
                        id: previewButton
            width: Math.max(68, previewMetrics.width + 20)
                        TextMetrics { id: previewMetrics; text: previewButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                        visible: !!card.modelData.preview; text: Eitr.I18n.tr("Preview"); foreground: manager.foreground
                        onClicked: manager.expanded = manager.expanded === card.modelData.id ? "" : card.modelData.id
                    }
                }
                Image {
                    width: parent.width; height: visible ? Math.min(220, width * (sourceSize.height || 1) / (sourceSize.width || 1)) : 0
                    visible: manager.expanded === card.modelData.id && !!card.modelData.preview
                    source: card.modelData.preview || ""; fillMode: Image.PreserveAspectFit
                }
                PluginManagement {
                    width: parent.width
                    entries: manager.entries.filter(entry => entry.plugin === card.modelData.id)
                    foreground: manager.foreground; background: manager.background
                }
            }
        }
    }
}
