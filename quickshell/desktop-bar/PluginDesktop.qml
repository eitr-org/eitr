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
                    readonly property var fitted: Geometry.fit(draft, display.bounds, modelData.minWidth || 96, modelData.minHeight || 96, desktop.grid)
                    onModelDataChanged: draft = Object.assign({}, modelData.geometry)
                    screen: display.modelData
                    anchors { top: true; left: true }
                    margins.left: fitted.x; margins.top: fitted.y
                    implicitWidth: fitted.width; implicitHeight: fitted.height
                    color: "transparent"
                    exclusionMode: ExclusionMode.Ignore
                    WlrLayershell.namespace: "eitr-plugin-widget"
                    readonly property bool aboveWindows: !!modelData.geometry.aboveWindows
                    visible: !aboveWindows || !display.fullscreen
                    WlrLayershell.layer: aboveWindows ? WlrLayer.Top : WlrLayer.Bottom
                    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
                    mask: Region { item: !window.aboveWindows || content.editing ? content : null }
                    PluginWidget {
                        id: content
                        anchors.fill: parent; entry: window.modelData
                        active: window.visible
                        foreground: desktop.foreground; background: desktop.background; accent: desktop.accent
                        editing: PluginRegistry.editing && (!PluginRegistry.editTarget || (PluginRegistry.editTarget.plugin === window.modelData.plugin && PluginRegistry.editTarget.id === window.modelData.id && PluginRegistry.editTarget.monitor === display.modelData.name))
                        onMoved: function(deltaX, deltaY) {
                            window.draft = Object.assign({}, window.draft, {x: window.draft.x + deltaX, y: window.draft.y + deltaY});
                        }
                        onResized: function(deltaX, deltaY) {
                            window.draft = Object.assign({}, window.draft, {width: window.draft.width + deltaX, height: window.draft.height + deltaY});
                        }
                        onFinished: PluginRegistry.change("place", window.modelData, display.modelData.name, window.fitted)
                    }
                }
            }
        }
    }
}
