import ".."
import QtQuick
import QtQuick.Layouts
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: row
    required property var catalog
    required property var item
    property var change: null
    property bool checked: true
    property bool expanded: false
    property bool canUpdate: true
    readonly property var kind: catalog.kinds.find(entry => entry.id === item.storeKind)
    readonly property int count: (catalog.updateCache[item.storeKind] || {})[item.id] || 0
    readonly property string version: change && change.before && change.after && change.before !== change.after
        ? change.before + " → " + change.after : ""
    readonly property var permissions: change && change.permissions
    readonly property string kindLabel: {
        switch (item.storeKind) {
        case "plugins": return Eitr.I18n.tr("Plugin");
        case "themes": return Eitr.I18n.tr("Theme");
        case "lockscreens": return Eitr.I18n.tr("Lockscreen");
        case "wallpapers": return Eitr.I18n.tr("Wallpaper");
        }
        return "";
    }

    signal toggleChecked()
    signal toggleExpanded()
    signal moveFocus(int delta)
    signal updateRequested()

    objectName: "store-update-" + item.id
    activeFocusOnTab: true
    Keys.onUpPressed: moveFocus(-1)
    Keys.onDownPressed: moveFocus(1)
    Keys.onSpacePressed: toggleChecked()
    Keys.onRightPressed: if (!expanded) toggleExpanded()
    Keys.onReturnPressed: toggleExpanded()
    Keys.onEnterPressed: toggleExpanded()
    Accessible.role: Accessible.CheckBox
    Accessible.name: (item.name || "") + " · " + kindLabel
    Accessible.checked: checked
    Accessible.onToggleAction: toggleChecked()
    spacing: PanelStyle.selectionRowGap

    Rectangle {
        width: parent.width
        // Two lines (name and version) need more room than a one-line selection row.
        implicitHeight: Math.max(52, controls.implicitHeight + 12)
        height: implicitHeight
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(catalog.foreground, PanelStyle.selectionAlpha(row.checked, hover.hovered || row.activeFocus))
        border.width: row.activeFocus ? 1 : PanelStyle.selectionBorderWidth(row.checked)
        border.color: row.activeFocus ? catalog.accent : Qt.alpha(catalog.foreground, PanelStyle.selectionBorderAlpha)
        HoverHandler { id: hover }

        RowLayout {
            id: controls
            anchors.fill: parent
            anchors.leftMargin: PanelStyle.selectionActionInset + 2
            anchors.rightMargin: PanelStyle.selectionActionInset + 2
            spacing: PanelStyle.selectionActionGap
            PanelButton {
                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                activeFocusOnTab: false
                foreground: catalog.foreground
                icon: true; iconSize: PanelStyle.selectionIconSize
                text: row.checked ? "\u{F0132}" : "\u{F0131}"
                Accessible.role: Accessible.CheckBox
                Accessible.name: row.Accessible.name
                Accessible.checked: row.checked
                onClicked: { row.forceActiveFocus(); row.toggleChecked(); }
            }
            StoreLabel {
                catalog: row.catalog
                font.family: PanelStyle.fontFamily
                font.pixelSize: PanelStyle.selectionIconSize
                text: row.kind ? String.fromCodePoint(parseInt(row.kind.icon, 16)) : ""
            }
            Column {
                Layout.fillWidth: true
                spacing: PanelStyle.selectionDetailGap
                StoreLabel {
                    catalog: row.catalog
                    width: parent.width; elide: Text.ElideRight; wrapMode: Text.NoWrap
                    text: row.item.name || ""
                }
                StoreLabel {
                    catalog: row.catalog
                    width: parent.width; elide: Text.ElideRight; wrapMode: Text.NoWrap
                    color: catalog.muted; font.pixelSize: PanelStyle.captionSize
                    text: row.version || (row.count === 1 ? Eitr.I18n.tr("1 change") : Eitr.I18n.tr("%1 changes").arg(row.count))
                }
                TapHandler { onTapped: { row.forceActiveFocus(); row.toggleExpanded(); } }
            }
            StorePill { catalog: row.catalog; text: row.kindLabel }
            PanelButton {
                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                foreground: catalog.foreground
                text: row.expanded ? "⌄" : ">"
                Accessible.name: row.expanded ? Eitr.I18n.tr("Hide changes") : Eitr.I18n.tr("Show changes")
                onClicked: { row.forceActiveFocus(); row.toggleExpanded(); }
            }
            StoreActionButton {
                id: update
                catalog: row.catalog
                objectName: "update-" + row.item.id
                Layout.preferredWidth: updateLabel.advanceWidth + 24
                available: row.canUpdate
                text: Eitr.I18n.tr("Update")
                onClicked: row.updateRequested()
                TextMetrics { id: updateLabel; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: update.text }
            }
        }
    }
    Rectangle {
        visible: row.expanded
        width: parent.width
        height: details.implicitHeight
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(catalog.foreground, 0.04)
        border.width: 1
        border.color: Qt.alpha(catalog.foreground, PanelStyle.selectionBorderAlpha)
        readonly property var permissionLines: {
            const permissions = row.permissions;
            if (!row.expanded || !permissions) return [];
            const lines = [];
            if (permissions.capabilities.length) lines.push(Eitr.I18n.tr("New capabilities: %1").arg(permissions.capabilities.join(", ")));
            if (permissions.packages.length) lines.push(Eitr.I18n.tr("New system packages: %1").arg(permissions.packages.join(", ")));
            if (permissions.service) lines.push(Eitr.I18n.tr("New or changed service"));
            if (permissions.hooks.length) lines.push(Eitr.I18n.tr("New or changed hooks: %1").arg(permissions.hooks.join(", ")));
            return lines;
        }

        Column {
            id: details
            width: parent.width
            padding: PanelStyle.selectionInset + 4
            spacing: PanelStyle.selectionRowGap

            StoreLabel {
                catalog: row.catalog
                width: parent.width - parent.padding * 2
                visible: text !== ""
                text: row.change ? row.change.error || row.version : Eitr.I18n.tr("Loading…")
            }
            StoreLabel {
                catalog: row.catalog
                visible: Boolean(row.change && (row.change.commits || []).length)
                color: catalog.muted; font.pixelSize: PanelStyle.captionSize
                text: Eitr.I18n.tr("Changes")
            }
            Repeater {
                model: row.expanded && row.change ? row.change.commits || [] : []
                StoreLabel {
                    required property var modelData
                    catalog: row.catalog
                    width: details.width - details.padding * 2
                    text: modelData.date + " · " + modelData.subject
                }
            }
            StoreLabel {
                catalog: row.catalog
                width: parent.width - parent.padding * 2
                visible: text !== ""
                text: row.change && row.change.more ? Eitr.I18n.tr("and %1 more").arg(row.change.more) : ""
                color: catalog.muted
            }
            StoreLabel {
                catalog: row.catalog
                visible: Boolean(row.permissions)
                color: catalog.muted; font.pixelSize: PanelStyle.captionSize
                text: Eitr.I18n.tr("What it asks for")
            }
            Repeater {
                model: parent.parent.permissionLines
                StoreLabel {
                    required property string modelData
                    catalog: row.catalog
                    width: details.width - details.padding * 2
                    text: modelData
                    color: catalog.accent
                }
            }
            StoreLabel {
                catalog: row.catalog
                visible: Boolean(row.permissions) && parent.parent.permissionLines.length === 0
                width: parent.width - parent.padding * 2
                text: Eitr.I18n.tr("No new permissions")
                color: catalog.muted
            }
        }
    }
}
