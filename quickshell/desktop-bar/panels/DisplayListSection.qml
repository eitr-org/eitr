import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import Quickshell

Column {
    id: content
    required property var menu
    required property var trialOperation
    required property var setPrimary
    width: parent.width
    spacing: 12
    visible: content.menu.settingsSection !== "nightlight"
    Item {
        width: content.width
        height: visible ? 28 : 0
        visible: content.menu.settingsSection !== "nightlight"
        Text { anchors.verticalCenter: parent.verticalCenter; text: Eitr.I18n.tr("Displays"); color: content.menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    }
    Text { visible: content.menu.settingsSection !== "nightlight" && content.menu.displayError !== ""; text: content.menu.displayError; color: content.menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    Text {
        visible: content.menu.settingsSection !== "nightlight" && content.menu.monitors.length === 0
        height: visible ? 36 : 0
        text: Eitr.I18n.tr("No active displays")
        color: content.menu.foreground
        opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
    }
    MonitorMap {
        width: content.width
        height: visible ? implicitHeight : 0
        // The map is a Settings view; the bar's Display panel keeps to the list.
        visible: content.menu.embedded && content.menu.settingsSection !== "nightlight"
        compact: false
        monitors: content.menu.monitors
        settings: content.menu.displaySettings.monitors || []
        pending: content.menu.pendingMonitor
        primary: content.menu.primaryDisplay
        selected: content.menu.settingsFor
        foreground: content.menu.foreground; background: content.menu.background; accent: content.menu.accent
        gold: content.menu.mapHighlight
        onSelectedMonitor: name => { content.menu.settingsFor = name; content.menu.refreshDisplaySettings(); }
    }
    // One display per row, or two side by side when Settings is wide.
    Flow {
    id: displayList
    readonly property int columns: content.width >= 1100 ? 2 : 1
    readonly property real entryWidth: (content.width - (columns - 1) * spacing) / columns
    visible: content.menu.settingsSection !== "nightlight"
    width: content.width; spacing: PanelStyle.selectionRowGap
    Repeater {
        model: content.menu.monitors
        // Each display's row; when selected, its settings open right under it.
        Item {
        id: displayEntry
        required property var modelData
        readonly property bool editing: content.menu.settingsFor === modelData.name
        readonly property bool isMain: modelData.name === content.menu.primaryDisplay
        // An open display sits on its own card, so it is clear which one the settings belong to.
        readonly property real cardInset: editing ? 8 : 0
        width: displayList.entryWidth
        height: entryColumn.implicitHeight + cardInset * 2
        Rectangle {
            anchors.fill: parent
            visible: displayEntry.editing
            radius: DesktopStyle.radius(PanelStyle.controlRadius + 4)
            color: Qt.alpha(content.menu.foreground, 0.04)
            border.width: 1
            border.color: Qt.alpha(content.menu.accent, 0.45)
        }
        Column {
        id: entryColumn
        x: displayEntry.cardInset; y: displayEntry.cardInset
        width: displayEntry.width - displayEntry.cardInset * 2
        spacing: 10
        Rectangle {
            width: parent.width
            height: PanelStyle.selectionRowHeight
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(content.menu.foreground, PanelStyle.selectionAlpha(displayEntry.editing, displayHover.hovered))
            border.width: PanelStyle.selectionBorderWidth(displayEntry.editing)
            border.color: Qt.alpha(content.menu.foreground, PanelStyle.selectionBorderAlpha)
            HoverHandler { id: displayHover; cursorShape: Qt.PointingHandCursor }
            TapHandler {
                onTapped: {
                    content.menu.settingsFor = displayEntry.editing ? "" : displayEntry.modelData.name;
                    if (content.menu.settingsFor) content.menu.refreshDisplaySettings();
                }
            }
            BarTooltip { target: parent; hovered: displayHover.hovered; text: displayEntry.editing ? Eitr.I18n.tr("Close its settings") : Eitr.I18n.tr("Resolution, position and more"); background: content.menu.background; foreground: content.menu.foreground }
            Row {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 10
                spacing: 8
                Text { width: 22; height: parent.height; text: "󰍹"; verticalAlignment: Text.AlignVCenter; color: displayEntry.editing ? content.menu.accent : content.menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 16 }
                Text { width: parent.width - 250; height: parent.height; text: displayEntry.modelData.name + (displayEntry.modelData.model ? " · " + displayEntry.modelData.model : ""); elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter; color: content.menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                // Beside the name, well clear of the resolution on the right.
                Text { width: 62; height: parent.height; text: displayEntry.isMain ? Eitr.I18n.tr("Main") : ""; horizontalAlignment: Text.AlignLeft; verticalAlignment: Text.AlignVCenter; color: content.menu.accent; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.bold: true }
                Text { width: 112; height: parent.height; text: Eitr.I18n.tr("{width}×{height} · {rate} Hz", {width: displayEntry.modelData.width, height: displayEntry.modelData.height, rate: Math.round(displayEntry.modelData.refreshRate)}); horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter; color: content.menu.foreground; opacity: 0.75; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                Text { width: 16; height: parent.height; text: displayEntry.editing ? "󰅀" : "󰅂"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; color: content.menu.accent; font.family: DesktopFonts.family; font.pixelSize: 16 }
            }
        }
        DisplaySettingsEditor {
            readonly property var details: (content.menu.displaySettings.monitors || []).find(item => item.name === displayEntry.modelData.name)
            visible: displayEntry.editing && !!details
            height: visible ? implicitHeight : 0
            width: parent.width
            monitor: details || ({})
            others: content.menu.monitors.map(item => item.name).filter(name => name !== displayEntry.modelData.name)
            placeable: content.menu.placeableBeside(displayEntry.modelData.name)
            isMain: displayEntry.isMain
            foreground: content.menu.foreground
            background: content.menu.background
            accent: content.menu.accent
            busy: content.trialOperation.running || content.setPrimary.running || content.menu.trialSeconds > 0
            onTryChange: function(key, value) { content.menu.trySetting(displayEntry.modelData.name, key, value); }
            onMakeMain: content.menu.selectPrimary(displayEntry.modelData.name)
        }
        }
        }
    }
    }
    // Display layout belongs with the displays, not on the Night Light tab.
    PanelFooterLink {
        id: handEditButton
        visible: content.menu.settingsSection !== "nightlight"
        width: content.width
        text: Eitr.I18n.tr("Edit layout by hand…")
        foreground: content.menu.foreground
        onClicked: Quickshell.execDetached(["python3", content.menu.settingsHelper, "edit"])
        HoverHandler { id: handEditHover }
        BarTooltip { target: handEditButton; hovered: handEditHover.hovered; text: Eitr.I18n.tr("Pixel offsets, flipped screens and more in local.lua"); background: content.menu.background; foreground: content.menu.foreground }
    }
}
