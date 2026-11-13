import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// One installed plugin: name, author and switch, its desktop widgets and bar icons with
// their settings, Update and Remove. Control Center's Plugins page and the
// Add-ons window both show it.
Rectangle {
    id: card
    required property var modelData
    required property var entries
    required property color foreground
    required property color background
    required property color accent
    property bool showPreview: false
    // A host with its own review flow (the Add-ons window) handles these; otherwise
    // they open the reviewed terminal flows.
    property var updateAction: null
    property var removeAction: null
    // Without a frame inside a host that already draws its own card.
    property bool framed: true
    property bool showErrors: false
    onModelDataChanged: { showPreview = false; showErrors = false; }
    height: body.implicitHeight + (framed ? 20 : 0)
    color: framed ? Qt.alpha(card.foreground, PanelStyle.selectionAlpha(false, false)) : "transparent"
    border.color: Qt.alpha(card.foreground, PanelStyle.selectionBorderAlpha); border.width: framed ? 1 : 0
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    Column {
        id: body
        x: card.framed ? PanelStyle.selectionInset : 0; y: x
        width: card.width - 2 * x
        spacing: PanelStyle.selectionRowGap
        Item {
            width: body.width; height: 48
            Image {
                asynchronous: true
                id: icon
                width: 40; height: 40; anchors.verticalCenter: parent.verticalCenter
                source: card.modelData.icon || ""; fillMode: Image.PreserveAspectFit
                sourceSize.width: 80; sourceSize.height: 80
            }
            Text {
                visible: icon.status !== Image.Ready; width: 40; height: 40
                text: "󰏖"; color: card.foreground; font.pixelSize: 28
                font.family: PanelStyle.fontFamily; horizontalAlignment: Text.AlignHCenter
            }
            Column {
                x: 48; width: Math.max(0, enabledSwitch.x - x - 6)
                anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionDetailGap
                Text {
                    width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText
                    text: card.modelData.name; color: card.foreground
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                Text {
                    width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText
                    text: card.modelData.author + " · " + card.modelData.version + (card.modelData.official ? " · " + Eitr.I18n.tr("Official") : "")
                    color: card.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
            }
            PanelSwitch {
                id: enabledSwitch
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                checked: card.modelData.enabled
                enabled: !card.modelData.blocked || card.modelData.blocked === "disabled"
                foreground: card.foreground; accent: card.accent
                Accessible.name: Eitr.I18n.tr("Enable plugin")
                onClicked: PluginRegistry.setEnabled(card.modelData.id, checked)
            }
        }
        Text {
            width: parent.width; wrapMode: Text.Wrap; textFormat: Text.PlainText
            text: card.modelData.description; color: card.foreground
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        // Only an unusual state is spelled out; the switch already shows on or off.
        Text {
            visible: text !== ""
            width: parent.width; wrapMode: Text.Wrap
            text: !card.modelData.enabled ? Eitr.I18n.tr("Disabled") : card.modelData.blocked ? Eitr.I18n.tr("Blocked") : ""
            color: card.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        Text {
            visible: card.modelData.updateCount > 0
            text: "↑ " + Eitr.I18n.tr("Update available")
            color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        Text {
            visible: PluginRegistry.pluginErrors(card.modelData.id).length > 0
            width: parent.width; wrapMode: Text.Wrap; textFormat: Text.PlainText
            text: Eitr.I18n.tr("This plugin has errors") + "\n" + (PluginRegistry.pluginErrors(card.modelData.id)[0]?.message || "")
            color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        PanelButton {
            visible: PluginRegistry.pluginErrors(card.modelData.id).length > 0
            width: parent.width
            text: Eitr.I18n.tr("View error details"); foreground: card.foreground
            onClicked: card.showErrors = !card.showErrors
        }
        TextEdit {
            visible: card.showErrors
            width: parent.width; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap
            textFormat: TextEdit.PlainText
            text: PluginRegistry.errorDetails(card.modelData.id)
            color: card.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        PluginManagement {
            width: parent.width
            entries: card.entries.filter(entry => entry.plugin === card.modelData.id)
            foreground: card.foreground; background: card.background; accent: card.accent
        }
        PanelDivider { width: parent.width; foreground: card.foreground }
        // Everyday actions on the left; Remove, with its confirmation, apart on the right.
        Item {
            width: parent.width; height: removeButton.height
            Row {
                spacing: PanelStyle.selectionActionGap
                PanelButton {
                    id: updateButton
                    visible: card.modelData.updateCount > 0
                    width: Math.max(68, updateMetrics.advanceWidth + 24)
                    TextMetrics { id: updateMetrics; text: updateButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                    text: Eitr.I18n.tr("Update"); foreground: card.foreground
                    onClicked: card.updateAction ? card.updateAction(card.modelData) : PluginRegistry.review("update", card.modelData.id)
                }
                PanelButton {
                    id: previewButton
                    visible: !!card.modelData.preview
                    width: Math.max(68, previewMetrics.advanceWidth + 24)
                    TextMetrics { id: previewMetrics; text: previewButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                    text: Eitr.I18n.tr("Preview"); foreground: card.foreground
                    onClicked: card.showPreview = !card.showPreview
                }
            }
            PanelButton {
                id: removeButton
                anchors.right: parent.right
                width: Math.max(68, removeMetrics.advanceWidth + 24)
                TextMetrics { id: removeMetrics; text: removeButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
                outlined: true
                text: Eitr.I18n.tr("Remove"); foreground: card.foreground
                onClicked: card.removeAction ? card.removeAction(card.modelData) : PluginRegistry.review("remove", card.modelData.id)
            }
        }
        Image {
            asynchronous: true
            width: parent.width; height: visible ? 220 : 0
            visible: card.showPreview && !!card.modelData.preview
            source: card.modelData.preview || ""; fillMode: Image.PreserveAspectFit
        }
    }
}
