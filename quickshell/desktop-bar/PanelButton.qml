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
    property int iconSize: 20
    property bool compactIconBackground: false
    property real iconOffsetX: 0
    property bool outlined: false
    property bool selected: false
    property string leadingIcon: ""
    property int textAlignment: Text.AlignHCenter
    readonly property color fillColor: Qt.rgba(foreground.r, foreground.g, foreground.b, selected ? 0.18 : mouse.containsMouse ? 0.16 : icon || outlined ? 0 : 0.08)
    signal clicked()
    activeFocusOnTab: true
    enabled: available && !loading
    Keys.onReturnPressed: if (enabled) clicked()
    Keys.onEnterPressed: if (enabled) clicked()
    Keys.onSpacePressed: if (enabled) clicked()
    width: icon ? 28 : 68
    height: 32
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: icon && compactIconBackground ? "transparent" : fillColor
    border.width: outlined && !(icon && compactIconBackground) ? 1 : 0
    border.color: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.3)
    opacity: available && !loading ? 1 : 0.45
    Rectangle {
        visible: button.icon && button.compactIconBackground
        anchors.centerIn: parent
        width: Math.min(24, button.width)
        height: Math.min(24, button.height)
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: button.fillColor
        border.width: button.outlined ? 1 : 0
        border.color: Qt.rgba(button.foreground.r, button.foreground.g, button.foreground.b, 0.3)
    }
    Text {
        id: label
        visible: !button.loading || button.icon
        x: button.icon ? (button.width - ink.tightBoundingRect.width) / 2 - ink.tightBoundingRect.x + button.iconOffsetX : button.leadingIcon !== "" ? 34 : 8
        y: button.icon ? button.height / 2 - (baselineOffset + ink.tightBoundingRect.y + ink.tightBoundingRect.height / 2) : 0
        width: button.icon ? implicitWidth : parent.width - x - 8
        height: button.icon ? implicitHeight : parent.height
        verticalAlignment: button.icon ? Text.AlignTop : Text.AlignVCenter
        horizontalAlignment: button.icon ? Text.AlignLeft : button.textAlignment
        elide: Text.ElideRight
        text: button.text
        color: button.foreground
        font.family: button.icon ? PanelStyle.fontFamily : DesktopFonts.family
        font.pixelSize: button.icon ? button.iconSize : button.textSize
        TextMetrics { id: ink; font: label.font; text: label.text }
        transform: Rotation {
            id: spin
            origin.x: ink.tightBoundingRect.x + ink.tightBoundingRect.width / 2
            origin.y: label.baselineOffset + ink.tightBoundingRect.y + ink.tightBoundingRect.height / 2
            NumberAnimation on angle {
                from: 0; to: 360
                duration: 1200
                loops: Animation.Infinite
                running: button.visible && button.icon && button.loading
                onStopped: spin.angle = 0
            }
        }
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
        visible: button.loading && !button.icon
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
