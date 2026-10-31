import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../PanelStyle.js" as PanelStyle
import "../JsonState.js" as JsonState

ThemedPopup {
    id: center
    waitForFreshData: true
    escapeHandler: () => center.page === "plugins" ? pluginManager.back() : plugins.back()
    required property var service
    required property var wifiControl
    required property var bluetoothControl
    required property var displayControl
    required property var keyboardControl
    property string wifiGlyph: "󰤨"
    required property var battery
    required property var mediaPlayer
    required property bool idleEnabled
    required property bool idleBusy
    property bool chatOpen: false
    property var chatAssistant: ({})
    property string page: "general"
    property string barPosition: "top"
    property string appearance: "solid"
    property string layout: "unified"
    property string barScreens: "main"
    property bool barAutoHide: false
    property bool barDock: true
    property string mediaStyle: "bars"
    property string clockFormat: "12h"
    property string workspaceStyle: "Runes"
    property var airplane: PowerService.radios
    property var powerTokens: []
    property string powerActionId: ""
    Connections {
        target: PowerService
        function onRadiosChanged() { center.updateContent(function() { center.airplane = PowerService.radios; }); }
    }
    property bool crashNotifications: true
    readonly property string crashHelpScript: Eitr.Paths.code("walker/scripts/actions/system/crash-help.py")
    property bool gameMode: false
    readonly property string gameModeScript: Eitr.Paths.code("walker/scripts/actions/toggle/game-mode.sh")
    property var styleErrors: ({})
    function styleResult(key, text, code, fields) {
        const result = JsonState.parse(text, code, fields);
        let errors = Object.assign({}, styleErrors);
        if (result.ok) delete errors[key];
        else errors[key] = result.error;
        styleErrors = errors;
        return result.data;
    }
    readonly property var crashOperationRef: crashOperation
    readonly property var gameModeOperationRef: gameModeOperation
    readonly property var cursorWriteRef: cursorWrite
    readonly property var lockscreenWriteRef: lockscreenWrite
    readonly property var fireWriteRef: fireWrite
    readonly property var terminalWriteRef: terminalWrite
    property string actionError: ""
    property var pendingCommand: []
    // Sections the user folded or unfolded this session (title -> open).
    property var folds: ({})
    property var cursorChoices: ({family: [], size: [], color: []})
    property var lockscreens: []
    property string lockscreen: ""
    property string terminalChoice: "kitty"
    property var terminalChoices: []
    readonly property string terminalScript: Eitr.Paths.code("walker/scripts/actions/style/terminal.py")
    property bool cursorFire: false
    property string updateChannel: ""
    property var organizationPolicy: ({})
    readonly property string cursorScript: Eitr.Paths.code("walker/scripts/actions/style/cursor.py")
    readonly property string lockscreenScript: Eitr.Paths.code("quickshell/lockscreen/scripts/settings.py")
    readonly property string effectsScript: Eitr.Paths.code("walker/scripts/actions/style/terminal-effects.py")
    property var screenMargins: [12, 12, 12, 12]
    readonly property real edgeClearance: barPosition === "top" ? screenMargins[2] : barPosition === "bottom" ? screenMargins[0] : screenMargins[0] + screenMargins[2]
    signal idleToggleRequested()
    signal lockRequested()
    signal settingRequested(string key, string value)
    signal workspaceStyleRequested(string value)
    signal panelRequested(string kind)
    signal pickerRequested(string kind)
    implicitWidth: Math.min(520, hostWindow ? hostWindow.width - ((barPosition === "left" || barPosition === "right") && strip ? strip.width : 0) : 520)
    implicitHeight: hostWindow ? hostWindow.height - (barPosition === "top" || barPosition === "bottom" ? (strip ? strip.height : 30) : 0) - (detached ? 0 : edgeClearance) : 800
    leadingOffset: !detached && (barPosition === "left" || barPosition === "right") ? screenMargins[0] : 0
    barEdge: barPosition
    leftAligned: true
    function refresh() {
        keyboardControl.refresh();
        if (!crashQuery.running && !crashOperation.running) crashQuery.running = true;
        if (!gameModeQuery.running && !gameModeOperation.running) gameModeQuery.running = true;
    }
    property bool powerOpen: false
    readonly property var bluetoothDevices: bluetoothControl.adapter && bluetoothControl.adapter.enabled
        ? bluetoothControl.adapter.devices.values.filter(device => device.connected) : []
    function runAfterClose(command) { pendingCommand = command; opened = false; }
    // The same command as that Walker menu row (scripts/menu-action.py), after closing.
    function menuAction(menu, row) { runAfterClose(["python3", Quickshell.shellDir + "/scripts/menu-action.py", menu, row]); }
    function walkerMenu(name) { runAfterClose([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:" + name]); }
    function setFold(title, open) { let next = Object.assign({}, folds); next[title] = open; folds = next; }
    function loadStyle() {
        if (!cursorQuery.running) cursorQuery.running = true;
        if (!lockscreenQuery.running) lockscreenQuery.running = true;
        if (!terminalQuery.running) terminalQuery.running = true;
        if (!fireQuery.running) fireQuery.running = true;
    }
    function run(process, command) { if (process.running) return; actionError = ""; process.command = command; process.running = true; }
    // Fetch once in the background after the bar starts, so even the first opening
    // shows its data instead of rebuilding lists halfway through the animation.
    Timer { interval: 8000; running: true; onTriggered: { center.refresh(); center.loadStyle(); chatStatus.running = true; } }
    // Queries start once the unfold has finished (DockPanel.revealed): their results
    // rebuild lists, which would otherwise stall the animation midway.
    onRevealed: {
        DisplayService.open(center, 5);
        center.refresh(); chatStatus.running = true;
        if (page === "style") loadStyle();
        if (!organizationQuery.running) organizationQuery.running = true;
        if (page === "settings" && !channelQuery.running) channelQuery.running = true;
    }
    property string networkToken: ""
    property string networkMessage: ""
    property string networkErrorCode: ""
    function networkActionFinished(error, code) { networkErrorCode = code || ""; networkMessage = error; }
    Connections {
        target: center.wifiControl
        function onBusyChanged() { if (center.opened && !center.wifiControl.busy) center.refresh(); }
    }
    Component.onDestruction: { DisplayService.close(center); wifiControl.release(networkToken); wifiControl.detach(center); DesktopData.releaseOwner(center); DesktopData.client.detachAction(powerActionId); }
    onOpenedChanged: {
        if (!opened) DisplayService.close(center);
        PowerService.release(powerTokens);
        powerTokens = opened ? PowerService.observe(center, 5, true) : [];
        if (opened) networkToken = wifiControl.observe(center);
        else {
            wifiControl.release(networkToken); networkToken = "";
            chatOpen = false; chatView.reset();
        }
    }
    onPageChanged: {
        if (page === "style") loadStyle();
        if (page === "settings" && !channelQuery.running) channelQuery.running = true;
    }
    onVisibleChanged: if (!visible) {
        powerOpen = false;
        page = "general";
        pluginManager.reset();
        scroll.contentY = 0;
        if (pendingCommand.length) {
            let command = pendingCommand; pendingCommand = [];
            Quickshell.execDetached(command);
        }
    }
    Timer { interval: 5000; repeat: true; running: center.opened; onTriggered: center.refresh() }
    Process {
        id: crashQuery
        command: ["python3", center.crashHelpScript, "status"]
        stdout: StdioCollector { id: crashOutput }
        onExited: center.crashNotifications = crashOutput.text.trim() === "on"
    }
    Process {
        id: crashOperation
        command: ["python3", center.crashHelpScript, "toggle"]
        onExited: function(code) {
            if (code !== 0) center.actionError = Eitr.I18n.tr("Could not change crash notifications");
            center.refresh();
        }
    }
    Process {
        id: gameModeQuery
        command: ["bash", center.gameModeScript, "status"]
        stdout: StdioCollector { id: gameModeOutput }
        onExited: center.gameMode = gameModeOutput.text.trim() === "on"
    }
    Process {
        id: gameModeOperation
        command: ["bash", center.gameModeScript, "toggle"]
        onExited: function(code) {
            if (code !== 0) center.actionError = Eitr.I18n.tr("Could not change game mode");
            center.refresh();
        }
    }
    Process {
        id: cursorQuery
        command: ["python3", center.cursorScript, "summary"]
        stdout: StdioCollector { id: cursorOutput }
        onExited: function(code) {
            const data = center.styleResult("cursor", cursorOutput.text, code, {choices: {family: [{id: "string", label: "string", selected: "boolean"}], size: [{id: "string", label: "string", selected: "boolean"}], color: [{id: "string", label: "string", selected: "boolean"}]}, current: "object", available: "boolean"});
            center.updateContent(function() {
                const choices = data ? data.choices : {family: [], size: [], color: []};
                if (JsonState.changed(center.cursorChoices, choices)) center.cursorChoices = choices;
            });
        }
    }
    Process { id: cursorWrite; onExited: function(code) { if (code !== 0) center.actionError = Eitr.I18n.tr("Could not change the cursor"); cursorQuery.running = true; } }
    Process {
        id: lockscreenQuery
        command: ["python3", center.lockscreenScript, "summary"]
        stdout: StdioCollector { id: lockscreenOutput }
        onExited: function(code) {
            const data = center.styleResult("lockscreen", lockscreenOutput.text, code, {choices: [{value: "string", label: "string"}], current: "string", available: "boolean"});
            center.updateContent(function() {
                const choices = data ? data.choices : [];
                if (JsonState.changed(center.lockscreens, choices)) center.lockscreens = choices;
                center.lockscreen = data ? data.current : "";
            });
        }
    }
    Process {
        id: lockscreenWrite
        stderr: StdioCollector { id: lockscreenError }
        onExited: function(code) { if (code !== 0) center.actionError = lockscreenError.text.trim() || Eitr.I18n.tr("Could not change the lockscreen"); lockscreenQuery.running = true; }
    }
    Process {
        id: fireQuery
        command: ["python3", center.effectsScript, "summary"]
        stdout: StdioCollector { id: fireOutput }
        onExited: function(code) {
            const data = center.styleResult("effects", fireOutput.text, code, {current: "boolean", choices: "array", available: "boolean"});
            center.cursorFire = data ? data.current : false;
        }
    }
    Process {
        id: terminalQuery
        command: ["python3", center.terminalScript, "summary"]
        stdout: StdioCollector { id: terminalOutput }
        onExited: function(code) {
            const data = center.styleResult("terminal", terminalOutput.text, code, {current: "string", choices: [{value: "string", label: "string"}], available: "boolean"});
            center.updateContent(function() {
                const choices = data ? data.choices : [];
                if (JsonState.changed(center.terminalChoices, choices)) center.terminalChoices = choices;
                center.terminalChoice = data ? data.current : "";
            });
        }
    }
    Process {
        id: terminalWrite
        stderr: StdioCollector { id: terminalError }
        onExited: function(code) {
            if (code !== 0) center.actionError = terminalError.text.trim();
            terminalQuery.running = true;
        }
    }
    Process { id: fireWrite; onExited: function(code) { if (code !== 0) center.actionError = Eitr.I18n.tr("Could not change Cursor Fire"); fireQuery.running = true; } }
    Process {
        id: organizationQuery
        running: true
        command: ["python3", (Quickshell.env("EITR_LIBRARY_ROOT") || "/usr/share/eitr/lib") + "/eitr_policy.py", "status"]
        stdout: StdioCollector { id: organizationOutput }
        onExited: {
            const received = organizationOutput.text;
            center.updateContent(function() {
                try {
                    let policy = JSON.parse(received);
                    if (JsonState.changed(center.organizationPolicy, policy)) center.organizationPolicy = policy;
                    if (center.organizationPolicy.development === false || center.organizationPolicy.assistants_together === false) {
                        center.chatOpen = false; chatView.reset();
                    }
                }
                catch (error) { if (JsonState.changed(center.organizationPolicy, {})) center.organizationPolicy = ({}); }

            });
        }
    }
    Process {
        id: channelQuery
        command: ["/usr/lib/eitr/eitr-system", "channel-status"]
        stdout: StdioCollector { id: channelOutput }
        onExited: center.updateChannel = channelOutput.text.trim()
    }
    Process {
        id: chatStatus
        command: ["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/assistant-chat.py"), "status"]
        stdout: StdioCollector { id: chatStatusOutput }
        onExited: {
            const received = chatStatusOutput.text;
            center.updateContent(function() {
                let assistant;
                try { assistant = JSON.parse(received); }
                catch (error) { assistant = ({}); }
                if (JsonState.changed(center.chatAssistant, assistant)) center.chatAssistant = assistant;
                if (!center.chatAssistant.identifier) { center.chatOpen = false; chatView.reset(); }

            });
        }
    }
    RowLayout {
        anchors.fill: parent; anchors.margins: 0
        anchors.topMargin: 0; anchors.bottomMargin: 0
        spacing: 12
        ControlCenterNavigation {
            centerRef: center
            onPageSelected: function(page) { center.chatOpen = false; chatView.reset(); center.page = page; }
            onChatRequested: { center.chatOpen = true; chatView.focusInput(); }
        }
        Rectangle { Layout.fillHeight: true; Layout.preferredWidth: 1; color: Qt.alpha(center.foreground, PanelStyle.dividerAlpha) }
        Item {
            Layout.fillWidth: true; Layout.fillHeight: true
            AssistantChat {
                id: chatView
                anchors.fill: parent; visible: center.chatOpen
                foreground: center.foreground; background: center.background
                assistant: center.chatAssistant
                onClosed: { center.chatOpen = false; center.keyTarget.forceActiveFocus(); }
            }
            Flickable {
                visible: !center.chatOpen
                id: scroll
                anchors.fill: parent
                contentHeight: content.implicitHeight; clip: true
                boundsBehavior: Flickable.StopAtBounds
                Column {
                    id: content
                    width: scroll.width; spacing: 12
                    PanelHeading {
                        text: ({plugins: Eitr.I18n.tr("Plugins"), general: Eitr.I18n.tr("General"), style: Eitr.I18n.tr("Style"), tools: Eitr.I18n.tr("Tools"), settings: Eitr.I18n.tr("Settings")})[center.page]
                        rune: center.page
                        foreground: center.foreground; accent: center.accent
                    }
                    Text { visible: center.actionError !== ""; width: parent.width; wrapMode: Text.WordWrap; text: center.actionError; color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                    ControlCenterConnectivity { centerRef: center }
                    ControlCenterSliders { centerRef: center }
                    PluginArea {
                        id: plugins
                        width: parent.width
                        visible: center.page === "general" && tiles.length > 0
                        active: center.opened && center.page === "general"
                        foreground: center.foreground; background: center.background; accent: center.accent
                    }
                    PluginManager {
                        id: pluginManager
                        width: parent.width; visible: center.page === "plugins"
                        foreground: center.foreground; background: center.background; accent: center.accent
                    }
                    ControlCenterStyle { centerRef: center }
                    ControlCenterSettings { centerRef: center }
                    ControlCenterTools { centerRef: center }
                    ControlCenterPower { centerRef: center }
                }
            }
        }
    }
}
