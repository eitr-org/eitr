import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Hyprland

DockPanel {
    id: popup
    property var escapeHandler: null
    property bool grabReady: false
    onHostWindowChanged: if (!hostWindow && grabReady) opened = false
    onVisibleChanged: if (!visible) grabReady = false
    required property Item target
    required property color foreground
    required property color background
    required property color accent
    property bool centered: false
    property bool leftAligned: false
    property string barEdge: "top"
    property color surfaceColor: background
    readonly property var contentGaps: hostWindow && hostWindow.outerGaps ? hostWindow.outerGaps : [12, 12, 12, 12]
    readonly property real verticalContentInset: (contentGaps[0] + contentGaps[2]) * PanelStyle.contentGapMultiplier
    readonly property real horizontalContentInset: panelSurface.leftPadding + panelSurface.rightPadding
        + (panelSurface.vertical ? 0 : panelSurface.leadingBodyInset + panelSurface.trailingBodyInset)
    property Item keyTarget: body
    default property alias panelContent: body.data
    opened: false
    attachmentTarget: target
    attachmentEdge: barEdge
    alignment: centered ? "center" : leftAligned ? "left" : "right"
    data: [
        Connections {
            target: PluginRegistry
            function onReviewStarted() { popup.opened = false; }
        },
        Connections {
            target: popup
            function onOpenedChanged() {
                if (popup.opened) grabDelay.restart();
                else {
                    grabDelay.stop();
                    popup.grabReady = false;
                }
            }
        },
        Timer {
            id: grabDelay
            interval: 100
            onTriggered: if (popup.opened) {
                if (!popup.hostWindow) { popup.opened = false; return; }
                popup.keyTarget.forceActiveFocus();
                popup.grabReady = true;
            }
        },
        HyprlandFocusGrab { id: grab; active: popup.grabReady && popup.opened && popup.visible && !!popup.hostWindow && popup.focusWindows.length > 0; windows: popup.focusWindows; onCleared: popup.opened = false },
        PanelSurface {
            id: panelSurface
            anchors.fill: parent
            hostWindow: popup
            color: popup.surfaceColor
            Item {
                id: body
                anchors.fill: parent
                clip: true
                focus: true
                Keys.onEscapePressed: if (!popup.escapeHandler || !popup.escapeHandler()) popup.opened = false
            }
        }
    ]
}
