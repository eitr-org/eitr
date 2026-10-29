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
    readonly property bool detached: false
    // Straight sides meet the screen edge, without the panels' inward curves.
    readonly property bool edgeJoins: false
    property real revealProgress: 1
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
                        Rectangle {
                            anchors.fill: parent
                            radius: DesktopStyle.radius(6)
                            color: Qt.rgba(dock.foreground.r, dock.foreground.g, dock.foreground.b, PanelStyle.selectionAlpha(false, true))
                            visible: mouse.containsMouse
                        }
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
                        // One dot per window, up to three; dimmed when none is on this workspace.
                        Row {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom; anchors.bottomMargin: 1
                            spacing: 2
                            opacity: slot.modelData.onCurrentWorkspace ? 1 : 0.4
                            Repeater {
                                model: Math.min(3, slot.modelData.windows.length)
                                Rectangle { width: 3; height: 3; radius: 1.5; color: dock.foreground }
                            }
                        }
                        MouseArea {
                            id: mouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                            onClicked: function(event) {
                                if (event.button === Qt.MiddleButton) dock.closeRequested(slot.modelData);
                                else dock.activated(slot.modelData);
                            }
                        }
                        BarTooltip {
                            target: slot; hovered: mouse.containsMouse
                            text: slot.modelData.windows.length > 1 ? slot.appName + " (" + slot.modelData.windows.length + ")" : slot.appName; background: dock.background; foreground: dock.foreground
                        }
                    }
                }
            }
        }
    }
}
