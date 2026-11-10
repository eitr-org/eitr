import ".."
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Services.Polkit
import Quickshell.Wayland

// The session's polkit authentication agent: administrator password prompts are drawn
// by the bar. Quickshell queues requests and exposes one AuthFlow at a time as
// agent.flow; the prompt covers the focused screen until that flow completes.
// hypr/scripts/polkit-fallback.sh asks `polkit status` after login and starts KDE's
// agent when this one has not registered.
Scope {
    id: prompt
    required property color foreground
    required property color background
    required property color accent
    property var defaultScreen: null
    readonly property var flow: agent.flow
    readonly property bool showing: !!flow && !flow.isCompleted
    property var promptScreen: null

    function focusedScreen() {
        const monitor = Hyprland.focusedMonitor;
        const screens = Quickshell.screens || [];
        return screens.find(screen => monitor && screen && screen.name === monitor.name) || defaultScreen || screens[0] || null;
    }
    // The screen is chosen once per request, so the prompt never jumps while typing.
    onShowingChanged: if (showing) promptScreen = focusedScreen()

    PolkitAgent { id: agent }

    IpcHandler {
        target: "polkit"
        function status(): string { return agent.isRegistered ? "registered" : "unregistered"; }
    }

    LazyLoader {
        active: prompt.showing && !!prompt.promptScreen
        PanelWindow {
            screen: prompt.promptScreen
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            color: "transparent"
            WlrLayershell.namespace: "eitr-polkit-prompt"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
            Rectangle { anchors.fill: parent; color: "#80000000" }
            // Clicks beside the card do nothing: only Cancel, Escape or an answer close it.
            MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }
            PolkitDialog {
                id: dialog
                anchors.centerIn: parent
                width: Math.min(implicitWidth, parent.width - 2 * 24)
                flow: prompt.flow
                foreground: prompt.foreground
                background: prompt.background
                accent: prompt.accent
                focus: true
                Component.onCompleted: Qt.callLater(dialog.focusPassword)
            }
        }
    }
}
