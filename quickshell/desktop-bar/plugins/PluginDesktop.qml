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
    PluginWidgetMenuHost { foreground: desktop.foreground; background: desktop.background; accent: desktop.accent }
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
            // Keyed by copy, not by the placement objects: a settings change then updates the
            // existing window (and keeps its open menu) instead of rebuilding it.
            readonly property var copies: PluginRegistry.placed("widgets", display.modelData.name)
            Variants {
                model: display.copies.map(copy => copy.plugin + "/" + copy.id + "/" + copy.geometry.instance)
                PanelWindow {
                    id: window
                    required property string modelData
                    readonly property var entry: display.copies.find(copy => copy.plugin + "/" + copy.id + "/" + copy.geometry.instance === modelData) || window.lastEntry
                    // The last known copy, while Variants removes a window whose copy is gone.
                    property var lastEntry: ({geometry: {}})
                    onEntryChanged: if (entry !== lastEntry) lastEntry = entry
                    readonly property var placement: entry.geometry
                    property var draft: Object.assign({}, placement)
                    property bool gesturing: false
                    property var gestureStart: null
                    readonly property var fitted: Geometry.fit(draft, display.bounds, window.entry.minWidth || 96, window.entry.minHeight || 96, 1)
                    // A rotated widget's surface is its bounding box, so no corner is clipped.
                    readonly property int angle: PluginRegistry.rotation(placement)
                    readonly property var box: Geometry.rotatedBox(fitted, angle, display.bounds)
                    function save() {
                        draft = Geometry.fit(draft, display.bounds, window.entry.minWidth || 96, window.entry.minHeight || 96, desktop.grid);
                        gesturing = false;
                        PluginRegistry.change("place", window.entry, {instance: placement.instance, geometry: draft});
                    }
                    function size(factor) {
                        draft = Geometry.scale(fitted, display.bounds, window.entry.minWidth || 96, window.entry.minHeight || 96, factor);
                        PluginRegistry.change("place", window.entry, {instance: placement.instance, geometry: draft});
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
                    // Input follows the turned widget itself (strips inside its bounding box), so the
                    // box's empty corners still reach the desktop; editing takes the whole box and
                    // above-window widgets pass clicks through.
                    readonly property var strips: Geometry.rotatedStrips(fitted.width, fitted.height, angle, box.width, box.height, 24)
                    property var stripRegions: []
                    function rebuildMask() {
                        for (const region of stripRegions) region.destroy();
                        stripRegions = strips.map(strip => stripRegion.createObject(window, strip));
                    }
                    onStripsChanged: rebuildMask()
                    Component.onCompleted: rebuildMask()
                    Component { id: stripRegion; Region {} }
                    mask: Region {
                        item: content.editing ? hitBox : null
                        regions: !window.aboveWindows && !content.editing ? window.stripRegions : []
                    }
                    Item {
                        id: hitBox
                        x: content.editing ? window.box.x : 0; y: content.editing ? window.box.y : 0
                        width: window.box.width; height: window.box.height
                    }
                    Connections {
                        target: PluginRegistry
                        function onWidgetAction(plugin, id, instance, action, custom) {
                            if (plugin !== window.entry.plugin || id !== window.entry.id || instance !== window.placement.instance) return;
                            if (custom) content.selectMenu(action);
                            else content.menuAction(action);
                        }
                    }
                    PluginWidget {
                        id: content
                        x: hitBox.x + (window.box.width - width) / 2; y: hitBox.y + (window.box.height - height) / 2
                        width: window.fitted.width; height: window.fitted.height
                        rotation: window.angle
                        entry: window.entry
                        originX: window.fitted.x; originY: window.fitted.y
                        onMenuEntriesChanged: PluginRegistry.setMenu(window.placement, menuEntries)
                        Component.onCompleted: PluginRegistry.setMenu(window.placement, menuEntries)
                        active: window.visible
                        surface: PluginRegistry.widgetSurface(window.entry)
                        aboveWindows: window.aboveWindows
                        onSizeRequested: factor => window.size(factor)
                        // The menu opens in its own window, in display coordinates.
                        onMenuRequested: position => PluginRegistry.openWidgetMenu(window.placement,
                            position.x + (content.editing ? 0 : window.box.x), position.y + (content.editing ? 0 : window.box.y))
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
                        onRotating: degrees => PluginRegistry.previewRotation(window.placement, degrees)
                        onRotationFinished: degrees => PluginRegistry.change("rotate", window.entry, {instance: window.placement.instance, rotation: degrees})
                    }
                }
            }
        }
    }
}
