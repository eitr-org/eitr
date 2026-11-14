import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    required property var catalog

    id: selectionBar
    readonly property bool shown: catalog.getMore && catalog.chosen.length > 0 && catalog.capabilities.useOnClick && !catalog.capabilities.needsAdministrator && !catalog.reviewing
    visible: opacity > 0
    opacity: shown ? 1 : 0
    z: 2
    x: catalog.sidebarWidth + ((catalog.width - catalog.sidebarWidth - PanelStyle.padding) - width) / 2
    anchors.bottom: parent.bottom
    anchors.bottomMargin: PanelStyle.padding + (shown ? 0 : -12)
    width: Math.min(catalog.scroll.width - 24, 540); height: 56
    radius: DesktopStyle.radius(12); color: Qt.rgba(catalog.raised.r, catalog.raised.g, catalog.raised.b, 1)
    border.width: 1; border.color: catalog.lineStrong
    Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(160) } }
    Behavior on anchors.bottomMargin { NumberAnimation { duration: DesktopStyle.motionDuration(160) } }
    Column {
        x: 16; anchors.verticalCenter: parent.verticalCenter; width: clearSelection.x - x - 12; spacing: 1
        StoreLabel { catalog: selectionBar.catalog; width: parent.width; wrapMode: Text.NoWrap; elide: Text.ElideRight; text: Eitr.I18n.tr("Selected") + " · " + catalog.chosen.length }
        StoreLabel { catalog: selectionBar.catalog; width: parent.width; wrapMode: Text.NoWrap; elide: Text.ElideRight; color: catalog.muted; font.pixelSize: PanelStyle.captionSize; text: catalog.sizeText(catalog.totalSize) }
    }
    StoreActionButton { catalog: selectionBar.catalog; id: clearSelection; anchors.right: reviewSelection.left; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 80; text: Eitr.I18n.tr("Clear"); onClicked: catalog.selected = [] }
    TextMetrics { id: reviewLabel; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: Eitr.I18n.tr("Review & install") }
    StoreActionButton { catalog: selectionBar.catalog; id: reviewSelection; objectName: "review-selection"; anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; width: Math.max(150, reviewLabel.advanceWidth + 32); primary: true; text: Eitr.I18n.tr("Review & install"); onClicked: { catalog.reviewing = true; catalog.forceActiveFocus(); } }
}
