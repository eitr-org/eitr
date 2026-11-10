import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: manager
    required property color foreground
    required property color background
    required property color accent
    property var installed: PluginRegistry.installed
    property var entries: PluginRegistry.entries
    property string selectedPlugin: ""
    readonly property var selected: installed.find(plugin => plugin.id === selectedPlugin) || null
    onInstalledChanged: if (selectedPlugin && !selected) selectedPlugin = ""
    function reset() {
        selectedPlugin = "";
    }
    function back() {
        if (!selectedPlugin) return false;
        selectedPlugin = "";
        return true;
    }
    spacing: PanelStyle.selectionRowGap
    Flow {
        visible: !manager.selected
        width: parent.width
        spacing: PanelStyle.selectionActionGap
        PanelButton {
            id: addButton
            width: Math.max(68, addMetrics.width + 20)
            TextMetrics { id: addMetrics; text: addButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
            text: Eitr.I18n.tr("Add Plugins"); foreground: manager.foreground
            onClicked: PluginRegistry.review("add", "")
        }
        PanelButton {
            id: updateAllButton
            width: Math.max(68, updateAllMetrics.width + 20)
            TextMetrics { id: updateAllMetrics; text: updateAllButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
            visible: manager.installed.some(plugin => plugin.updateCount > 0)
            text: Eitr.I18n.tr("Update Plugins"); foreground: manager.foreground
            onClicked: PluginRegistry.review("update", "")
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
        visible: !manager.selected && manager.installed.length === 0
        text: Eitr.I18n.tr("No plugins installed")
        color: manager.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    Text {
        visible: !manager.selected
        width: manager.width; wrapMode: Text.Wrap
        text: Eitr.I18n.tr("Above-window widgets are click-through. Use this page or Edit widgets for their options.")
        color: manager.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
    Repeater {
        model: manager.selected ? [] : manager.installed
        Rectangle {
            id: pluginRow
            required property var modelData
            readonly property var diagnostics: PluginRegistry.pluginErrors(modelData.id)
            width: manager.width; height: diagnostics.length ? 72 : PanelStyle.selectionRowHeight
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(manager.foreground, PanelStyle.selectionAlpha(false, rowHover.hovered))
            border.width: PanelStyle.selectionBorderWidth(false)
            border.color: Qt.alpha(manager.foreground, PanelStyle.selectionBorderAlpha)
            Image {
                asynchronous: true
                id: rowIcon
                x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter
                width: PanelStyle.selectionIconSize; height: width
                source: pluginRow.modelData.icon || ""; fillMode: Image.PreserveAspectFit
            }
            Text {
                visible: rowIcon.status !== Image.Ready
                x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter
                text: "󰏖"; color: manager.foreground
                font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
            }
            Column {
                x: PanelStyle.selectionTextInset; anchors.verticalCenter: parent.verticalCenter
                width: rowSwitch.x - x - PanelStyle.selectionActionGap
                spacing: PanelStyle.selectionDetailGap
                Text {
                    width: parent.width
                    text: pluginRow.modelData.name + (pluginRow.modelData.updateCount > 0 ? " · ↑" : "")
                    textFormat: Text.PlainText; elide: Text.ElideRight
                    color: manager.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                Text {
                    visible: pluginRow.diagnostics.length > 0
                    width: parent.width; text: Eitr.I18n.tr("This plugin has errors")
                    textFormat: Text.PlainText; elide: Text.ElideRight
                    color: manager.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
                Text {
                    visible: pluginRow.diagnostics.length > 0
                    width: parent.width; text: pluginRow.diagnostics[0]?.message || ""
                    textFormat: Text.PlainText; elide: Text.ElideRight
                    color: manager.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
            }
            HoverHandler { id: rowHover }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: manager.selectedPlugin = pluginRow.modelData.id
            }
            Accessible.role: Accessible.Button
            Accessible.name: modelData.name + (diagnostics.length ? " · " + Eitr.I18n.tr("This plugin has errors") + ": " + diagnostics[0].message : "") + (modelData.updateCount > 0 ? " · " + Eitr.I18n.tr("Update available") : "")
            Accessible.onPressAction: manager.selectedPlugin = modelData.id
            activeFocusOnTab: true
            Keys.onReturnPressed: manager.selectedPlugin = modelData.id
            Keys.onSpacePressed: manager.selectedPlugin = modelData.id
            PanelSwitch {
                id: rowSwitch
                anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset
                anchors.verticalCenter: parent.verticalCenter
                checked: pluginRow.modelData.enabled
                enabled: !pluginRow.modelData.blocked || pluginRow.modelData.blocked === "disabled"
                foreground: manager.foreground; accent: manager.accent
                Accessible.name: Eitr.I18n.tr("Enable plugin")
                onClicked: PluginRegistry.setEnabled(pluginRow.modelData.id, checked)
            }
        }
    }
    Row {
        visible: !!manager.selected
        width: parent.width; spacing: PanelStyle.selectionActionGap
        PanelButton {
            width: 28; height: 28; icon: true; text: "󰅁"
            foreground: manager.foreground; Accessible.name: Eitr.I18n.tr("Back")
            onClicked: manager.back()
        }
        Text {
            width: parent.width - 34; height: 28; verticalAlignment: Text.AlignVCenter
            text: manager.selected ? manager.selected.name : ""
            textFormat: Text.PlainText; elide: Text.ElideRight
            color: manager.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize
        }
    }
    Repeater {
        model: manager.selected ? [manager.selected] : []
        // The Repeater fills PluginDetails' own required modelData.
        PluginDetails {
            width: manager.width
            entries: manager.entries.filter(entry => entry.plugin === modelData.id)
            foreground: manager.foreground; background: manager.background; accent: manager.accent
        }
    }
}
