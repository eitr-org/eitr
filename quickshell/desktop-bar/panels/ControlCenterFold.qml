import ".."
pragma ComponentBehavior: Bound
import QtQuick
import "../PanelStyle.js" as PanelStyle

Item {
    required property var centerRef
    id: fold
    required property string title
    property bool startOpen: false
    default property alias body: foldBody.data
    readonly property bool open: fold.centerRef.folds[title] === undefined ? startOpen : fold.centerRef.folds[title]
    width: parent ? parent.width : 0
    implicitHeight: foldHeader.height + (open ? foldBody.implicitHeight + PanelStyle.selectionInset * 2 : 0)
    Rectangle {
        anchors.fill: parent
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(fold.centerRef.foreground, PanelStyle.selectionAlpha(false, false))
        border.width: 1; border.color: Qt.alpha(fold.centerRef.foreground, PanelStyle.dividerAlpha)
    }
    Rectangle {
        id: foldHeader
        width: parent.width; height: 34
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(fold.centerRef.foreground, foldMouse.containsMouse ? PanelStyle.selectionAlpha(false, true) : 0)
        Text {
            x: 12; width: parent.width - 42; anchors.verticalCenter: parent.verticalCenter
            elide: Text.ElideRight
            text: fold.title.toUpperCase(); color: fold.centerRef.foreground
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.bold: true; font.letterSpacing: 0.6
        }
        Text {
            anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
            text: fold.open ? "󰅀" : "󰅂"; color: fold.centerRef.accent
            font.family: DesktopFonts.family; font.pixelSize: 16
        }
        MouseArea { id: foldMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: fold.centerRef.setFold(fold.title, !fold.open) }
    }
    Column {
        id: foldBody
        visible: fold.open
        x: PanelStyle.selectionInset; y: foldHeader.height + PanelStyle.selectionInset
        width: fold.width - PanelStyle.selectionInset * 2; spacing: PanelStyle.selectionRowGap
    }
}
