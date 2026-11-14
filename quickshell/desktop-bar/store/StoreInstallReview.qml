import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

StoreSheet {
    id: root
    visible: catalog.reviewing
    sheetWidth: width - 72
    sheetHeight: 440
    heading: catalog.kind === "wallpapers" ? Eitr.I18n.tr("Review wallpaper installation") : Eitr.I18n.tr("Review theme installation")
    description: catalog.kind === "wallpapers" ? Eitr.I18n.tr("Data-only images · Review selected sources") : Eitr.I18n.tr("Data-only themes · Review selected sources")
    confirmText: Eitr.I18n.tr("Install")
    ListView {
        width: parent.width; height: 190; orientation: ListView.Horizontal; spacing: 12; clip: true
        model: root.catalog.reviewing ? root.catalog.chosen : []; boundsBehavior: Flickable.StopAtBounds
        delegate: Column {
            id: entry
            required property var modelData
            width: 200; spacing: 8
            StorePreview { catalog: root.catalog; width: 200; height: 112; source: root.catalog.imageFor(entry.modelData) }
            StoreLabel { catalog: root.catalog; width: parent.width; text: entry.modelData.repository || "eitr-org/eitr-themes"; font.pixelSize: 11; elide: Text.ElideMiddle }
            StoreLabel { catalog: root.catalog; width: parent.width; text: entry.modelData.name; maximumLineCount: 1; elide: Text.ElideRight; font.bold: true }
            StoreLabel { catalog: root.catalog; text: root.catalog.sizeText(entry.modelData.size || 0); font.pixelSize: PanelStyle.captionSize; color: root.catalog.muted }
        }
    }
    StoreLabel { catalog: root.catalog; width: parent.width; text: root.catalog.busy ? root.catalog.progress : root.catalog.error || Eitr.I18n.tr("Total download: %1").arg(root.catalog.sizeText(root.catalog.totalSize)) }
    ProgressBar { width: parent.width; height: 6; visible: root.catalog.busy; indeterminate: true; palette.highlight: root.catalog.accent; palette.base: Qt.alpha(root.catalog.foreground, 0.08) }
}
