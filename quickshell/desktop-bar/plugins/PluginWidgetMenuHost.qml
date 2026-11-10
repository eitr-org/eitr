import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Wayland

// The right-click menu of a desktop widget copy, in its own overlay window: it stays where
// it opened while the widget rotates, resizes or reloads, and closes only on Escape, a
// click outside, or an action that ends it (edit position, another display, remove).
Scope {
    id: host
    required property color foreground
    required property color background
    required property color accent
    readonly property var target: PluginRegistry.menuTarget
    readonly property var entry: target ? PluginRegistry.entries.find(entry => entry.plugin === target.plugin && entry.id === target.id && entry.kind === "widgets" && !entry.disabled) || null : null
    readonly property var placement: target ? (PluginRegistry.placements.widgets || []).find(placement => placement.plugin === target.plugin && placement.id === target.id && placement.instance === target.instance) || null : null
    // A removed copy, or one moved to another display, ends its menu.
    onPlacementChanged: if (target && (!placement || placement.monitor !== target.monitor)) PluginRegistry.closeWidgetMenu()
    onEntryChanged: if (target && !entry) PluginRegistry.closeWidgetMenu()

    LazyLoader {
        active: !!host.target && !!host.entry && !!host.placement
        PanelWindow {
            id: window
            screen: Quickshell.screens.find(screen => screen.name === host.target.monitor) || null
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            color: "transparent"
            WlrLayershell.namespace: "eitr-plugin-menu"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
            // A click anywhere outside the card closes the menu.
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.AllButtons
                onClicked: PluginRegistry.closeWidgetMenu()
            }
            Item {
                id: card
                readonly property real margin: 12
                width: menu.implicitWidth
                height: Math.min(menu.implicitHeight, window.height - 2 * margin)
                // Opens at the pointer, flipped and clamped so it stays whole on screen.
                x: Math.max(margin, Math.min(host.target.x + width + margin > window.width ? host.target.x - width : host.target.x, window.width - width - margin))
                y: Math.max(margin, Math.min(host.target.y + height + margin > window.height ? host.target.y - height : host.target.y, window.height - height - margin))
                MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }
                Flickable {
                    anchors.fill: parent
                    contentHeight: menu.implicitHeight; clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    interactive: contentHeight > height
                    PluginWidgetMenu {
                        id: menu
                        width: implicitWidth
                        entry: host.entry; placement: host.placement
                        foreground: host.foreground; background: host.background; accent: host.accent
                        focus: true
                        onCloseRequested: PluginRegistry.closeWidgetMenu()
                        Component.onCompleted: forceActiveFocus()
                    }
                }
            }
        }
    }
}
