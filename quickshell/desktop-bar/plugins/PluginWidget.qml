import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../PluginGeometry.js" as Geometry

Item {
    id: widget
    required property var entry
    required property color foreground
    required property color background
    required property color accent
    property string surface: entry.surface || "none"
    property bool aboveWindows: false
    property real originX: 0
    property real originY: 0
    readonly property var menuEntries: component.menuEntries
    function pointerPosition(area, mouse) {
        return area.mapToGlobal(mouse.x, mouse.y);
    }
    function selectMenu(id) { component.menuSelect(id); }
    // The saved placement of this copy (entry.geometry on the desktop).
    readonly property var placement: entry.geometry || null
    signal sizeRequested(real factor)
    // A right-click, at the pointer's place in this widget's unrotated parent.
    signal menuRequested(point position)
    property bool active: true
    property bool editing: false
    signal begun()
    signal moved(real deltaX, real deltaY)
    signal resized(real deltaX, real deltaY)
    signal finished()
    // The title bar's rotate handle: the angle while dragging, then the one to keep.
    signal rotating(int degrees)
    signal rotationFinished(int degrees)
    Rectangle { visible: widget.surface !== "none"; anchors.fill: parent; color: widget.background; radius: DesktopStyle.radius(PanelStyle.controlRadius) }
    PluginComponent {
        id: component
        surface: widget.surface !== "none"
        anchors.fill: parent
        active: widget.active && widget.visible
        entry: widget.entry
        foreground: widget.foreground; background: widget.background; accent: widget.accent
    }
    focus: editing
    Keys.onEscapePressed: PluginRegistry.editing = false
    onEditingChanged: if (editing) forceActiveFocus()
    // Size steps need the display's bounds, so the desktop surface applies them.
    function menuAction(action) {
        if (action === "smaller") sizeRequested(0.9);
        else if (action === "larger") sizeRequested(1.1);
        else if (action === "full") sizeRequested(0);
    }
    // Above the plugin's own content, but under the edit chrome while editing: a MouseArea
    // sets the arrow cursor wherever it lies on top, even for buttons it does not take.
    MouseArea {
        anchors.fill: parent; z: widget.editing ? 0 : 3
        acceptedButtons: Qt.RightButton
        enabled: !widget.aboveWindows || widget.editing
        onClicked: function(mouse) {
            widget.menuRequested(widget.parent ? mapToItem(widget.parent, mouse.x, mouse.y) : Qt.point(mouse.x, mouse.y));
        }
    }
    Rectangle {
        anchors.fill: parent; visible: widget.editing; color: "transparent"
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        border.color: widget.accent; border.width: 2
    }
    Rectangle {
        visible: widget.editing; width: parent.width; height: 28
        color: widget.background; radius: DesktopStyle.radius(PanelStyle.controlRadius)
        Text {
            x: rotateHandle.x + rotateHandle.width + 6; anchors.verticalCenter: parent.verticalCenter
            text: widget.entry.title; textFormat: Text.PlainText
            width: parent.width - x - 8; elide: Text.ElideRight
            color: widget.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        MouseArea {
            id: moveHandle
            anchors.fill: parent; cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor; preventStealing: true
            property point start
            onPressed: function(mouse) { start = widget.pointerPosition(moveHandle, mouse); widget.begun(); }
            onPositionChanged: function(mouse) {
                if (!pressed) return;
                const next = widget.pointerPosition(moveHandle, mouse);
                widget.moved(next.x - start.x, next.y - start.y);
            }
            onReleased: widget.finished()
            onCanceled: widget.finished()
        }
        // Drag around the widget's centre to turn it; quarter turns snap as on the slider.
        Rectangle {
            id: rotateHandle
            x: 4; anchors.verticalCenter: parent.verticalCenter
            width: 22; height: 22; radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: rotateArea.containsMouse || rotateArea.pressed ? Qt.alpha(widget.foreground, 0.16) : "transparent"
            Text {
                anchors.centerIn: parent; text: String.fromCodePoint(0xF0467)
                color: widget.foreground; font.family: PanelStyle.fontFamily; font.pixelSize: 15
            }
            MouseArea {
                id: rotateArea
                anchors.fill: parent; hoverEnabled: true; preventStealing: true
                cursorShape: pressed ? Qt.ClosedHandCursor : Qt.PointingHandCursor
                Accessible.role: Accessible.Button
                Accessible.name: Eitr.I18n.tr("Rotation")
                property point centre
                property real startAngle: 0
                property int startRotation: 0
                property int current: 0
                function angleTo(point) { return Math.atan2(point.y - centre.y, point.x - centre.x) * 180 / Math.PI; }
                onPressed: function(mouse) {
                    centre = widget.mapToGlobal(widget.width / 2, widget.height / 2);
                    startAngle = angleTo(widget.pointerPosition(rotateArea, mouse));
                    startRotation = Math.round(widget.rotation);
                    current = startRotation;
                }
                onPositionChanged: function(mouse) {
                    if (!pressed) return;
                    current = Geometry.snapRotation(startRotation + angleTo(widget.pointerPosition(rotateArea, mouse)) - startAngle);
                    widget.rotating(current);
                }
                onReleased: if (current !== startRotation) widget.rotationFinished(current)
                onCanceled: widget.rotating(startRotation)
            }
        }
    }
    Rectangle {
        id: resizeGrip
        visible: widget.editing; width: 28; height: 28
        anchors.right: parent.right; anchors.bottom: parent.bottom
        color: widget.accent; radius: DesktopStyle.radius(PanelStyle.controlRadius)
        Text { anchors.centerIn: parent; text: "↘"; color: widget.background; font.pixelSize: 20 }
        MouseArea {
            id: resizeHandle
            anchors.fill: parent; cursorShape: Qt.SizeFDiagCursor; preventStealing: true
            property point start
            onPressed: function(mouse) { start = widget.pointerPosition(resizeHandle, mouse); widget.begun(); }
            onPositionChanged: function(mouse) {
                if (!pressed) return;
                const next = widget.pointerPosition(resizeHandle, mouse);
                widget.resized(next.x - start.x, next.y - start.y);
            }
            onReleased: widget.finished()
            onCanceled: widget.finished()
        }
    }
    // Beside the resize grip, solid in the accent so it reads on any wallpaper.
    PanelButton {
        id: doneButton
        visible: widget.editing
        anchors.bottom: parent.bottom; anchors.right: resizeGrip.left; anchors.rightMargin: 6
        width: Math.max(64, doneMetrics.advanceWidth + 28); height: 28
        color: widget.accent
        text: Eitr.I18n.tr("Done"); foreground: PanelStyle.readableInk(widget.accent, widget.foreground, widget.background)
        onClicked: PluginRegistry.editing = false
        TextMetrics { id: doneMetrics; text: doneButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
    }
}
