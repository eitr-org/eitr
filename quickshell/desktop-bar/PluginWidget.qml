pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Hyprland
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

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
    property bool menuOpen: false
    property point menuPoint: Qt.point(0, 0)
    signal sizeRequested(real factor)
    signal surfaceRequested(string surface)
    signal layerRequested()
    signal removeRequested()
    property bool active: true
    property bool editing: false
    signal begun()
    signal moved(real deltaX, real deltaY)
    signal resized(real deltaX, real deltaY)
    signal finished()
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
    Keys.onEscapePressed: { menuOpen = false; PluginRegistry.editing = false; }
    onEditingChanged: if (editing) forceActiveFocus()
    function menuAction(action) {
        menuOpen = false;
        if (action === "edit") { PluginRegistry.editTarget = {plugin: entry.plugin, id: entry.id, monitor: entry.geometry ? entry.geometry.monitor : ""}; PluginRegistry.editing = true; }
        else if (action === "smaller") sizeRequested(0.9);
        else if (action === "larger") sizeRequested(1.1);
        else if (action === "full") sizeRequested(0);
        else if (action === "panel" || action === "none") surfaceRequested(action);
        else if (action === "layer") layerRequested();
        else if (action === "remove") removeRequested();
    }
    MouseArea {
        anchors.fill: parent; z: 3
        acceptedButtons: Qt.RightButton
        enabled: !widget.aboveWindows || widget.editing
        onClicked: function(mouse) { widget.menuPoint = Qt.point(mouse.x, mouse.y); widget.menuOpen = true; }
    }
    PopupWindow {
        id: context
        visible: widget.menuOpen
        color: "transparent"
        implicitWidth: 256; implicitHeight: Math.min(options.implicitHeight + 20, screen ? screen.height - 40 : 640)
        anchor.item: widget
        anchor.rect.x: widget.menuPoint.x; anchor.rect.y: widget.menuPoint.y
        anchor.edges: Edges.Top | Edges.Left
        anchor.gravity: Edges.Bottom | Edges.Right
        anchor.adjustment: PopupAdjustment.Slide
        onVisibleChanged: {
            if (visible) menuGrabDelay.restart();
            else { menuGrabDelay.stop(); menuGrab.active = false; }
        }
        Timer {
            id: menuGrabDelay
            interval: 100
            onTriggered: if (widget.menuOpen) { options.forceActiveFocus(); menuGrab.active = true; }
        }
        HyprlandFocusGrab { id: menuGrab; windows: [context]; onCleared: widget.menuOpen = false }
        Rectangle {
            anchors.fill: parent; color: widget.background
            radius: DesktopStyle.radius(PanelStyle.cornerRadius)
            border.width: 1; border.color: Qt.alpha(widget.foreground, PanelStyle.selectionBorderAlpha)
        }
        ScrollView {
            id: menuScroll
            x: 10; y: 10; width: parent.width - 20; height: parent.height - 20
            contentWidth: availableWidth; clip: true
        PluginWidgetMenu {
            id: options
            width: menuScroll.availableWidth
            foreground: widget.foreground; background: widget.background
            aboveWindows: widget.aboveWindows; surface: widget.surface; entries: component.menuEntries
            focus: widget.menuOpen
            Keys.onEscapePressed: widget.menuOpen = false
            onAction: action => widget.menuAction(action)
            onSelected: function(id) { component.menuSelect(id); widget.menuOpen = false; }
        }
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
            anchors.centerIn: parent; text: "⠿ " + widget.entry.title; textFormat: Text.PlainText
            width: parent.width - 12; elide: Text.ElideRight
            color: widget.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        MouseArea {
            id: moveHandle
            anchors.fill: parent; cursorShape: Qt.SizeAllCursor; preventStealing: true
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
    }
    Rectangle {
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
    PanelButton {
        visible: widget.editing
        anchors.bottom: parent.bottom; anchors.left: parent.left
        text: Eitr.I18n.tr("Done"); foreground: widget.foreground
        onClicked: PluginRegistry.editing = false
    }
}
