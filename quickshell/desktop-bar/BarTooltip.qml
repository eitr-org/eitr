import QtQuick
import "PanelStyle.js" as PanelStyle
import Quickshell

PopupWindow {
    id: tip
    required property Item target
    required property bool hovered
    required property string text
    required property color background
    required property color foreground
    property bool ready: false

    visible: hovered && ready && text !== ""
    color: "transparent"
    implicitWidth: Math.min(360, label.implicitWidth + 18)
    implicitHeight: label.implicitHeight + 12
    anchor.item: target
    anchor.rect.x: pointer.hovered ? pointer.point.position.x + 12 : (target.width - implicitWidth) / 2
    anchor.rect.y: pointer.hovered ? pointer.point.position.y + 18 : target.height + 6
    anchor.edges: Edges.Top | Edges.Left
    anchor.gravity: Edges.Bottom | Edges.Right
    anchor.adjustment: PopupAdjustment.Slide

    HoverHandler {
        id: pointer
        parent: tip.target
    }

    onHoveredChanged: {
        ready = false;
        if (hovered) delay.restart();
        else delay.stop();
    }

    Timer {
        id: delay
        interval: 400
        onTriggered: tip.ready = true
    }

    Rectangle {
        anchors.fill: parent
        radius: DesktopStyle.radius(4)
        color: tip.background
        border.color: Qt.rgba(tip.foreground.r, tip.foreground.g, tip.foreground.b, 0.18)
        Text {
            id: label
            anchors.centerIn: parent
            width: Math.min(342, implicitWidth)
            wrapMode: Text.Wrap
            textFormat: Text.PlainText
            text: tip.text
            color: tip.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
        }
    }
}
