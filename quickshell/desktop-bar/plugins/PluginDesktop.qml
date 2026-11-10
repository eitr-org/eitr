import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "../PluginGeometry.js" as Geometry

Scope {
    id: desktop
    required property color foreground
    required property color background
    required property color accent
    property real grid: 6
    readonly property bool observing: Quickshell.screens.some(screen => PluginRegistry.placed("widgets", screen.name).length > 0)
    property var monitors: DisplayService.topology.monitors
    function refresh() { DisplayService.refresh(); }
    Variants {
        model: Quickshell.screens
        Scope {
            id: display
            required property var modelData
            readonly property var monitor: desktop.monitors.find(monitor => monitor.name === modelData.name)
            readonly property var liveMonitor: Hyprland.monitorFor(modelData)
            readonly property bool fullscreen: !!(liveMonitor && liveMonitor.activeWorkspace && liveMonitor.activeWorkspace.hasFullscreen)
            readonly property var reserved: monitor && monitor.reserved ? monitor.reserved : [0, 0, 0, 0]
            readonly property var bounds: ({x: reserved[0], y: reserved[1], width: modelData.width - reserved[0] - reserved[2], height: modelData.height - reserved[1] - reserved[3]})
            Variants {
                model: PluginRegistry.placed("widgets", display.modelData.name)
                PanelWindow {
                    id: window
                    required property var modelData
                    readonly property var placement: modelData.geometry
                    property var draft: Object.assign({}, placement)
                    property bool gesturing: false
                    property var gestureStart: null
                    readonly property var fitted: Geometry.fit(draft, display.bounds, modelData.minWidth || 96, modelData.minHeight || 96, 1)
                    // A rotated widget's surface is its bounding box, so no corner is clipped.
                    readonly property int angle: PluginRegistry.rotation(placement)
                    readonly property var box: Geometry.rotatedBox(fitted, angle, display.bounds)
                    function save() {
                        draft = Geometry.fit(draft, display.bounds, modelData.minWidth || 96, modelData.minHeight || 96, desktop.grid);
                        gesturing = false;
                        PluginRegistry.change("place", modelData, {instance: placement.instance, geometry: draft});
                    }
                    function size(factor) {
                        draft = Geometry.scale(fitted, display.bounds, modelData.minWidth || 96, modelData.minHeight || 96, factor);
                        PluginRegistry.change("place", modelData, {instance: placement.instance, geometry: draft});
                    }
                    onPlacementChanged: if (!gesturing) draft = Object.assign({}, placement)
                    screen: display.modelData
                    anchors { top: true; left: true; right: content.editing; bottom: content.editing }
                    margins.left: content.editing ? 0 : box.x; margins.top: content.editing ? 0 : box.y
                    implicitWidth: box.width; implicitHeight: box.height
                    color: "transparent"
                    exclusionMode: ExclusionMode.Ignore
                    WlrLayershell.namespace: content.surface === "none" ? "eitr-plugin-transparent" : "eitr-plugin-widget"
                    readonly property bool aboveWindows: !!placement.aboveWindows
                    visible: content.editing || !aboveWindows || !display.fullscreen
                    WlrLayershell.layer: content.editing ? WlrLayer.Overlay : aboveWindows ? WlrLayer.Top : WlrLayer.Bottom
                    WlrLayershell.keyboardFocus: content.editing ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
                    // Input follows the rotated bounding box; above-window widgets pass clicks through.
                    mask: Region { item: !window.aboveWindows || content.editing ? hitBox : null }
                    Item {
                        id: hitBox
                        x: content.editing ? window.box.x : 0; y: content.editing ? window.box.y : 0
                        width: window.box.width; height: window.box.height
                    }
                    Connections {
                        target: PluginRegistry
                        function onWidgetAction(plugin, id, instance, action, custom) {
                            if (plugin !== window.modelData.plugin || id !== window.modelData.id || instance !== window.placement.instance) return;
                            if (custom) content.selectMenu(action);
                            else content.menuAction(action);
                        }
                    }
                    PluginWidget {
                        id: content
                        x: hitBox.x + (window.box.width - width) / 2; y: hitBox.y + (window.box.height - height) / 2
                        width: window.fitted.width; height: window.fitted.height
                        rotation: window.angle
                        entry: window.modelData
                        originX: window.fitted.x; originY: window.fitted.y
                        onMenuEntriesChanged: PluginRegistry.setMenu(window.placement, menuEntries)
                        Component.onCompleted: PluginRegistry.setMenu(window.placement, menuEntries)
                        active: window.visible
                        surface: PluginRegistry.widgetSurface(window.modelData)
                        aboveWindows: window.aboveWindows
                        onSizeRequested: factor => window.size(factor)
                        foreground: desktop.foreground; background: desktop.background; accent: desktop.accent
                        editing: PluginRegistry.editing && (!PluginRegistry.editTarget || PluginRegistry.editingCopy(window.placement))
                        onBegun: { window.gestureStart = Object.assign({}, window.fitted); window.gesturing = true; }
                        onMoved: function(deltaX, deltaY) {
                            window.gesturing = true;
                            window.draft = Geometry.delta(window.gestureStart, deltaX, deltaY, false);
                        }
                        onResized: function(deltaX, deltaY) {
                            window.gesturing = true;
                            window.draft = Geometry.delta(window.gestureStart, deltaX, deltaY, true);
                        }
                        onFinished: window.save()
                    }
                }
            }
        }
    }
}
