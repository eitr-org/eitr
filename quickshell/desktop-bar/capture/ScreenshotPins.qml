import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Screenshots pinned on screen as floating references, above every window and on every
// workspace. Drag one to move it, scroll over it to resize it, and close it with its ×
// button, Escape or a middle click. Each pin is a screen-sized overlay that only takes
// input on its card, created and destroyed with its entry (never hidden and shown again).
Scope {
    id: pins
    required property color foreground
    required property color background
    property var entries: []
    property int nextId: 1

    function add(path) {
        if (!path) return;
        var screen = Eitr.Screens.focused(null);
        if (!screen) return;
        // Each new pin starts a little lower and to the left of the last, so none hides another.
        var offset = (entries.length % 6) * 28;
        entries = entries.concat([{id: nextId, path: path, screen: screen, x: screen.width - 460 - offset, y: 80 + offset}]);
        nextId += 1;
    }
    function remove(id) { entries = entries.filter(entry => entry.id !== id); }

    IpcHandler {
        target: "pins"
        function add(path: string): void { pins.add(path); }
        function clear(): void { pins.entries = []; }
        function count(): int { return pins.entries.length; }
    }

    Variants {
        model: pins.entries
        PanelWindow {
            id: pin
            required property var modelData
            property real zoom: 1
            screen: modelData.screen
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            // The pin's window always covers its screen and only the card moves inside it, with
            // the input region on the card alone: moving or resizing the window lags a frame
            // behind the pointer, which made the card jitter and jump on press and release.
            property bool dragging: false
            anchors { top: true; left: true; right: true; bottom: true }
            mask: Region { item: card }
            property point position: Qt.point(modelData.x, modelData.y)
            // Fits a 420 px wide card at first, never larger than half the screen.
            readonly property real baseWidth: image.status === Image.Ready ? Math.min(420, image.sourceSize.width, (screen ? screen.width : 1920) / 2) : 0
            readonly property real cardWidth: Math.max(80, baseWidth * zoom)
            readonly property real cardHeight: image.sourceSize.width > 0 ? cardWidth * image.sourceSize.height / image.sourceSize.width : 0
            WlrLayershell.namespace: "eitr-pin"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand

            Rectangle {
                id: card
                x: Math.round(pin.position.x) + 8
                y: Math.round(pin.position.y) + 8
                width: pin.cardWidth; height: pin.cardHeight
                radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                color: pins.background
                border.width: 1
                border.color: Qt.alpha(pins.foreground, hover.hovered ? 0.45 : 0.2)
                clip: true
                focus: true
                Keys.onEscapePressed: pins.remove(pin.modelData.id)
                Image {
                    id: image
                    anchors.fill: parent
                    anchors.margins: 1
                    source: "file://" + pin.modelData.path
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    mipmap: true
                }
                HoverHandler { id: hover }
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                    cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                    // Where the card was grabbed, in card coordinates.
                    property point grab: Qt.point(0, 0)
                    onPressed: function(mouse) {
                        card.forceActiveFocus();
                        if (mouse.button === Qt.MiddleButton) { pins.remove(pin.modelData.id); return; }
                        grab = Qt.point(mouse.x, mouse.y);
                        pin.dragging = true;
                    }
                    onReleased: pin.dragging = false
                    onCanceled: pin.dragging = false
                    onPositionChanged: function(mouse) {
                        if (!pin.dragging) return;
                        // The window stays still while dragging, so window coordinates are screen ones.
                        var at = mapToItem(pin.contentItem, mouse.x, mouse.y);
                        var area = pin.screen;
                        var nextX = at.x - grab.x - 8, nextY = at.y - grab.y - 8;
                        // Keep a corner of the pin on screen so it can always be reached.
                        pin.position = Qt.point(Math.max(48 - pin.cardWidth - 16, Math.min(area.width - 48, nextX)),
                                                Math.max(0, Math.min(area.height - 48, nextY)));
                    }
                    onWheel: function(wheel) {
                        pin.zoom = Math.max(0.3, Math.min(3, pin.zoom * (wheel.angleDelta.y > 0 ? 1.1 : 1 / 1.1)));
                    }
                }
                PanelButton {
                    visible: hover.hovered
                    anchors { top: parent.top; right: parent.right; margins: 6 }
                    icon: true; iconSize: 14; width: 24; height: 24
                    text: "󰅖"
                    foreground: pins.foreground
                    Accessible.name: Eitr.I18n.tr("Close pin")
                    onClicked: pins.remove(pin.modelData.id)
                    Rectangle { anchors.fill: parent; z: -1; radius: width / 2; color: Qt.alpha(pins.background, 0.85) }
                }
            }
        }
    }
}
