import ".."
import QtQuick
import Quickshell.Hyprland

Rectangle {
    id: button
    property var host

    property string text: ""
    property string tooltip: ""
    property bool active: false
    property int fontSize: 15
    property int buttonHeight: 24
    property int cornerRadius: 7
    property int textOffsetY: 0
    property string visualStyle: "Runes"

    signal clicked()
    signal rightClicked()

    width: 24
    height: buttonHeight
    radius: DesktopStyle.radius(cornerRadius)
    color: visualStyle === "Numbers" || visualStyle === "Runes" ? (!active && mouse.containsMouse ? host.hoverBg : "transparent") : "transparent"

    WorkspaceMarker {
        anchors.fill: parent
        style: button.visualStyle
        label: button.text
        active: button.active
        accent: host.activeBg
        foreground: host.fg
        selectedForeground: host.activeFg
        fontSize: button.fontSize
        textOffsetY: button.textOffsetY
    }


    MouseArea {
        id: mouse

        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.PointingHandCursor
        onEntered: Hyprland.refreshToplevels()
        onClicked: function(event) {
            if (event.button === Qt.RightButton) button.rightClicked();
            else button.clicked();
        }
    }

    BarTooltip {
        target: button
        hovered: mouse.containsMouse && !button.active
        text: button.tooltip
        foreground: host.fg
        background: host.workspaceMenuBg
    }

    Behavior on color {
        ColorAnimation {
            duration: DesktopStyle.motionDuration(120)
        }

    }

}
