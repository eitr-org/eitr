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
                    property var draft: Object.assign({}, modelData.geometry)
                    property bool gesturing: false
                    property var gestureStart: null
                    readonly property var fitted: Geometry.fit(draft, display.bounds, modelData.minWidth || 96, modelData.minHeight || 96, 1)
                    function save() {
                        draft = Geometry.fit(draft, display.bounds, modelData.minWidth || 96, modelData.minHeight || 96, desktop.grid);
                        gesturing = false;
                        PluginRegistry.change("place", modelData, display.modelData.name, draft);
                    }
                    function size(factor) {
                        draft = Geometry.scale(fitted, display.bounds, modelData.minWidth || 96, modelData.minHeight || 96, factor);
                        PluginRegistry.change("place", modelData, display.modelData.name, draft);
                    }
                    onModelDataChanged: if (!gesturing) draft = Object.assign({}, modelData.geometry)
                    screen: display.modelData
                    anchors { top: true; left: true; right: content.editing; bottom: content.editing }
                    margins.left: content.editing ? 0 : fitted.x; margins.top: content.editing ? 0 : fitted.y
                    implicitWidth: fitted.width; implicitHeight: fitted.height
                    color: "transparent"
                    exclusionMode: ExclusionMode.Ignore
                    WlrLayershell.namespace: content.surface === "none" ? "eitr-plugin-transparent" : "eitr-plugin-widget"
                    readonly property bool aboveWindows: !!modelData.geometry.aboveWindows
                    visible: content.editing || !aboveWindows || !display.fullscreen
                    WlrLayershell.layer: content.editing ? WlrLayer.Overlay : aboveWindows ? WlrLayer.Top : WlrLayer.Bottom
                    WlrLayershell.keyboardFocus: content.editing ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
                    mask: Region { item: !window.aboveWindows || content.editing ? content : null }
                    Connections {
                        target: PluginRegistry
                        function onWidgetAction(plugin, id, monitor, action, custom) {
                            if (plugin !== window.modelData.plugin || id !== window.modelData.id || monitor !== display.modelData.name) return;
                            if (custom) content.selectMenu(action);
                            else content.menuAction(action);
                        }
                    }
                    PluginWidget {
                        id: content
                        x: editing ? window.fitted.x : 0; y: editing ? window.fitted.y : 0
                        width: window.fitted.width; height: window.fitted.height
                        entry: window.modelData
                        originX: window.fitted.x; originY: window.fitted.y
                        onMenuEntriesChanged: PluginRegistry.setMenu(window.modelData, display.modelData.name, menuEntries)
                        Component.onCompleted: PluginRegistry.setMenu(window.modelData, display.modelData.name, menuEntries)
                        active: window.visible
                        surface: PluginRegistry.widgetSurface(window.modelData)
                        aboveWindows: window.aboveWindows
                        onSizeRequested: factor => window.size(factor)
                        onSurfaceRequested: surface => PluginRegistry.change("surface", window.modelData, display.modelData.name, null, surface)
                        onLayerRequested: PluginRegistry.change("toggle-layer", window.modelData, display.modelData.name, null)
                        onRemoveRequested: PluginRegistry.change("unplace", window.modelData, display.modelData.name, null)
                        foreground: desktop.foreground; background: desktop.background; accent: desktop.accent
                        editing: PluginRegistry.editing && (!PluginRegistry.editTarget || (PluginRegistry.editTarget.plugin === window.modelData.plugin && PluginRegistry.editTarget.id === window.modelData.id && PluginRegistry.editTarget.monitor === display.modelData.name))
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
