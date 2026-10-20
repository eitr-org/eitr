import QtQuick
import "PanelStyle.js" as PanelStyle

Rectangle {
    id: button
    required property color foreground
    required property string text
    property bool available: true
    property bool loading: false
    property bool icon: false
    property int textSize: PanelStyle.controlSize
    property int iconSize: 18
    property bool compactIconBackground: false
    property real iconOffsetX: 0
    property bool outlined: false
    property bool selected: false
    property string leadingIcon: ""
    property int textAlignment: Text.AlignHCenter
    readonly property color fillColor: Qt.rgba(foreground.r, foreground.g, foreground.b, selected ? 0.18 : mouse.containsMouse ? 0.16 : outlined ? 0 : 0.08)
    signal clicked()
    activeFocusOnTab: true
    enabled: available && !loading
    Keys.onReturnPressed: if (enabled) clicked()
    Keys.onEnterPressed: if (enabled) clicked()
    Keys.onSpacePressed: if (enabled) clicked()
    width: icon ? 34 : 68
    height: 40
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: icon && compactIconBackground ? "transparent" : fillColor
    border.width: outlined && !(icon && compactIconBackground) ? 1 : 0
    border.color: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.3)
    opacity: available && !loading ? 1 : 0.45
    Rectangle {
        visible: button.icon && button.compactIconBackground
        anchors.centerIn: parent
        width: 28
        height: Math.min(28, button.height)
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: button.fillColor
        border.width: button.outlined ? 1 : 0
        border.color: Qt.rgba(button.foreground.r, button.foreground.g, button.foreground.b, 0.3)
    }
    Text {
        visible: !button.loading
        x: button.icon ? button.iconOffsetX : button.leadingIcon !== "" ? 34 : 8
        width: button.icon ? parent.width : parent.width - x - 8
        height: parent.height
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: button.textAlignment
        elide: Text.ElideRight
        text: button.text
        color: button.foreground
        font.family: button.icon ? PanelStyle.fontFamily : DesktopFonts.family
        font.pixelSize: button.icon ? button.iconSize : button.textSize
    }
    Text {
        visible: button.leadingIcon !== "" && !button.loading
        x: 8
        width: 18
        anchors.verticalCenter: parent.verticalCenter
        horizontalAlignment: Text.AlignHCenter
        text: button.leadingIcon
        color: button.foreground
        font.family: PanelStyle.fontFamily
        font.pixelSize: 16
    }
    Text {
        anchors.centerIn: parent
        visible: button.loading
        text: "󰑐"
        color: button.foreground
        font.family: PanelStyle.fontFamily
        font.pixelSize: 18
        RotationAnimator on rotation {
            from: 0
            to: 360
            duration: 900
            loops: Animation.Infinite
            running: button.visible && button.loading
        }
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        enabled: button.available && !button.loading
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            button.forceActiveFocus();
            button.clicked();
        }
    }
}
