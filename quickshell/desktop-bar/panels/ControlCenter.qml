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
    keyTarget: content
    escapeHandler: () => {
        return center.page === "plugins" ? pluginManager.back() : plugins.back();
    }
    required property var service
    required property var wifiControl
    required property var bluetoothControl
    required property var displayControl
    property string wifiGlyph: "󰤨"
    required property var battery
    required property var mediaPlayer
    required property bool idleEnabled
    required property bool idleBusy
    property bool chatOpen: false
    property var chatAssistant: ({})
    property string accountToken: ""
    readonly property var accountPicture: DesktopData.topics["account.picture"] ? DesktopData.topics["account.picture"].data : ({})
    property string page: "general"
    property string barPosition: "top"
    property var airplane: PowerService.radios
    property var powerTokens: []
    property string powerActionId: ""
    Connections {
        target: PowerService
        function onRadiosChanged() { center.updateContent(function() { center.airplane = PowerService.radios; }); }
    }
    property bool gameMode: false
    readonly property string gameModeScript: Eitr.Paths.code("walker/scripts/actions/toggle/game-mode.sh")
    readonly property var gameModeOperationRef: gameModeOperation
    property string actionError: ""
    property var pendingCommand: []
    // Sections the user folded or unfolded this session (title -> open).
    property var folds: ({})
    property var screenMargins: [12, 12, 12, 12]
    readonly property real edgeClearance: barPosition === "top" ? screenMargins[2] : barPosition === "bottom" ? screenMargins[0] : 0
    signal idleToggleRequested()
    signal lockRequested()
    signal panelRequested(string kind)
    // Opens the Settings window at a page ("" for its overview).
    signal settingsRequested(string page)
    implicitWidth: Math.min(520, hostWindow ? hostWindow.width - ((barPosition === "left" || barPosition === "right") && strip ? strip.width : 0) : 520)
    implicitHeight: hostWindow ? hostWindow.height - (barPosition === "top" || barPosition === "bottom" ? (strip ? strip.height : 30) : 0) - (detached ? 0 : edgeClearance) : 800
    barEdge: barPosition
    leftAligned: true
    function refresh() {
        if (!gameModeQuery.running && !gameModeOperation.running) gameModeQuery.running = true;
    }
    property bool powerOpen: false
    readonly property var bluetoothDevices: bluetoothControl.adapter && bluetoothControl.adapter.enabled
        ? bluetoothControl.adapter.devices.values.filter(device => device.connected) : []
    function runAfterClose(command) { pendingCommand = command; opened = false; }
    // The same command as that Walker menu row (scripts/menu-action.py), after closing.
    function menuAction(menu, row) { runAfterClose(["python3", Quickshell.shellDir + "/scripts/menu-action.py", menu, row]); }
    function setFold(title, open) { let next = Object.assign({}, folds); next[title] = open; folds = next; }
    readonly property string timerFold: Eitr.I18n.tr("Timer & Focus")
    property var organizationPolicy: ({})
    function openSettings(page) { opened = false; settingsRequested(page); }
    // Fetch once in the background after the bar starts, so even the first opening
    // shows its data instead of rebuilding lists halfway through the animation.
    Timer { interval: 8000; running: true; onTriggered: { center.refresh(); chatStatus.running = true; } }
    // Queries start once the unfold has finished (DockPanel.revealed): their results
    // rebuild lists, which would otherwise stall the animation midway.
    onRevealed: {
        DisplayService.open(center, 5);
        center.refresh(); chatStatus.running = true;
        if (!organizationQuery.running) organizationQuery.running = true;
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
        if (accountToken) DesktopData.release(accountToken);
        accountToken = opened ? DesktopData.observe("account.picture", center) : "";
        if (!opened) DisplayService.close(center);
        PowerService.release(powerTokens);
        powerTokens = opened ? PowerService.observe(center, 5, true) : [];
        if (opened) networkToken = wifiControl.observe(center);
        else {
            wifiControl.release(networkToken); networkToken = "";
            chatOpen = false; chatView.reset();
        }
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
            onSettingsRequested: center.openSettings("")
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
                        text: ({plugins: Eitr.I18n.tr("Plugins"), general: Eitr.I18n.tr("General"), tools: Eitr.I18n.tr("Tools")})[center.page]
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
                    ControlCenterTools { centerRef: center }
                    ControlCenterPower { centerRef: center }
                }
            }
        }
    }
}
