import QtQuick
import Quickshell
import "PanelStyle.js" as PanelStyle

Item {
    id: dock
    required property string barEdge
    required property var apps
    required property color foreground
    required property color background
    property var desktopEntries: DesktopEntries.applications.values
    property real availableLength: 1000
    readonly property bool vertical: barEdge === "left" || barEdge === "right"
    readonly property real axisLength: Math.min(availableLength, 16 + Math.max(0, apps.length * 42 - 6))
    readonly property QtObject hostWindow: QtObject { readonly property var outerGaps: [4, 4, 4, 4] }
    readonly property bool detached: true
    readonly property real revealProgress: 1
    readonly property bool hovered: pointer.hovered
    signal activated(var entry)
    signal closeRequested(var entry)
    width: vertical ? 52 : axisLength
    height: vertical ? axisLength : 52
    function application(appClass) {
        var key = appClass.toLowerCase();
        return desktopEntries.find(entry => entry.id.toLowerCase() === key || (entry.startupClass || "").toLowerCase() === key)
            || DesktopEntries.heuristicLookup(appClass);
    }
    HoverHandler { id: pointer }
    PanelSurface {
        anchors.fill: parent
        hostWindow: dock
        Flickable {
            anchors.fill: parent
            contentWidth: dock.vertical ? width : icons.width
            contentHeight: dock.vertical ? icons.height : height
            flickableDirection: dock.vertical ? Flickable.VerticalFlick : Flickable.HorizontalFlick
            boundsBehavior: Flickable.StopAtBounds
            clip: true
            Grid {
                id: icons
                columns: dock.vertical ? 1 : Math.max(1, dock.apps.length)
                spacing: 6
                Repeater {
                    model: dock.apps
                    Item {
                        id: slot
                        required property var modelData
                        readonly property var application: dock.application(modelData.appClass)
                        readonly property string appName: application ? application.name : modelData.appClass
                        width: 36; height: 36
                        Image {
                            id: icon
                            anchors.centerIn: parent
                            width: 28; height: 28
                            source: slot.application && slot.application.icon ? Quickshell.iconPath(slot.application.icon, true) : ""
                            sourceSize.width: 28; sourceSize.height: 28
                            asynchronous: true
                        }
                        Text {
                            anchors.centerIn: parent
                            visible: icon.status !== Image.Ready
                            text: "󰀻"; color: dock.foreground
                            font.family: PanelStyle.fontFamily; font.pixelSize: 24
                        }
                        Rectangle {
                            width: 3; height: 3; radius: 1.5
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            color: dock.foreground
                            visible: slot.modelData.onCurrentWorkspace
                        }
                        MouseArea {
                            id: mouse
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                            onClicked: function(event) {
                                if (event.button === Qt.MiddleButton) dock.closeRequested(slot.modelData);
                                else dock.activated(slot.modelData);
                            }
                        }
                        BarTooltip {
                            target: slot; hovered: mouse.containsMouse
                            text: slot.appName; background: dock.background; foreground: dock.foreground
                        }
                    }
                }
            }
        }
    }
}
