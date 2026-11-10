import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

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
    property bool menuGrabReady: false
    onActiveChanged: if (!active) menuOpen = false
    onVisibleChanged: if (!visible) menuOpen = false
    property point menuPoint: Qt.point(0, 0)
    // The saved placement of this copy (entry.geometry on the desktop).
    readonly property var placement: entry.geometry || null
    signal sizeRequested(real factor)
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
    // Size steps need the display's bounds, so the desktop surface applies them.
    function menuAction(action) {
        if (action === "smaller") sizeRequested(0.9);
        else if (action === "larger") sizeRequested(1.1);
        else if (action === "full") sizeRequested(0);
    }
    Connections {
        target: PluginRegistry
        function onReviewStarted() { widget.menuOpen = false; }
    }
    MouseArea {
        anchors.fill: parent; z: 3
        acceptedButtons: Qt.RightButton
        enabled: !widget.aboveWindows || widget.editing
        // The menu anchors to the unrotated parent, at the pointer's place there.
        onClicked: function(mouse) {
            widget.menuPoint = widget.parent ? mapToItem(widget.parent, mouse.x, mouse.y) : Qt.point(mouse.x, mouse.y);
            widget.menuOpen = true;
        }
    }
    PopupWindow {
        id: context
        visible: widget.menuOpen
        color: "transparent"
        implicitWidth: options.implicitWidth
        implicitHeight: Math.min(options.implicitHeight, screen ? screen.height - 40 : 720)
        anchor.item: widget.parent || widget
        anchor.rect.x: widget.menuPoint.x; anchor.rect.y: widget.menuPoint.y
        anchor.edges: Edges.Top | Edges.Left
        anchor.gravity: Edges.Bottom | Edges.Right
        // Near a screen edge the menu opens the other way, then slides to stay on screen.
        anchor.adjustment: PopupAdjustment.Flip | PopupAdjustment.Slide
        onVisibleChanged: {
            if (visible) menuGrabDelay.restart();
            else { menuGrabDelay.stop(); widget.menuGrabReady = false; }
        }
        Timer {
            id: menuGrabDelay
            interval: 100
            onTriggered: if (widget.menuOpen) { options.forceActiveFocus(); widget.menuGrabReady = true; }
        }
        HyprlandFocusGrab { id: menuGrab; objectName: "pluginMenuGrab"; active: widget.menuGrabReady && widget.menuOpen && context.visible && widget.active && widget.visible; windows: [context]; onCleared: widget.menuOpen = false }
        Flickable {
            anchors.fill: parent
            contentHeight: options.implicitHeight; clip: true
            boundsBehavior: Flickable.StopAtBounds
            interactive: contentHeight > height
            PluginWidgetMenu {
                id: options
                width: context.implicitWidth
                entry: widget.entry; placement: widget.placement
                foreground: widget.foreground; background: widget.background; accent: widget.accent
                focus: widget.menuOpen
                onCloseRequested: widget.menuOpen = false
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
