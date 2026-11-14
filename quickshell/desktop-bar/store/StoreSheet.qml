import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    id: root
    required property var catalog
    property string heading: ""
    property string description: ""
    property string confirmText: ""
    property real sheetWidth: Math.min(520, width - 48)
    property real sheetHeight: body.implicitHeight + 124
    default property alias content: body.data
    z: 3; anchors.fill: parent; color: catalog.background
    MouseArea { anchors.fill: parent }
    Rectangle {
        anchors.centerIn: parent; width: root.sheetWidth; height: root.sheetHeight
        radius: DesktopStyle.radius(12); color: root.catalog.surface
        border.width: 1; border.color: root.catalog.line
        Column {
            id: body
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            anchors.margins: 24; spacing: 18
            StoreLabel { catalog: root.catalog; width: parent.width; font.family: SiteStyle.carved; font.pixelSize: PanelStyle.headingSize; font.weight: Font.Medium; text: root.heading }
            StoreLabel { catalog: root.catalog; width: parent.width; text: root.description; color: root.catalog.muted }
        }
        Row {
            anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 24; spacing: 8
            StoreActionButton { catalog: root.catalog; width: 100; available: !root.catalog.busy; text: Eitr.I18n.tr("Cancel"); onClicked: root.catalog.cancelSheet() }
            StoreActionButton { catalog: root.catalog; width: 100; available: !root.catalog.busy; primary: true; text: root.confirmText; onClicked: root.catalog.confirm() }
        }
    }
}
