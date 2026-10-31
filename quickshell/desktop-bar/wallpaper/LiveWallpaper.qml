import ".."
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland
import "../Performance.js" as Performance

// A wallpaper that ships live layers (theme/motion/<wallpaper name>/) is drawn
// here over Hyprpaper's still copy: the starry sky, two aurora curtains that
// drift and breathe, then the ring with the emblem. The still image stays
// underneath for the lockscreen and as the fallback while layers load.
// Curtains update at 20 Hz on empty workspaces and 5 Hz behind windows.
// Fullscreen windows pause motion; failed Hyprpaper outputs use a still background here.
Scope {
    id: live
    property string wallpaper: ""
    // theme/current/backgrounds/<name>.png has its layers in theme/current/motion/<name>/.
    readonly property string motion: {
        var match = /^(.*)\/backgrounds\/([^/]+)\.(png|jpe?g|webp)$/i.exec(wallpaper);
        return match ? "file://" + match[1] + "/motion/" + match[2] + "/" : "";
    }
    property bool suspended: false
    property bool softwareRendering: true
    Process {
        id: rendererQuery
        command: ["python3", Quickshell.shellDir + "/scripts/rendering.py"]
        running: true
        stdout: StdioCollector {
            onStreamFinished: {
                try { live.softwareRendering = JSON.parse(text).software !== false; } catch (error) {}
            }
        }
    }
    Timer { interval: 5000; running: rendererQuery.running; onTriggered: rendererQuery.running = false }

    property var stillImages: ({})
    property var healthyOutputs: ({})
    property bool queryPending: false
    function checkWallpaper() {
        if (wallpaperQuery.running) queryPending = true;
        else wallpaperQuery.running = true;
    }
    Process {
        id: wallpaperQuery
        command: ["python3", Quickshell.shellDir + "/scripts/rendering.py", "--wallpaper"]
        running: true
        stdout: SplitParser {
            onRead: data => {
                try {
                    var result = JSON.parse(data);
                    live.stillImages = result.images;
                    if (result.healthy !== undefined) live.healthyOutputs = result.healthy;
                    if (live.wallpaper !== result.wallpaper) live.suspended = false;
                    live.wallpaper = result.wallpaper;
                } catch (error) {}
            }
        }
        onExited: {
            if (live.queryPending) {
                live.queryPending = false;
                live.checkWallpaper();
            }
        }
    }
    Connections {
        target: Quickshell
        function onScreensChanged() { live.checkWallpaper(); settledCheck.restart(); }
    }
    // A second, one-shot check gives login and wallpaper commits time to finish.
    Timer { id: settledCheck; interval: 3000; running: true; onTriggered: live.checkWallpaper() }
    PreferenceWatch {
        path: (Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config") + "/eitr/appearance.json"
        onChanged: { live.checkWallpaper(); settledCheck.restart(); }
    }

    FileView {
        path: Quickshell.env("HOME") + "/.cache/current-wallpaper"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: { live.wallpaper = text().trim(); live.suspended = false; live.checkWallpaper(); settledCheck.restart(); }
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
            readonly property bool occupied: monitor && monitor.activeWorkspace
                ? Performance.workspaceHasWindows(Hyprland.toplevels.values, monitor.activeWorkspace.id) : false
            // Only an output Hyprpaper is known not to draw; unknown (before the first check) is not.
            readonly property bool stillFallback: live.healthyOutputs[modelData.name] === false
            readonly property bool animate: !live.softwareRendering && !FocusMode.enabled && live.motion !== "" && !live.suspended
            visible: stillFallback || (animate && scene.ready)
            color: "transparent"
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "eitr-live-wallpaper"
            WlrLayershell.layer: window.animate ? WlrLayer.Bottom : WlrLayer.Background
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            mask: Region {}

            // Seconds of motion so far; every layer's position is a slow function of it.
            property real time: 0
            Timer {
                interval: Performance.wallpaperInterval(window.occupied)
                repeat: true
                running: window.visible && window.animate && !window.covered
                onTriggered: window.time += interval / 1000
            }

            Image {
                anchors.fill: parent
                visible: window.stillFallback
                source: window.stillFallback ? (live.stillImages[window.modelData.name] || live.stillImages["*"] || "") : ""
                fillMode: Image.PreserveAspectCrop
                sourceSize: Qt.size(Math.ceil(width * (window.screen ? window.screen.devicePixelRatio : 1)),
                                    Math.ceil(height * (window.screen ? window.screen.devicePixelRatio : 1)))
            }
            LiveWallpaperScene {
                id: scene
                anchors.fill: parent
                visible: window.animate && ready
                motion: live.softwareRendering ? "" : live.motion
                pixelRatio: window.screen ? window.screen.devicePixelRatio : 1
                time: window.time
            }
        }
    }
}
