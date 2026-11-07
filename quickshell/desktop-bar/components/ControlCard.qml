import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

Rectangle {
    id: card
    property color surface: Qt.alpha(foreground, 0.04)
    property color line: Qt.alpha(foreground, 0.15)
    property color gold: foreground
    property bool carved: false
    property alias spacing: contents.spacing
    property string title: ""
    required property color foreground
    default property alias body: contents.data
    implicitHeight: contents.implicitHeight + 72
    width: parent ? parent.width : 0
    height: visible ? implicitHeight : 0
    radius: DesktopStyle.radius(10)
    color: card.surface
    border.width: 1
    border.color: card.line
    Text {
        x: 16
        y: 14
        width: parent.width - 32
        text: card.title
        color: card.gold
        font.family: card.carved ? SiteStyle.carved : DesktopFonts.family
        font.pixelSize: 12
        font.capitalization: Font.AllUppercase
        font.letterSpacing: 1.3
        elide: Text.ElideRight
    }
    Rectangle {
        x: 16
        y: 39
        width: parent.width - 32
        height: 1
        color: Qt.alpha(card.gold, 0.3)
    }
    Column {
        id: contents
        x: 16
        y: 52
        width: parent.width - 32
        spacing: 12
    }
    property real reveal: 1
    opacity: reveal
    transform: Translate {
        y: (1 - card.reveal) * 6
    }
    onVisibleChanged: {
        if (visible) {
            reveal = 0;
            entrance.restart();
        } else
            entrance.stop();
    }
    NumberAnimation {
        id: entrance
        target: card
        property: "reveal"
        from: 0
        to: 1
        duration: DesktopStyle.motionDuration(180)
        easing.type: Easing.OutCubic
    }
}
