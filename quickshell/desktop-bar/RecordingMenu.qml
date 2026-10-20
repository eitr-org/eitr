import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Io

// The recording dot's popup while OBS records or streams: elapsed time and size,
// pause/stop/chapter, the OBS microphone and camera, and the scene. Actions go
// through ObsMenu (the controller); details come from obs-control.py details.
ThemedPopup {
    id: menu
    required property var controller
    property var details: ({})
    property real fetchedAt: 0
    property real now: Date.now()
    readonly property bool recording: controller.obsState.recording
    readonly property bool streaming: controller.obsState.streaming
    readonly property bool paused: controller.obsState.paused
    readonly property var scenes: details.scenes || []
    readonly property var microphone: details.mic || {available: false, muted: false}
    readonly property var camera: details.webcam || {available: false, enabled: false}
    implicitWidth: 340
    implicitHeight: content.implicitHeight + verticalContentInset

    // OBS reports times every refresh; between them the clock runs locally.
    function elapsed(seconds, running) {
        const value = (seconds || 0) + (running && fetchedAt ? (now - fetchedAt) / 1000 : 0);
        const whole = Math.max(0, Math.floor(value));
        const pad = number => String(number).padStart(2, "0");
        return pad(Math.floor(whole / 3600)) + ":" + pad(Math.floor(whole % 3600 / 60)) + ":" + pad(whole % 60);
    }
    function size(bytes) {
        if (!bytes) return "0 MB";
        return bytes >= 1e9 ? (bytes / 1e9).toFixed(2) + " GB" : Math.max(1, Math.round(bytes / 1e6)) + " MB";
    }
    function refresh() {
        if (!detailsQuery.running) detailsQuery.running = true;
    }

    onOpenedChanged: if (opened) refresh()
    Timer { interval: 2000; repeat: true; running: menu.opened; onTriggered: menu.refresh() }
    Timer { interval: 500; repeat: true; running: menu.opened; onTriggered: menu.now = Date.now() }
    Process {
        id: detailsQuery
        command: ["python3", menu.controller.controlScript, "details"]
        stdout: StdioCollector { id: detailsOutput }
        onExited: function(code) {
            try {
                if (code === 0) {
                    menu.details = JSON.parse(detailsOutput.text);
                    menu.fetchedAt = Date.now();
                    menu.now = menu.fetchedAt;
                }
            } catch (error) {}
        }
    }
    Connections {
        target: menu.controller
        function onObsStateChanged() {
            if (!menu.controller.obsState.recording && !menu.controller.obsState.streaming && !menu.controller.busy)
                menu.opened = false;
        }
        function onBusyChanged() {
            if (menu.controller.busy) return;
            if (!menu.controller.obsState.recording && !menu.controller.obsState.streaming) menu.opened = false;
            else if (menu.opened) menu.refresh();
        }
    }

    component Toggle: PanelButton {
        id: toggle
        property string description
        property string glyph
        icon: true
        compactIconBackground: true
        height: 34
        width: 34
        text: glyph
        foreground: menu.foreground
        HoverHandler { id: toggleHover }
        BarTooltip { target: toggle; hovered: toggleHover.hovered; text: toggle.description; foreground: menu.foreground; background: menu.background }
    }

    Column {
        id: content
        width: parent.width
        spacing: 10
        Row {
            visible: menu.recording
            width: parent.width
            spacing: 4
            PanelHeading {
                width: parent.width - 3 * 38
                anchors.verticalCenter: parent.verticalCenter
                text: menu.elapsed(menu.details.recordingSeconds, menu.recording && !menu.paused)
                subtitle: menu.paused ? Eitr.I18n.tr("PAUSED · {size}", {size: menu.size(menu.details.recordingBytes)}) : Eitr.I18n.tr("RECORDING · {size}", {size: menu.size(menu.details.recordingBytes)})
                foreground: menu.foreground; accent: menu.accent; rune: "recording"
            }
            ObsActionButton {
                controller: menu.controller
                action: menu.paused ? "resume" : "pause"
                description: menu.paused ? Eitr.I18n.tr("Resume recording") : Eitr.I18n.tr("Pause recording")
                glyph: menu.paused ? "\u{F040A}" : "\u{F03E4}"
            }
            ObsActionButton {
                controller: menu.controller
                action: "chapter"
                description: Eitr.I18n.tr("Add a chapter marker")
                glyph: "\u{F00C0}"
            }
            ObsActionButton {
                controller: menu.controller
                action: "stop"
                description: Eitr.I18n.tr("Stop recording")
                glyph: "\u{F04DB}"
            }
        }
        Row {
            visible: menu.streaming
            width: parent.width
            spacing: 8
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: liveLabel.implicitWidth + 12; height: 20
                radius: DesktopStyle.radius(4)
                color: "#e05c68"
                Text {
                    id: liveLabel
                    anchors.centerIn: parent
                    text: Eitr.I18n.tr("LIVE")
                    color: "#ffffff"
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    font.bold: true
                }
            }
            Text {
                width: parent.width - liveLabel.implicitWidth - 12 - 8 * 2 - 34
                anchors.verticalCenter: parent.verticalCenter
                text: menu.elapsed(menu.details.streamingSeconds, menu.streaming)
                color: menu.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.headingSize
                font.bold: true
            }
            ObsActionButton {
                controller: menu.controller
                action: "stop-stream"
                description: Eitr.I18n.tr("Stop streaming")
                glyph: "\u{F04DB}"
            }
        }
        PanelDivider {
            visible: menu.microphone.available || menu.camera.available || menu.scenes.length > 1
            width: parent.width
            height: 8
            foreground: menu.foreground
        }
        Row {
            visible: menu.microphone.available || menu.camera.available
            spacing: 8
            Toggle {
                visible: menu.microphone.available
                glyph: menu.microphone.muted ? "\u{F036D}" : "\u{F036C}"
                description: menu.microphone.muted ? Eitr.I18n.tr("Unmute the OBS microphone") : Eitr.I18n.tr("Mute the OBS microphone")
                available: menu.controller.controlsReady
                loading: menu.controller.pendingAction === "mic-mute" || menu.controller.pendingAction === "mic-unmute"
                onClicked: menu.controller.run(menu.microphone.muted ? "mic-unmute" : "mic-mute")
            }
            Toggle {
                visible: menu.camera.available
                glyph: menu.camera.enabled ? "\u{F0100}" : "\u{F05DF}"
                description: menu.camera.enabled ? Eitr.I18n.tr("Hide the camera") : Eitr.I18n.tr("Show the camera")
                available: menu.controller.controlsReady
                loading: menu.controller.pendingAction === "camera-on" || menu.controller.pendingAction === "camera-off"
                onClicked: menu.controller.run(menu.camera.enabled ? "camera-off" : "camera-on")
            }
        }
        Text {
            visible: menu.scenes.length > 1
            text: Eitr.I18n.tr("SCENE")
            color: menu.foreground
            opacity: 0.6
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
        Flow {
            visible: menu.scenes.length > 1
            width: parent.width
            spacing: 6
            Repeater {
                model: menu.scenes
                PanelButton {
                    required property string modelData
                    height: 28
                    outlined: true
                    textSize: PanelStyle.captionSize
                    text: modelData
                    foreground: menu.foreground
                    selected: modelData === menu.details.scene
                    available: menu.controller.controlsReady && !selected
                    loading: menu.controller.pendingAction === "scene" && menu.controller.pendingArgument === modelData
                    onClicked: menu.controller.run("scene", modelData)
                }
            }
        }
        Text {
            visible: menu.controller.actionError !== ""
            width: parent.width
            wrapMode: Text.Wrap
            text: menu.controller.actionError
            color: menu.foreground
            opacity: 0.8
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.secondarySize
        }
    }
}
