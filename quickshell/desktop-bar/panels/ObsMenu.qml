import ".."
import Eitr as Eitr
import QtQuick
import "../ObsQueue.js" as ObsQueue
import "../PanelStyle.js" as PanelStyle
import Quickshell

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
    property bool optionWriting: false
    property string optionToken: ""
    property string actionId: ""
    property string optionId: ""
    readonly property string optionsError: optionSnapshot && ["stale", "unavailable", "error"].includes(optionSnapshot.status)
        ? Eitr.I18n.tr("Recording settings unavailable") : ""
    onOptionsErrorChanged: status = actionError || optionsError || (!obsState.ready ? Eitr.I18n.tr("OBS status unavailable") : "")
    readonly property var optionSnapshot: DesktopData.topics["capture.options"]
    onOptionSnapshotChanged: {
        if (!optionSnapshot || optionSnapshot.status !== "ready") return;
        const snapshot = optionSnapshot.data;
        updateContent(function() {
            if (!menu.optionWriting && !Object.keys(menu.pendingOptionChanges).length)
                menu.applySnapshot("captureOptions", snapshot);
        });
    }
    property bool preparingStart: false
    property bool awaitingState: false
    property bool editing: false
    property var captureOptions: ({})
    property var pendingOptionChanges: ({})
    signal captureStarting()
    readonly property bool busy: pendingAction !== "" || (ObsStatus.busy && !optionWriting)
    property var obsState: ({ready: false, recording: false, paused: false, streaming: false})
    readonly property bool controlsReady: obsState.ready && !busy
    readonly property string controlScript: Quickshell.shellDir + "/scripts/obs-control.py"

    function refresh() { ObsStatus.refresh(); }
    function run(action, argument) {
        if (busy) return;
        status = "";
        actionError = "";
        pendingAction = action;
        pendingArgument = argument || "";
        preparingStart = action === "record" || action === "stream";
        if (preparingStart) editing = false;
        awaitingState = false;
        if (!optionWriting) beginAction();
    }
    function beginAction() {
        const id = ObsStatus.act(preparingStart ? "prepare" : pendingAction, preparingStart ? "" : pendingArgument,
            function(code, message) { menu.actionFinished(code, message); });
        if (id) actionId = id;
        else actionFinished("backend-unavailable", "");
    }
    function actionFinished(code, message) {
        actionId = "";
        if (code) {
            actionError = code === "outcome-unknown" ? Eitr.I18n.tr("Outcome unknown; refresh before retrying.") : (message || Eitr.I18n.tr("OBS command failed"));
            status = actionError;
            if (liveActions.indexOf(pendingAction) < 0) opened = true;
            pendingAction = "";
            preparingStart = false;
        } else if (preparingStart) {
            preparingStart = false;
            opened = false;
            captureStarting();
            startDelay.restart();
        } else {
            awaitingState = true;
            refresh();
        }
    }
    function loadOptions() {
        if (!opened) return;
        if (!optionToken) optionToken = DesktopData.observe("capture.options", menu);
        else DesktopData.refresh("capture.options");
    }
    function saveOption(key, enabled) {
        if (busy) return;
        captureOptions = ObsQueue.withOption(captureOptions, key, enabled);
        pendingOptionChanges = ObsQueue.enqueue(pendingOptionChanges, key, enabled);
        writeNextOption();
    }
    function writeNextOption() {
        if (optionWriting || ObsStatus.busy) return;
        const next = ObsQueue.takeNext(pendingOptionChanges);
        if (!next) return;
        pendingOptionChanges = next.remaining;
        optionWriting = true;
        const id = DesktopData.client.actCapture("set-option", {key: next.key, enabled: next.enabled}, function(code, message) {
            menu.optionWriting = false;
            menu.optionId = "";
            if (code) {
                menu.actionError = code === "outcome-unknown" ? Eitr.I18n.tr("Outcome unknown; refresh before retrying.") : (message || Eitr.I18n.tr("Could not save recording settings"));
                menu.status = menu.actionError;
                menu.pendingOptionChanges = ({});
                menu.pendingAction = "";
                menu.preparingStart = false;
                menu.loadOptions();
            }
        });
        if (id) optionId = id;
        else {
            optionWriting = false;
            pendingOptionChanges = ({});
            actionError = Eitr.I18n.tr("Could not save recording settings");
        }
    }
    onOpenedChanged: {
        if (opened) { refresh(); loadOptions(); }
        else if (optionToken) { DesktopData.release(optionToken); optionToken = ""; }
    }
    Component.onCompleted: obsState = ObsStatus.state
    Component.onDestruction: {
        DesktopData.releaseOwner(menu);
        DesktopData.client.detachAction(actionId);
        DesktopData.client.detachAction(optionId);
    }
    Connections {
        target: ObsStatus
        function onBusyChanged() {
            if (!ObsStatus.busy && !menu.optionWriting) {
                if (Object.keys(menu.pendingOptionChanges).length) menu.writeNextOption();
                else if (menu.pendingAction !== "" && !menu.awaitingState && !startDelay.running)
                    menu.beginAction();
            }
        }
    }
    Timer {
        id: startDelay
        interval: menu.transitionDuration + 50
        onTriggered: {
            menu.beginAction();
        }
    }
    Connections {
        target: ObsStatus
        function onReceived(snapshot) {
            menu.updateContent(function() {
                if (menu.pendingAction !== "" && !menu.awaitingState) return;
                menu.applySnapshot("obsState", snapshot);
                menu.status = menu.actionError || menu.optionsError || snapshot.error || (!snapshot.ready ? Eitr.I18n.tr("OBS status unavailable") : "");
                menu.pendingAction = "";
                menu.awaitingState = false;
            });
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
