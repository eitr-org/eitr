import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland

// A wallpaper that ships live layers (theme/motion/<wallpaper name>/) is drawn
// here over Hyprpaper's still copy: the starry sky, two aurora curtains that
// drift and breathe, then the ring with the emblem. The still image stays
// underneath for the lockscreen and as the fallback while layers load.
// The curtains move in twenty steps a second rather than every frame, because
// blurred windows re-blur whatever changes behind them; they stop behind
// fullscreen windows.
Scope {
    id: live
    property string wallpaper: ""
    // theme/current/backgrounds/<name>.png has its layers in theme/current/motion/<name>/.
    readonly property string motion: {
        var match = /^(.*)\/backgrounds\/([^/]+)\.(png|jpe?g|webp)$/i.exec(wallpaper);
        return match ? "file://" + match[1] + "/motion/" + match[2] + "/" : "";
    }
    property bool suspended: false

    FileView {
        path: Quickshell.env("HOME") + "/.cache/current-wallpaper"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: { live.wallpaper = text().trim(); live.suspended = false; }
        onLoadFailed: live.wallpaper = ""
    }

    IpcHandler {
        target: "liveWallpaper"
        // A wallpaper change hides the layers so its transition shows; the new
        // selection decides whether they come back.
        function suspend(): void { live.suspended = true; }
        function status(): string { return JSON.stringify({motion: live.motion, suspended: live.suspended}); }
    }

    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: window
            required property var modelData
            screen: modelData
            readonly property var monitor: Hyprland.monitorFor(modelData)
            readonly property bool covered: !!(monitor && monitor.activeWorkspace && monitor.activeWorkspace.hasFullscreen)
            visible: !FocusMode.enabled && live.motion !== "" && !live.suspended && scene.ready
            color: "transparent"
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "eitr-live-wallpaper"
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            mask: Region {}

            // Seconds of motion so far; every layer's position is a slow function of it.
            property real time: 0
            Timer {
                interval: 50
                repeat: true
                running: window.visible && !window.covered
                onTriggered: window.time += interval / 1000
            }

            LiveWallpaperScene {
                id: scene
                anchors.fill: parent
                motion: live.motion
                time: window.time
            }
        }
    }
}
