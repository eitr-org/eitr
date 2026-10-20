import QtQuick
import Eitr as Eitr
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    Component.onCompleted: Quickshell.watchFiles = Quickshell.env("EITR_LIVE_RELOAD") === "1"
    id: root
    property real progress: 0
    property bool started: false
    readonly property string next: Quickshell.env("EITR_NEXT_WALLPAPER")
    // Monitor name to image URI ("*" for any other), from transition.py: each
    // screen reveals from what it shows to the file commit gives it (21:9 on ultrawides).
    readonly property var previousImages: parse(Quickshell.env("EITR_PREVIOUS_WALLPAPERS"))
    readonly property var nextImages: parse(Quickshell.env("EITR_NEXT_WALLPAPERS"))
    function parse(text) {
        try { return JSON.parse(text || "{}"); } catch (error) { return {}; }
    }
    function imageFor(images, screenName, fallback) {
        return images[screenName] || images["*"] || fallback;
    }
    function start() {
        if (started) return;
        if (windows.instances.some(window => !window.ready)) return;
        started = true;
        // Allow the initial old-wallpaper frame to be presented first.
        prepare.start();
    }
    NumberAnimation {
        id: reveal
        target: root; property: "progress"
        from: 0; to: 1; duration: 650; easing.type: Easing.InOutCubic
        // Only replace Hyprpaper once the new image completely covers it.
        onFinished: commit.running = true
    }
    Process {
        id: commit
        command: ["python3", Eitr.Paths.code("walker/scripts/actions/wallpaper/transition.py"), "commit", root.next]
        onExited: function(exitCode) {
            if (exitCode === 0) handoff.start();
            else Qt.exit(1);
        }
    }
    Timer { id: prepare; interval: 120; onTriggered: reveal.start(); }
    // Keep the completed frame covering Hyprpaper until the compositor catches up.
    Timer { id: handoff; interval: 250; onTriggered: Qt.quit(); }
    Timer { interval: 10000; running: true; onTriggered: Qt.exit(1); }
    // A broken image can never become ready; fail now so transition.py
    // commits the static wallpaper instead of waiting for the timeout.
    function failOnError(status) {
        if (status === Image.Error) Qt.exit(1);
    }
    Variants {
        id: windows
        model: Quickshell.screens
        PanelWindow {
            id: window
            required property var modelData
            readonly property string previousImage: root.imageFor(root.previousImages, modelData.name, "")
            readonly property bool ready: newImage.status === Image.Ready && (oldImage.status === Image.Ready || previousImage === "")
            onReadyChanged: root.start()
            Component.onCompleted: {
                // Local images may fail before the status handlers run.
                root.failOnError(oldImage.status);
                root.failOnError(newImage.status);
                Qt.callLater(root.start);
            }
            screen: modelData
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "eitr-wallpaper-transition"
            WlrLayershell.layer: WlrLayer.Bottom
            mask: Region {}
            color: "transparent"
            Image {
                id: oldImage
                anchors.fill: parent
                source: window.previousImage
                fillMode: Image.PreserveAspectCrop
                onStatusChanged: root.failOnError(status)
            }
            Item {
                id: circleMask
                anchors.fill: parent
                visible: false
                layer.enabled: true
                Rectangle {
                    anchors.centerIn: parent
                    width: Math.sqrt(window.width * window.width + window.height * window.height) * root.progress
                    height: width
                    radius: width / 2
                    color: "white"
                }
            }
            Image {
                id: newImage
                anchors.fill: parent
                source: root.imageFor(root.nextImages, window.modelData.name, root.next)
                fillMode: Image.PreserveAspectCrop
                onStatusChanged: root.failOnError(status)
                layer.enabled: true
                layer.effect: MultiEffect {
                    maskEnabled: true
                    maskSource: circleMask
                    maskThresholdMin: 0.5
                    maskSpreadAtMin: 0.5
                }
            }
        }
    }
}
