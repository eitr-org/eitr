import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// The last row of a panel: where its full settings or app live ("Network Settings…").
// Every panel that has such a place ends with this same row.
Item {
    id: link
    required property string text
    required property color foreground
    signal clicked()
    width: parent ? parent.width : implicitWidth
    height: PanelStyle.selectionRowHeight
    activeFocusOnTab: true
    Accessible.role: Accessible.Link
    Accessible.name: text
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) { link.clicked(); event.accepted = true; }
    }
    // No hover fill: the label lines up with the panel's text, and the chevron
    // brightens and steps right to show the row is clickable.
    readonly property bool emphasized: mouse.containsMouse || activeFocus
    Text {
        width: parent.width - 32
        anchors.verticalCenter: parent.verticalCenter
        text: link.text
        elide: Text.ElideRight
        color: link.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
    }
    Text {
        anchors.right: parent.right
        anchors.rightMargin: link.emphasized ? 0 : 3
        anchors.verticalCenter: parent.verticalCenter
        text: "\u{F0142}"
        color: link.foreground
        opacity: link.emphasized ? 1 : PanelStyle.secondaryTextOpacity
        Behavior on anchors.rightMargin { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
        font.family: DesktopFonts.family
        font.pixelSize: 16
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: link.clicked()
    }
}
