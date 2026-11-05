import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Hyprland
import Eitr as Eitr

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
    // Reserve joins independently of edge contact: content-sized height must not
    // feed back through placementExtent and the surface's flush-edge detection.
    // A panel reaching both screen ends may leave this reserve unused.
    readonly property real verticalJoinInset: !verticalAttachment || detached ? 0
        : PanelStyle.surfaceInset * (alignment === "center" || (alignment === "left" && leadingOffset > 0) ? 2 : 1)
    readonly property real verticalContentInset: panelSurface.topPadding + panelSurface.bottomPadding + verticalJoinInset
    readonly property real horizontalContentInset: panelSurface.leftPadding + panelSurface.rightPadding
        + (panelSurface.vertical ? 0 : panelSurface.leadingBodyInset + panelSurface.trailingBodyInset)
    property Item keyTarget: body
    // A picture filling the whole panel sheet, under the content (PanelSurface.backdrop).
    property Item backdrop: null
    property real paddingScale: 1
    property real backdropInset: 0
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
        // Islands: the card that grows from the pill's shape into this panel and back.
        Rectangle {
            id: pillCard
            readonly property rect pill: popup.pillRect
            readonly property real progress: popup.revealProgress
            visible: !!popup.morphPill && popup.visible
            x: (pill.x - popup.x) * (1 - progress)
            y: (pill.y - popup.y) * (1 - progress)
            width: pill.width + (popup.width - pill.width) * progress
            height: pill.height + (popup.height - pill.height) * progress
            radius: (popup.morphPill ? popup.morphPill.radius : 0) * (1 - progress) + 20 * progress
            color: popup.surfaceColor
        },
        // Dynamic: step to the previous or next panel of the island this card grew from.
        Item {
            id: islandNavigation
            anchors.fill: parent
            z: 1
            readonly property var islands: popup.morphIsland && popup.hostWindow ? popup.hostWindow.dynamicSurfaces : null
            visible: !!islands && popup.opened && popup.revealProgress > 0.5
            opacity: Math.max(0, popup.revealProgress * 2 - 1)
            readonly property bool sideways: popup.verticalAttachment
            readonly property real inset: 8
            PanelButton {
                objectName: "dynamicPreviousPanel"
                icon: true; iconSize: 16; width: 24; height: 24
                text: islandNavigation.sideways ? "󰅃" : "󰅁"
                foreground: popup.foreground
                x: popup.barEdge === "right" ? parent.width - width - islandNavigation.inset : islandNavigation.inset
                y: popup.barEdge === "bottom" ? parent.height - height - islandNavigation.inset : islandNavigation.inset
                Accessible.name: Eitr.I18n.tr("Previous panel")
                onClicked: islandNavigation.islands.step(popup, -1)
            }
            PanelButton {
                objectName: "dynamicNextPanel"
                icon: true; iconSize: 16; width: 24; height: 24
                text: islandNavigation.sideways ? "󰅀" : "󰅂"
                foreground: popup.foreground
                x: islandNavigation.sideways ? (popup.barEdge === "right" ? parent.width - width - islandNavigation.inset : islandNavigation.inset) : parent.width - width - islandNavigation.inset
                y: islandNavigation.sideways ? parent.height - height - islandNavigation.inset : (popup.barEdge === "bottom" ? parent.height - height - islandNavigation.inset : islandNavigation.inset)
                Accessible.name: Eitr.I18n.tr("Next panel")
                onClicked: islandNavigation.islands.step(popup, 1)
            }
        },
        PanelSurface {
            id: panelSurface
            anchors.fill: parent
            hostWindow: popup
            color: popup.surfaceColor
            backdrop: popup.backdrop
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
