import QtQuick
import QtQuick.Effects
import Quickshell
import "PanelStyle.js" as PanelStyle
import "DockModel.js" as DockModel

Item {
    id: dock
    required property string barEdge
    required property var apps
    required property color foreground
    required property color background
    property var desktopEntries: DesktopEntries.applications.values
    property real availableLength: 1000
    readonly property bool vertical: barEdge === "left" || barEdge === "right"
    readonly property real axisLength: Math.min(availableLength, 16 + Math.max(0, apps.length * 42 - 6) + (dividerVisible ? 12 : 0))
    readonly property QtObject hostWindow: QtObject { readonly property var outerGaps: [4, 4, 4, 4] }
    readonly property bool detached: false
    // Straight sides meet the screen edge, without the panels' inward curves.
    readonly property bool edgeJoins: false
    property real revealProgress: 1
    readonly property bool hovered: pointer.hovered
    property bool menuOpen: false
    property var dragEntry: null
    property var previewPins: []
    readonly property bool dragging: dragEntry !== null
    readonly property var pins: apps.filter(entry => entry.pinned).map(entry => entry.desktopId || entry.appClass)
    readonly property var orderedApps: dragging ? DockModel.orderWithPins(apps, previewPins) : apps
    readonly property int pinCount: dragging ? previewPins.length : pins.length
    readonly property bool dividerVisible: pinCount > 0 && pinCount < apps.length
    function slotPosition(entry) {
        var index = orderedApps.findIndex(candidate => candidate.id === entry.id);
        return index * 42 + (dividerVisible && index >= pinCount ? 12 : 0);
    }
    function dragTo(entry, axis) {
        if (!entry.desktopId) return;
        if (!dragging) { dragEntry = entry; previewPins = pins.slice(); }
        previewPins = DockModel.dragPins(pins, entry, axis);
    }
    function finishDrag() {
        if (dragging) pinsRequested(previewPins);
        dragEntry = null;
    }
    signal pinsRequested(var pins)
    signal contextRequested(var entry, point position)
    signal activated(var entry)
    signal closeRequested(var entry)
    width: vertical ? 52 : axisLength
    height: vertical ? axisLength : 52
    function application(appClass) {
        var key = DockModel.desktopId(appClass);
        var webApp = DockModel.webAppKey(appClass);
        return desktopEntries.find(entry => DockModel.desktopId(entry.id) === key || DockModel.desktopId(entry.startupClass) === key)
            || (webApp ? desktopEntries.find(entry => DockModel.webAppKey(entry.startupClass) === webApp) : null)
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
            interactive: !dock.dragging
            boundsBehavior: Flickable.StopAtBounds
            clip: true
            Item {
                id: icons
                width: dock.vertical ? 36 : Math.max(0, dock.apps.length * 42 - 6) + (dock.dividerVisible ? 12 : 0)
                height: dock.vertical ? Math.max(0, dock.apps.length * 42 - 6) + (dock.dividerVisible ? 12 : 0) : 36
                Rectangle {
                    objectName: "dockDivider"
                    visible: dock.dividerVisible
                    x: dock.vertical ? 5 : dock.pinCount * 42 + 3
                    y: dock.vertical ? dock.pinCount * 42 + 3 : 5
                    width: dock.vertical ? 26 : 1
                    height: dock.vertical ? 1 : 26
                    color: Qt.alpha(dock.foreground, PanelStyle.dividerAlpha)
                }
                Repeater {
                    model: dock.apps
                    Item {
                        id: slot
                        objectName: "dockSlot-" + modelData.id
                        required property var modelData
                        readonly property var application: dock.application(modelData.appClass)
                        readonly property bool eitrTerminal: !application && DockModel.eitrTerminal(modelData.appClass)
                        readonly property string appName: application ? application.name : eitrTerminal ? "Eitr" : modelData.appClass
                        width: 36; height: 36
                        x: dock.vertical ? 0 : dock.slotPosition(modelData)
                        y: dock.vertical ? dock.slotPosition(modelData) : 0
                        Behavior on x { NumberAnimation { duration: DesktopStyle.motionDuration(140) } }
                        Behavior on y { NumberAnimation { duration: DesktopStyle.motionDuration(140) } }
                        Rectangle {
                            anchors.fill: parent
                            radius: DesktopStyle.radius(6)
                            color: Qt.rgba(dock.foreground.r, dock.foreground.g, dock.foreground.b, PanelStyle.selectionAlpha(false, true))
                            visible: mouse.containsMouse
                        }
                        Image {
                            id: icon
                            objectName: "dockIcon-" + slot.modelData.id
                            anchors.centerIn: parent
                            width: 28; height: 28
                            source: slot.application && slot.application.icon ? Quickshell.iconPath(slot.application.icon, true) : ""
                            sourceSize.width: 28; sourceSize.height: 28
                            asynchronous: true
                        }
                        Image {
                            id: eitrLogo
                            anchors.centerIn: parent
                            width: 24; height: 24
                            visible: slot.eitrTerminal
                            source: visible ? Quickshell.shellDir + "/assets/eitr-logo-white.svg" : ""
                            fillMode: Image.PreserveAspectFit
                            sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio), Math.ceil(height * Screen.devicePixelRatio))
                            smooth: true
                            layer.enabled: visible
                            layer.effect: MultiEffect { colorization: 1; colorizationColor: dock.foreground }
                        }
                        Text {
                            anchors.centerIn: parent
                            visible: icon.status !== Image.Ready && !slot.eitrTerminal
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
                                objectName: "dockDots-" + slot.modelData.id
                                model: Math.min(3, slot.modelData.windows.length)
                                Rectangle { width: 3; height: 3; radius: 1.5; color: dock.foreground }
                            }
                        }
                        MouseArea {
                            id: mouse
                            anchors.fill: parent
                            hoverEnabled: true
                            preventStealing: true
                            cursorShape: Qt.PointingHandCursor
                            acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
                            property point pressPosition
                            property bool moved: false
                            onPressed: function(event) { pressPosition = mapToItem(icons, event.x, event.y); moved = false; }
                            onPositionChanged: function(event) {
                                if (!pressed || pressedButtons !== Qt.LeftButton) return;
                                var point = mapToItem(icons, event.x, event.y);
                                var axis = dock.vertical ? point.y : point.x;
                                if (Math.abs(axis - (dock.vertical ? pressPosition.y : pressPosition.x)) > 6) moved = true;
                                if (moved) dock.dragTo(slot.modelData, axis);
                            }
                            onReleased: if (dock.dragging) dock.finishDrag()
                            onCanceled: dock.dragEntry = null
                            onClicked: function(event) {
                                if (moved) return;
                                if (event.button === Qt.RightButton) dock.contextRequested(slot.modelData, slot.mapToItem(dock, 18, 18));
                                else if (event.button === Qt.MiddleButton) dock.closeRequested(slot.modelData);
                                else dock.activated(slot.modelData);
                            }
                        }
                        BarTooltip {
                            target: slot; hovered: mouse.containsMouse && !dock.dragging && !dock.menuOpen
                            text: slot.modelData.windows.length > 1 ? slot.appName + " (" + slot.modelData.windows.length + ")" : slot.appName; background: dock.background; foreground: dock.foreground
                        }
                    }
                }
            }
        }
    }
}
