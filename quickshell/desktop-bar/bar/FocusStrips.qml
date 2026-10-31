import ".."
import QtQuick
import Quickshell
import Quickshell.Wayland

// Focus mode's strip on every display: tabs, clock and network/battery status.
Scope {
    property var host
    Variants {
        model: FocusMode.enabled ? Quickshell.screens : []
        delegate: Component {
            PanelWindow {
                required property var modelData
                screen: modelData
                anchors { top: true; left: true; right: true }
                implicitHeight: 28; exclusiveZone: 28
                color: "transparent"
                WlrLayershell.namespace: "eitr-focus-strip"
                FocusStrip {
                    anchors.fill: parent
                    tabs: FocusMode.tabs(modelData)
                    foreground: host.fg; background: host.workspaceMenuBg; accent: host.activeBg
                    clockText: Qt.formatDateTime(focusClock.date, host.barClock === "24h" ? "HH:mm" : "h:mm AP")
                    networkText: host.focusNetworkGlyph
                    batteryText: host.battery.available ? host.batteryIcon + " " + Math.round(host.battery.percent) + "%" : ""
                    onSelected: address => FocusMode.activate(address)
                }
            }
        }
    }
    SystemClock { id: focusClock; precision: SystemClock.Minutes }
}
