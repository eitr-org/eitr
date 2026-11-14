import ".."
import QtQuick
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Item {
    id: entry
    property var choice: null
    required property color foreground
    property string placeholder: ""
    readonly property string iconName: choice && choice.icon ? String(choice.icon) : ""
    Image {
        id: image
        x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter
        width: PanelStyle.selectionIconSize; height: width
        source: entry.iconName.startsWith("/") ? "file://" + entry.iconName : entry.iconName.startsWith("file:") ? entry.iconName : entry.iconName ? Quickshell.iconPath(entry.iconName, true) : ""
        visible: status === Image.Ready
    }
    Text {
        x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter
        width: PanelStyle.selectionIconSize; horizontalAlignment: Text.AlignHCenter
        visible: !image.visible; text: "\uf2d0"; color: entry.foreground
        font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
    }
    Column {
        x: PanelStyle.selectionTextInset; width: parent.width - x - PanelStyle.selectionInset
        anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionDetailGap
        Text { width: parent.width; text: entry.choice ? Eitr.I18n.tr(String(entry.choice.label ?? entry.choice.name ?? entry.choice)) : entry.placeholder; color: entry.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; elide: Text.ElideRight }
        Text { width: parent.width; visible: text !== ""; text: entry.choice ? entry.choice.description || "" : ""; color: Qt.alpha(entry.foreground, PanelStyle.secondaryTextOpacity); font.family: DesktopFonts.family; font.pixelSize: 11; elide: Text.ElideRight }
    }
}
