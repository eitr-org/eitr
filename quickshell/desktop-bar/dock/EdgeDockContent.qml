import ".."
import QtQuick
import QtQuick.Effects
import Quickshell
import "../PanelStyle.js" as PanelStyle
import "../DockModel.js" as DockModel

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
    // Magnify on hover: icons near the pointer grow away from the screen edge on a
    // cosine falloff and neighbours shift apart; the surface itself never moves.
    // The pointer is measured against the unscaled slots, so growth cannot feed back.
    readonly property real magnification: 1.6
    readonly property real magnifyReach: 2.5 * 42
    readonly property bool overflowing: (vertical ? icons.height : icons.width) > (vertical ? height : width) - 16
    readonly property bool magnifying: pointer.hovered && !dragging && !menuOpen && !overflowing
        && revealProgress >= 1 && !DesktopStyle.reduceMotion
    property real magnifyStrength: magnifying ? 1 : 0
    Behavior on magnifyStrength { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    readonly property bool clipsContent: overflowing || magnifyStrength === 0
    property real lastPointerAxis: 0
    readonly property point pointerPosition: pointer.point.position
    onPointerPositionChanged: {
        if (!pointer.hovered) return;
        var local = icons.mapFromItem(dock, pointerPosition.x, pointerPosition.y);
        lastPointerAxis = vertical ? local.y : local.x;
    }
    function slotScale(entry) {
        if (magnifyStrength === 0) return 1;
        var distance = Math.abs(lastPointerAxis - (slotPosition(entry) + 18));
        if (distance >= magnifyReach) return 1;
        return 1 + (magnification - 1) * magnifyStrength * (1 + Math.cos(Math.PI * distance / magnifyReach)) / 2;
    }
    // Extra length every grown slot adds, spread so the point under the pointer stays put.
    function slotShift(entry) {
        if (magnifyStrength === 0) return 0;
        var shift = 0;
        var own = slotPosition(entry);
        for (var candidate of orderedApps) {
            var start = slotPosition(candidate);
            var extra = 36 * (slotScale(candidate) - 1);
            if (start < own) shift += extra;
            else if (candidate.id === entry.id) shift += extra / 2;
            shift -= extra * Math.max(0, Math.min(1, (lastPointerAxis - start) / 36));
        }
        return shift;
    }
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
            clip: dock.overflowing
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
                        readonly property real magnifiedScale: dock.slotScale(modelData)
                        readonly property real magnifiedShift: dock.slotShift(modelData)
                        z: magnifiedScale
                        transform: [
                            Scale {
                                origin.x: dock.barEdge === "left" ? 0 : dock.barEdge === "right" ? 36 : 18
                                origin.y: dock.barEdge === "top" ? 0 : dock.barEdge === "bottom" ? 36 : 18
                                xScale: slot.magnifiedScale; yScale: slot.magnifiedScale
                            },
                            Translate {
                                x: dock.vertical ? 0 : slot.magnifiedShift
                                y: dock.vertical ? slot.magnifiedShift : 0
                            }
                        ]
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
                            // Drawn sharp at the largest magnified size.
                            sourceSize.width: 48; sourceSize.height: 48
                            smooth: true; mipmap: true
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
