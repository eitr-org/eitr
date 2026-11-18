import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

// Multi-display overlay for Cleaning mode. Visual Escape-hold progress lives here,
// while Hyprland's `clean` submap owns the actual 3-second and 5-minute exits.
Scope {
    id: overlay
    required property color foreground
    required property color background
    required property color accent
    property bool active: false
    property bool holdingEsc: false
    property real holdProgress: 0

    function open() {
        stopHold();
        active = true;
    }

    function close() {
        stopHold();
        active = false;
    }

    function startHold() {
        if (!active || holdingEsc)
            return;
        holdingEsc = true;
        holdProgress = 0;
        holdAnimation.restart();
    }

    function stopHold() {
        holdAnimation.stop();
        holdingEsc = false;
        holdProgress = 0;
    }

    NumberAnimation {
        id: holdAnimation
        target: overlay
        property: "holdProgress"
        from: 0
        to: 1
        duration: 3000
        easing.type: Easing.Linear
    }

    IpcHandler {
        target: "clean"
        function show(): void { overlay.open(); }
        function hide(): void { overlay.close(); }
        function status(): string {
            return JSON.stringify({
                active: overlay.active,
                holdingEsc: overlay.holdingEsc,
                progress: overlay.holdProgress
            });
        }
    }

    Variants {
        model: overlay.active ? (Quickshell.screens || []) : []
        delegate: Component {
            PanelWindow {
                id: window
                required property var modelData
                screen: modelData
                visible: overlay.active
                anchors { top: true; bottom: true; left: true; right: true }
                exclusionMode: ExclusionMode.Ignore
                color: "transparent"
                WlrLayershell.namespace: "desktop-clean"
                WlrLayershell.layer: WlrLayer.Overlay
                WlrLayershell.keyboardFocus: overlay.active ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
                onVisibleChanged: if (visible) Qt.callLater(surfaceContent.forceActiveFocus)

                IdleInhibitor {
                    enabled: window.visible
                    window: window
                }

                CleanOverlayContent {
                    id: surfaceContent
                    anchors.fill: parent
                    focus: true
                    foreground: overlay.foreground
                    background: overlay.background
                    accent: overlay.accent
                    holdProgress: overlay.holdProgress
                    holdingEsc: overlay.holdingEsc
                    onEscPressed: overlay.startHold()
                    onEscReleased: overlay.stopHold()
                    Component.onCompleted: Qt.callLater(forceActiveFocus)
                }
            }
        }
    }
}
