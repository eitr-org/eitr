import Eitr as Eitr
import QtQuick
import "ObsQueue.js" as ObsQueue
import "PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    waitForFreshData: true
    implicitWidth: 328
    implicitHeight: content.implicitHeight + verticalContentInset
    property string status: ""
    property string actionError: ""
    property string pendingAction: ""
    property string pendingArgument: ""
    // Actions the recording popup runs on live capture; their errors stay in that popup.
    readonly property var liveActions: ["chapter", "mic-mute", "mic-unmute", "camera-on", "camera-off", "scene"]
    property bool preparingStart: false
    property bool awaitingState: false
    property bool editing: false
    property var captureOptions: ({})
    property var pendingOptionChanges: ({})
    signal captureStarting()
    readonly property bool busy: pendingAction !== ""
    property var obsState: ({ready: false, recording: false, paused: false, streaming: false})
    readonly property bool controlsReady: obsState.ready && !busy
    readonly property string controlScript: Quickshell.shellDir + "/scripts/obs-control.py"

    function refresh() {
        if (busy && !awaitingState) return;
        if (!actionProcess.running) ObsStatus.refresh();
    }
    function run(action, argument) {
        if (busy) return;
        status = "";
        actionError = "";
        pendingAction = action;
        pendingArgument = argument || "";
        preparingStart = action === "record" || action === "stream";
        if (preparingStart) editing = false;
        awaitingState = false;
        if (!optionWriter.running) beginAction();
    }
    function beginAction() {
        actionProcess.command = ["python3", menu.controlScript, preparingStart ? "prepare" : pendingAction]
            .concat(!preparingStart && pendingArgument ? [pendingArgument] : []);
        actionProcess.running = true;
    }
    function loadOptions() {
        if (!optionQuery.running && !optionWriter.running) optionQuery.running = true;
    }
    function saveOption(key, enabled) {
        if (busy) return;
        captureOptions = ObsQueue.withOption(captureOptions, key, enabled);
        pendingOptionChanges = ObsQueue.enqueue(pendingOptionChanges, key, enabled);
        writeNextOption();
    }
    function writeNextOption() {
        if (optionWriter.running) return;
        const next = ObsQueue.takeNext(pendingOptionChanges);
        if (!next) return;
        pendingOptionChanges = next.remaining;
        optionWriter.command = ["python3", menu.controlScript].concat(ObsQueue.optionArguments(next.key, next.enabled));
        optionWriter.running = true;
    }
    onOpenedChanged: if (opened) { refresh(); loadOptions(); }
    Component.onCompleted: obsState = ObsStatus.state
    Process {
        id: optionQuery
        command: ["python3", menu.controlScript, "options"]
        stdout: StdioCollector { id: optionOutput }
        onExited: function(code) {
            const received = optionOutput.text;
            menu.updateContent(function() {
                if (optionWriter.running || Object.keys(menu.pendingOptionChanges).length) return;
                try { if (code === 0) menu.applySnapshot("captureOptions", JSON.parse(received)); }
                catch (error) { menu.status = "Recording settings unavailable"; }

            });
        }
    }
    Process {
        id: optionWriter
        stdout: StdioCollector { id: optionResult }
        onExited: function(code) {
            if (code !== 0) {
                menu.actionError = optionResult.text.trim() || Eitr.I18n.tr("Could not save recording settings");
                menu.status = menu.actionError;
                menu.pendingOptionChanges = ({});
                menu.pendingAction = "";
                menu.preparingStart = false;
                menu.loadOptions();
            } else {
                menu.writeNextOption();
                if (!optionWriter.running && menu.busy) menu.beginAction();
            }
        }
    }
    Timer {
        id: startDelay
        interval: menu.transitionDuration + 50
        onTriggered: {
            actionProcess.command = ["python3", menu.controlScript, menu.pendingAction];
            actionProcess.running = true;
        }
    }
    Connections {
        target: ObsStatus
        function onReceived(snapshot) {
            menu.updateContent(function() {
                if (actionProcess.running || (menu.busy && !menu.awaitingState)) return;
                menu.applySnapshot("obsState", snapshot);
                menu.status = menu.actionError || snapshot.error || (!snapshot.ready ? Eitr.I18n.tr("OBS status unavailable") : "");
                menu.pendingAction = "";
                menu.awaitingState = false;
            });
        }
    }
    Process {
        id: actionProcess
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            if (code !== 0) {
                menu.actionError = output.text.trim() || Eitr.I18n.tr("OBS command failed");
                menu.status = menu.actionError;
                if (menu.liveActions.indexOf(menu.pendingAction) < 0) menu.opened = true;
                menu.pendingAction = "";
                menu.preparingStart = false;
            } else if (menu.preparingStart) {
                menu.preparingStart = false;
                menu.opened = false;
                menu.captureStarting();
                startDelay.restart();
            } else {
                menu.awaitingState = true;
                menu.refresh();
            }
        }
    }
    Column {
        id: content
        x: 0
        y: 0
        width: parent.width
        spacing: 12
        Row {
            width: parent.width
            spacing: 4
            PanelHeading {
                width: parent.width - (editButton.visible ? 76 : 38)
                height: 34
                text: Eitr.I18n.tr("OBS Studio")
                foreground: menu.foreground; accent: menu.accent; rune: "capture"
            }
            PanelButton {
                id: editButton
                visible: !menu.obsState.recording && !menu.obsState.streaming && menu.pendingAction !== "record" && menu.pendingAction !== "stream"
                icon: true
                compactIconBackground: true
                height: 34
                text: "󰏫"
                foreground: menu.foreground
                available: !menu.busy
                onClicked: menu.editing = !menu.editing
                HoverHandler { id: editHover }
                BarTooltip { target: editButton; hovered: editHover.hovered; text: Eitr.I18n.tr("Recording options"); foreground: menu.foreground; background: menu.background }
            }
            PanelMoreButton {
                height: 34
                foreground: menu.foreground; background: menu.background
                actions: [
                    {title: Eitr.I18n.tr("Open recordings"), glyph: "󰉋", available: menu.controlsReady && !menu.busy, run: () => menu.run("folder")},
                    {title: Eitr.I18n.tr("Open OBS"), glyph: "󰻂", available: menu.controlsReady && !menu.busy, run: () => menu.run("open")}
                ]
            }
        }
        Column {
            width: content.width
            visible: menu.editing && !menu.obsState.recording && !menu.obsState.streaming
            spacing: 4
            Repeater {
                model: ["audio", "mic", "webcam"]
                Row {
                    id: optionRow
                    required property string modelData
                    width: content.width
                    property var option: menu.captureOptions[modelData] || {enabled: false, available: false}
                    Text {
                        width: parent.width - 52
                        height: 40
                        verticalAlignment: Text.AlignVCenter
                        text: ({audio: Eitr.I18n.tr("Desktop audio"), mic: Eitr.I18n.tr("Microphone"), webcam: Eitr.I18n.tr("Webcam")})[optionRow.modelData]
                        color: menu.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.controlSize
                    }
                    PanelSwitch {
                        anchors.verticalCenter: parent.verticalCenter
                        checked: optionRow.option.enabled
                        enabled: optionRow.option.available && !menu.busy
                        foreground: menu.foreground
                        accent: menu.accent
                        onToggled: menu.saveOption(optionRow.modelData, checked)
                    }
                    HoverHandler { id: optionHover }
                    BarTooltip {
                        target: optionRow
                        hovered: optionHover.hovered && !optionRow.option.available
                        text: Eitr.I18n.tr("Configure this source in OBS")
                        foreground: menu.foreground
                        background: menu.background
                    }
                }
            }
        }
        Repeater {
            model: ["Recording", "Streaming"]
            Column {
                id: section
                required property string modelData
                width: content.width
                spacing: 8
                readonly property bool recording: modelData === "Recording"
                readonly property bool active: recording ? menu.obsState.recording : menu.obsState.streaming
                PanelDivider {
                    width: parent.width
                    height: 8
                    foreground: menu.foreground
                }
                Row {
                    width: parent.width
                    spacing: 4
                    Text {
                        width: parent.width - (section.recording && section.active ? 76 : 38)
                        height: 34
                        verticalAlignment: Text.AlignVCenter
                        text: section.modelData
                        color: menu.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.controlSize
                    }
                    ObsActionButton {
                        controller: menu
                        visible: section.recording && section.active
                        action: menu.obsState.paused ? "resume" : "pause"
                        description: menu.obsState.paused ? Eitr.I18n.tr("Resume recording") : Eitr.I18n.tr("Pause recording")
                        glyph: menu.obsState.paused ? "󰐊" : "󰏤"
                    }
                    ObsActionButton {
                        controller: menu
                        action: section.recording ? (section.active ? "stop" : "record") : (section.active ? "stop-stream" : "stream")
                        description: section.modelData === "Recording" ? (section.active ? Eitr.I18n.tr("Stop recording") : Eitr.I18n.tr("Start recording")) : (section.active ? Eitr.I18n.tr("Stop streaming") : Eitr.I18n.tr("Start streaming"))
                        glyph: section.active ? "󰓛" : "󰐌"
                    }
                }
            }
        }
        Text {
            width: content.width
            visible: text !== ""
            text: menu.status
            wrapMode: Text.Wrap
            color: menu.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.secondarySize
        }
    }
}
