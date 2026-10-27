pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "PluginGeometry.js" as Geometry

Scope {
    id: desktop
    required property color foreground
    required property color background
    required property color accent
    property real grid: 6
    property var monitors: []
    property bool refreshPending: false
    function refresh() {
        if (monitorQuery.running) refreshPending = true;
        else monitorQuery.running = true;
    }
    Process {
        id: monitorQuery
        command: ["hyprctl", "-j", "monitors"]
        running: true
        stdout: StdioCollector { id: monitorOutput }
        onExited: function(code) {
            if (desktop.refreshPending) { desktop.refreshPending = false; Qt.callLater(desktop.refresh); }
            if (code === 0) try { desktop.monitors = JSON.parse(monitorOutput.text); } catch (error) {}
        }
    }
    Connections {
        target: Quickshell
        function onScreensChanged() { desktop.refresh(); }
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (["monitoradded", "monitorremoved", "configreloaded"].indexOf(event.name) !== -1) desktop.refresh();
        }
    }
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
                    anchors { top: true; left: true }
                    margins.left: fitted.x; margins.top: fitted.y
                    implicitWidth: fitted.width; implicitHeight: fitted.height
                    color: "transparent"
                    exclusionMode: ExclusionMode.Ignore
                    WlrLayershell.namespace: content.surface === "none" ? "eitr-plugin-transparent" : "eitr-plugin-widget"
                    readonly property bool aboveWindows: !!modelData.geometry.aboveWindows
                    visible: content.editing || !aboveWindows || !display.fullscreen
                    WlrLayershell.layer: content.editing || content.menuOpen ? WlrLayer.Overlay : aboveWindows ? WlrLayer.Top : WlrLayer.Bottom
                    WlrLayershell.keyboardFocus: content.editing || content.menuOpen ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
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
                        anchors.fill: parent; entry: window.modelData
                        originX: window.fitted.x; originY: window.fitted.y
                        onMenuEntriesChanged: PluginRegistry.setMenu(window.modelData, display.modelData.name, menuEntries)
                        Component.onCompleted: PluginRegistry.setMenu(window.modelData, display.modelData.name, menuEntries)
                        active: window.visible
                        surface: window.modelData.geometry.surface || window.modelData.surface || "panel"
                        aboveWindows: window.aboveWindows
                        onSizeRequested: factor => window.size(factor)
                        onSurfaceRequested: surface => PluginRegistry.change("surface", window.modelData, display.modelData.name, null, surface)
                        onLayerRequested: PluginRegistry.change("toggle-layer", window.modelData, display.modelData.name, null)
                        onRemoveRequested: PluginRegistry.change("unplace", window.modelData, display.modelData.name, null)
                        foreground: desktop.foreground; background: desktop.background; accent: desktop.accent
                        editing: PluginRegistry.editing && (!PluginRegistry.editTarget || (PluginRegistry.editTarget.plugin === window.modelData.plugin && PluginRegistry.editTarget.id === window.modelData.id && PluginRegistry.editTarget.monitor === display.modelData.name))
                        onMoved: function(deltaX, deltaY) {
                            window.gesturing = true;
                            window.draft = Geometry.delta(window.fitted, deltaX, deltaY, false);
                        }
                        onResized: function(deltaX, deltaY) {
                            window.gesturing = true;
                            window.draft = Geometry.delta(window.fitted, deltaX, deltaY, true);
                        }
                        onFinished: window.save()
                    }
                }
            }
        }
    }
}
