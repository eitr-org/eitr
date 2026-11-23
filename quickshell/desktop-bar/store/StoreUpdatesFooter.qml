import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

PanelButton {
    id: card
    required property var catalog
    readonly property int count: catalog.updateItems.length
    readonly property var status: catalog.updateCheck
    readonly property bool found: !status.pending && count > 0
    readonly property string kinds: catalog.kinds.filter(kind => catalog.updateItems.some(item => item.storeKind === kind.id))
        .map(kind => Eitr.I18n.tr(kind.label)).join(" · ")
    objectName: "store-updates-footer"
    implicitHeight: 60
    height: implicitHeight
    text: ""
    available: !catalog.busy
    foreground: catalog.foreground
    selected: catalog.tab === "updates"
    color: Qt.alpha(found ? catalog.accent : foreground, PanelStyle.selectionAlpha(found || selected, hover.hovered || activeFocus))
    border.width: activeFocus || found ? 1 : PanelStyle.selectionBorderWidth(selected)
    border.color: activeFocus || found ? catalog.accent : Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)
    Accessible.name: title.text + (caption.text ? " · " + caption.text : "") + (kindLabel.visible ? " · " + kinds : "")
    Accessible.role: Accessible.Button
    onClicked: catalog.tab = "updates"

    HoverHandler { id: hover }
    Column {
        x: PanelStyle.selectionInset
        width: parent.width - x - 25
        anchors.verticalCenter: parent.verticalCenter
        spacing: PanelStyle.selectionDetailGap
        StoreLabel {
            id: title
            catalog: card.catalog
            width: parent.width; elide: Text.ElideRight; wrapMode: Text.NoWrap
            text: card.status.pending ? Eitr.I18n.tr("Checking for updates…") : card.found ? Eitr.I18n.tr("Updates available")
                : card.status.error ? Eitr.I18n.tr("Update check failed") : card.status.date ? Eitr.I18n.tr("Up to date") : Eitr.I18n.tr("Updates")
        }
        StoreLabel {
            id: caption
            catalog: card.catalog
            width: parent.width; elide: Text.ElideRight; wrapMode: Text.NoWrap
            visible: text !== ""
            color: catalog.muted
            font.pixelSize: PanelStyle.captionSize
            text: card.found ? (card.count === 1 ? Eitr.I18n.tr("1 update") : Eitr.I18n.tr("%1 updates").arg(card.count))
                : !card.status.pending && card.status.date ? Eitr.I18n.tr("Last checked %1").arg(card.status.date.toLocaleDateString(Qt.locale(Eitr.I18n.locale), "d MMM") + ", " + card.status.date.toLocaleTimeString(Qt.locale(Eitr.I18n.locale), Locale.ShortFormat)) : ""
        }
        StoreLabel {
            id: kindLabel
            catalog: card.catalog
            visible: card.found
            width: parent.width; elide: Text.ElideRight; wrapMode: Text.NoWrap
            color: catalog.muted
            font.pixelSize: PanelStyle.captionSize
            text: card.kinds
        }
    }
    StoreLabel {
        catalog: card.catalog
        anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionInset
        anchors.verticalCenter: parent.verticalCenter
        text: ">"
        color: card.found ? catalog.foreground : catalog.muted
    }
}
