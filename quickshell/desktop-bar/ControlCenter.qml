pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts
import QtQuick.Effects
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import Quickshell.Services.Pipewire
import "PanelStyle.js" as PanelStyle
import "JsonState.js" as JsonState

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
    property string actionError: ""
    property var pendingCommand: []
    // Sections the user folded or unfolded this session (title -> open).
    property var folds: ({})
    property var cursorChoices: ({family: [], size: [], color: []})
    property var lockscreens: []
    property string lockscreen: ""
    property string terminalChoice: "kitty"
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
        keyboardControl.refresh(); displayControl.refresh(); displayControl.refreshNightlight(); displayControl.refreshDisplays();
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
    Component.onDestruction: { wifiControl.release(networkToken); wifiControl.detach(center); DesktopData.releaseOwner(center); DesktopData.client.detachAction(powerActionId); }
    onOpenedChanged: {
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
        command: ["sh", "-c", 'for group in family size color; do python3 "$1" entries "$group"; done', "sh", center.cursorScript]
        stdout: StdioCollector { id: cursorOutput }
        onExited: {
            const received = cursorOutput.text;
            center.updateContent(function() {
                try {
                    let lines = received.trim().split("\n");
                    let choices = {family: JSON.parse(lines[0]), size: JSON.parse(lines[1]), color: JSON.parse(lines[2])};
                    if (JsonState.changed(center.cursorChoices, choices)) center.cursorChoices = choices;
                } catch (error) {}

            });
        }
    }
    Process { id: cursorWrite; onExited: function(code) { if (code !== 0) center.actionError = Eitr.I18n.tr("Could not change the cursor"); cursorQuery.running = true; } }
    Process {
        id: lockscreenQuery
        command: ["sh", "-c", 'python3 "$1" list; echo "@current"; python3 "$1" current', "sh", center.lockscreenScript]
        stdout: StdioCollector { id: lockscreenOutput }
        onExited: {
            const received = lockscreenOutput.text;
            center.updateContent(function() {
                let parts = received.split("@current");
                let lockscreens = parts[0].trim().split("\n").filter(line => line.includes("\t"))
                    .map(line => ({value: line.split("\t")[0], label: line.split("\t")[1]}));
                if (JsonState.changed(center.lockscreens, lockscreens)) center.lockscreens = lockscreens;
                center.lockscreen = (parts[1] || "").trim();

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
        command: ["python3", center.effectsScript, "get", "cursor-fire"]
        stdout: StdioCollector { id: fireOutput }
        onExited: center.cursorFire = fireOutput.text.trim() === "on"
    }
    Process {
        id: terminalQuery
        command: ["python3", center.terminalScript, "get", "terminal"]
        stdout: StdioCollector { id: terminalOutput }
        onExited: center.terminalChoice = terminalOutput.text.trim()
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
        Column {
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: 34
            spacing: 10
            Repeater {
                model: [{key: "general", icon: "󰕮", name: "General"},
                    {key: "plugins", icon: "󰏖", name: "Plugins"},
                    {key: "style", icon: "󰏘", name: "Style"},
                    {key: "tools", icon: "󱁤", name: "Tools"}, {key: "settings", icon: "󰒓", name: "Settings"}]
                PanelButton {
                    textSize: 12; iconSize: 20
                    id: tab
                    required property var modelData
                    width: 34; height: 34; icon: true; text: modelData.key === "general" ? "" : modelData.icon
                    Image {
                        anchors.centerIn: parent; width: 22; height: 22
                        visible: tab.modelData.key === "general"
                        source: Quickshell.shellDir + "/assets/eitr-logo-white.svg"
                        fillMode: Image.PreserveAspectFit
                        // Drawn at its shown size: scaling the large SVG down afterwards leaves jagged edges.
                        sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio), Math.ceil(height * Screen.devicePixelRatio))
                        smooth: true
                        layer.enabled: true
                        layer.effect: MultiEffect { colorization: 1; colorizationColor: center.foreground }
                    }
                    foreground: center.foreground; selected: center.page === modelData.key && !center.chatOpen
                    onClicked: { center.chatOpen = false; chatView.reset(); center.page = modelData.key; }
                    HoverHandler { id: tabHover }
                    BarTooltip { target: tab; hovered: tabHover.hovered; text: Eitr.I18n.tr(tab.modelData.name); foreground: center.foreground; background: center.background }
                }
            }
            PanelButton {
                id: chatButton
                visible: !!center.chatAssistant.identifier && center.organizationPolicy.development !== false && center.organizationPolicy.assistants_together !== false
                width: 34; height: 34; icon: true; text: "󰭻"
                foreground: center.foreground; selected: center.chatOpen
                onClicked: { center.chatOpen = true; chatView.focusInput(); }
                HoverHandler { id: chatHover }
                BarTooltip { target: chatButton; hovered: chatHover.hovered; text: Eitr.I18n.tr("Chat with %1", [center.chatAssistant.name || ""]); foreground: center.foreground; background: center.background }
            }
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
                    Column {
                        visible: center.page === "general"
                        width: parent.width; spacing: 12
                        Section { text: Eitr.I18n.tr("Connectivity"); width: parent.width }
                        GridLayout {
                            width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
                            ToggleTile {
                                title: Eitr.I18n.tr("WiFi"); glyph: center.wifiGlyph
                                detail: center.wifiControl.connected ? center.wifiControl.connected.name : ""
                                selected: !!center.wifiControl.device && center.wifiControl.device.powered
                                available: !!center.wifiControl.device && !center.wifiControl.busy && !center.airplane.enabled
                                onClicked: center.wifiControl.act(center, "power", center.wifiControl.device.path, center.wifiControl.device.powered ? "false" : "true")
                            }
                            ToggleTile {
                                title: Eitr.I18n.tr("Bluetooth"); glyph: "󰂯"
                                detail: center.bluetoothDevices.length === 1 ? center.bluetoothDevices[0].name
                                    : center.bluetoothDevices.length > 1 ? Eitr.I18n.tr("{count} devices", {count: center.bluetoothDevices.length}) : ""
                                selected: !!center.bluetoothControl.adapter && center.bluetoothControl.adapter.enabled
                                available: !!center.bluetoothControl.adapter && !center.airplane.enabled
                                onClicked: center.bluetoothControl.adapter.enabled = !center.bluetoothControl.adapter.enabled
                            }
                            ToggleTile {
                                title: Eitr.I18n.tr("Airplane"); glyph: "󰀝"; selected: !!center.airplane.enabled
                                available: !!center.airplane.available && !PowerService.busy
                                onClicked: { center.powerActionId = PowerService.act("airplane", center.airplane.enabled ? "false" : "true", function(code, message) { center.networkActionFinished(message || (code ? "Could not complete request" : ""), code); }); if (!center.powerActionId) center.networkActionFinished("Could not complete request", "broker-unavailable"); }
                            }
                        }
                        Text { visible: (center.networkMessage || center.wifiControl.details.error || "") !== ""; width: parent.width; wrapMode: Text.WordWrap; text: center.networkMessage ? center.wifiControl.actionMessage(center.networkMessage) : (center.wifiControl.details.error || ""); color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Section { text: Eitr.I18n.tr("Quick Actions"); width: parent.width }
                        GridLayout {
                            width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
                            ToggleTile { title: Eitr.I18n.tr("Idle Lock"); tooltip: Eitr.I18n.tr("Lock the screen automatically when you're away."); glyph: "󱫖"; selected: center.idleEnabled; available: !center.idleBusy; onClicked: center.idleToggleRequested() }
                            ToggleTile { title: Eitr.I18n.tr("Crash Notifications"); tooltip: Eitr.I18n.tr("Show help notifications when a program crashes."); glyph: "󰅚"; selected: center.crashNotifications; available: !crashOperation.running; onClicked: { center.actionError = ""; crashOperation.running = true; } }
                            ToggleTile { title: Eitr.I18n.tr("Do Not Disturb"); tooltip: Eitr.I18n.tr("Silence popups while keeping notification history."); glyph: "󰂛"; selected: center.service.doNotDisturb; onClicked: center.service.toggleDnd() }
                            ToggleTile {
                                visible: center.organizationPolicy.gaming === true
                                title: Eitr.I18n.tr("Game Mode"); tooltip: Eitr.I18n.tr("Disable effects and popups; use the performance profile."); glyph: "󰊴"; selected: center.gameMode
                                available: !gameModeOperation.running
                                onClicked: { center.actionError = ""; gameModeOperation.running = true; }
                            }
                            ToggleTile {
                                title: Eitr.I18n.tr("Night Light"); tooltip: Eitr.I18n.tr("Use warmer screen colors."); glyph: "󰖔"
                                detail: center.displayControl.nightlight.mode === "auto" ? Eitr.I18n.tr("Scheduled") : ""
                                selected: center.displayControl.nightlight.mode === "on" || !!center.displayControl.nightlight.active
                                available: !!center.displayControl.nightlight.available
                                onClicked: center.displayControl.setNightlight(center.displayControl.nightlight.mode === "on" ? "off" : "on")
                            }
                        }
                        GridLayout {
                            width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
                            GridAction { title: Eitr.I18n.tr("Hide Bar"); tooltip: Eitr.I18n.tr("Hide the bar; press SUPER + Shift + Space to restore it."); glyph: "󰍜"; onClicked: center.menuAction("toggle", "Desktop Bar") }
                            GridAction { title: Eitr.I18n.tr("Start Screensaver"); tooltip: Eitr.I18n.tr("Start the screensaver now."); glyph: "󱄄"; onClicked: center.menuAction("toggle", "Start Screensaver") }
                        }
                    }
                    Column {
                        visible: center.page === "general"
                        width: parent.width; spacing: 12
                        Section { text: Eitr.I18n.tr("Sound"); width: parent.width }
                        AudioLevelControl { width: parent.width; node: Pipewire.defaultAudioSink; showName: false; textSize: 12; iconSize: 16; foreground: center.foreground; background: center.background; accent: center.accent }
                        AudioLevelControl { width: parent.width; node: Pipewire.defaultAudioSource; microphone: true; showName: false; textSize: 12; iconSize: 16; foreground: center.foreground; background: center.background; accent: center.accent }
                        Section { visible: center.displayControl.state.kind === "backlight"; text: Eitr.I18n.tr("Display"); width: parent.width }
                        Row {
                            visible: center.displayControl.state.kind === "backlight"
                            width: parent.width; spacing: 10
                            Text { width: 30; height: 30; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; text: "󰃟"; color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: 16 }
                            PanelSlider {
                                id: brightnessSlider
                                width: parent.width - 100; from: 1; to: 100
                                foreground: center.foreground; accent: center.accent
                                enabled: !!center.displayControl.state.available
                                Binding { target: brightnessSlider; property: "value"; value: center.displayControl.state.value; when: !brightnessSlider.pressed }
                                onMoved: brightnessSettle.restart()
                                Timer { id: brightnessSettle; interval: 120; onTriggered: center.displayControl.applyValue(Math.round(brightnessSlider.value)) }
                            }
                            Text { width: 50; height: 30; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignRight; text: center.displayControl.state.available ? center.displayControl.state.value + "%" : "--"; color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize; font.features: PanelStyle.tabularFigures }
                        }
                        Section { visible: !!center.mediaPlayer; text: Eitr.I18n.tr("Media"); width: parent.width }
                        MediaCard { compact: true; visible: !!center.mediaPlayer; width: parent.width; player: center.mediaPlayer; active: center.opened && center.page === "general"; foreground: center.foreground; accent: center.accent }
                    }
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
                    Column {
                        visible: center.page === "style"; width: parent.width; spacing: 12
                        Fold {
                        title: Eitr.I18n.tr("Theme & Wallpaper"); startOpen: true
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("Theme"); glyph: "󰏘"; onClicked: center.pickerRequested("theme") }
                            GridAction { title: Eitr.I18n.tr("Wallpaper"); glyph: "󰸉"; onClicked: center.pickerRequested("wallpaper") }
                            GridAction { title: Eitr.I18n.tr("Fonts"); glyph: "󰛖"; onClicked: center.walkerMenu("fonts") }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Focus")
                        RowLayout {
                            width: parent.width
                            Text { Layout.fillWidth: true; text: Eitr.I18n.tr("Distraction-free tabbed desktop"); color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; wrapMode: Text.WordWrap }
                            PanelSwitch { checked: FocusMode.enabled; foreground: center.foreground; accent: center.accent; onClicked: FocusMode.select(checked) }
                        }
                        Text { width: parent.width; visible: FocusMode.error !== ""; text: FocusMode.error; color: center.foreground; wrapMode: Text.Wrap; font.pixelSize: PanelStyle.captionSize }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Corners")
                        Row {
                            width: parent.width; spacing: 8
                            Repeater {
                                model: DesktopStyle.options
                                PanelButton {
                                    required property var modelData
                                    width: (parent.width - 16) / 3
                                    text: Eitr.I18n.tr(modelData.label); textSize: 12
                                    foreground: center.foreground
                                    selected: DesktopStyle.corners === modelData.key
                                    onClicked: DesktopStyle.select(modelData.key)
                                }
                            }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Bar")
                        OptionHeading { text: Eitr.I18n.tr("Layout") }
                        Grid { width: parent.width; columns: 2; spacing: 8
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Full"); selected: center.layout === "unified"; foreground: center.foreground; onClicked: center.settingRequested("layout", "unified") }
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Centered"); selected: center.layout === "centered"; foreground: center.foreground; onClicked: center.settingRequested("layout", "centered") }
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Tabs"); selected: center.layout === "notch"; foreground: center.foreground; onClicked: center.settingRequested("layout", "notch") }
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Islands"); selected: center.layout === "islands"; foreground: center.foreground; onClicked: center.settingRequested("layout", "islands") }
                        }
                        OptionHeading { text: Eitr.I18n.tr("Position") }
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            Repeater { model: ["top", "bottom", "left", "right"]
                                PanelButton { textSize: 12; iconSize: 16; required property string modelData; Layout.fillWidth: true; text: modelData.charAt(0).toUpperCase() + modelData.slice(1); foreground: center.foreground; selected: center.barPosition === modelData; onClicked: center.settingRequested("edge", modelData) }
                            }
                        }
                        OptionHeading { text: Eitr.I18n.tr("Appearance") }
                        Row { width: parent.width; spacing: 8
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Blur"); selected: center.appearance === "transparent"; foreground: center.foreground; onClicked: center.settingRequested("appearance", "transparent") }
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Theme Color"); selected: center.appearance === "solid"; foreground: center.foreground; onClicked: center.settingRequested("appearance", "solid") }
                        }
                        OptionHeading { text: Eitr.I18n.tr("Show on") }
                        Row { width: parent.width; spacing: 8
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Main Display"); selected: center.barScreens === "main"; foreground: center.foreground; onClicked: center.settingRequested("screens", "main") }
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("All Displays"); selected: center.barScreens === "all"; foreground: center.foreground; onClicked: center.settingRequested("screens", "all") }
                        }
                        OptionHeading { text: Eitr.I18n.tr("Clock") }
                        Row { width: parent.width; spacing: 8
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("12-hour"); selected: center.clockFormat === "12h"; foreground: center.foreground; onClicked: center.settingRequested("clock", "12h") }
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("24-hour"); selected: center.clockFormat === "24h"; foreground: center.foreground; onClicked: center.settingRequested("clock", "24h") }
                        }
                        OptionHeading { text: Eitr.I18n.tr("Media style") }
                        Row { width: parent.width; spacing: 8
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Bars"); selected: center.mediaStyle === "bars"; foreground: center.foreground; onClicked: center.settingRequested("mediaStyle", "bars") }
                            PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Line"); selected: center.mediaStyle === "line"; foreground: center.foreground; onClicked: center.settingRequested("mediaStyle", "line") }
                        }
                        OptionHeading { text: Eitr.I18n.tr("Behavior") }
                        Row {
                            width: parent.width; spacing: PanelStyle.selectionActionGap
                            Text {
                                width: parent.width - autoHideSwitch.width - parent.spacing; height: 32
                                verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Auto-hide")
                                color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                            }
                            PanelSwitch {
                                id: autoHideSwitch
                                anchors.verticalCenter: parent.verticalCenter
                                checked: center.barAutoHide; foreground: center.foreground; accent: center.accent
                                Accessible.name: Eitr.I18n.tr("Auto-hide")
                                onClicked: center.settingRequested("autohide", checked ? "yes" : "no")
                            }
                        }
                        Row {
                            width: parent.width; spacing: PanelStyle.selectionActionGap
                            Text {
                                width: parent.width - dockSwitch.width - parent.spacing; height: 32
                                verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Dock")
                                color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                            }
                            PanelSwitch {
                                id: dockSwitch
                                anchors.verticalCenter: parent.verticalCenter
                                checked: center.barDock; foreground: center.foreground; accent: center.accent
                                Accessible.name: Eitr.I18n.tr("Dock")
                                onClicked: center.settingRequested("dock", checked ? "yes" : "no")
                            }
                        }
                        Row {
                            width: parent.width; spacing: PanelStyle.selectionActionGap
                            Text {
                                width: parent.width - reduceMotionSwitch.width - parent.spacing; height: 32
                                verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Reduce motion")
                                color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                            }
                            PanelSwitch {
                                id: reduceMotionSwitch
                                anchors.verticalCenter: parent.verticalCenter
                                checked: DesktopStyle.reduceMotion; foreground: center.foreground; accent: center.accent
                                Accessible.name: Eitr.I18n.tr("Reduce motion")
                                onClicked: center.settingRequested("reduceMotion", checked ? "yes" : "no")
                            }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Workspaces")
                        Column { width: parent.width; spacing: 6
                            Repeater { model: ["Dots", "Glyph", "Numbers", "Runes"]
                                PanelButton {
                                    textSize: 12; iconSize: 16
                                    id: workspaceChoice
                                    required property string modelData
                                    width: parent.width; text: modelData; textAlignment: Text.AlignLeft
                                    foreground: center.foreground; selected: center.workspaceStyle === modelData
                                    onClicked: center.workspaceStyleRequested(modelData)
                                    Row {
                                        anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                                        Repeater { model: 5
                                            WorkspaceMarker { required property int index; style: workspaceChoice.modelData; label: String(index + 1); active: index === 1; foreground: center.foreground; accent: center.accent; selectedForeground: center.background }
                                        }
                                    }
                                }
                            }
                        }
                        }
                        Fold {
                            title: Eitr.I18n.tr("Lockscreen")
                            Column { width: parent.width; spacing: 6
                                Repeater { model: center.lockscreens
                                    PanelButton {
                                        required property var modelData
                                        width: parent.width; textSize: 12; text: Eitr.I18n.tr(modelData.label); textAlignment: Text.AlignLeft
                                        leadingIcon: modelData.value === center.lockscreen ? "\u{F00C}" : ""
                                        foreground: center.foreground; selected: modelData.value === center.lockscreen
                                        available: !lockscreenWrite.running
                                        onClicked: if (!selected) center.run(lockscreenWrite, ["python3", center.lockscreenScript, "select", modelData.value])
                                    }
                                }
                            }
                        }
                        Fold {
                            title: Eitr.I18n.tr("Cursor")
                            Repeater {
                                model: [{key: "family", label: Eitr.I18n.tr("Family")}, {key: "size", label: Eitr.I18n.tr("Size")}, {key: "color", label: Eitr.I18n.tr("Color")}]
                                Column {
                                    id: cursorGroup
                                    required property var modelData
                                    width: parent.width; spacing: 6
                                    OptionHeading { text: cursorGroup.modelData.label }
                                    Flow { width: parent.width; spacing: 6
                                        Repeater { model: center.cursorChoices[cursorGroup.modelData.key] || []
                                            PanelButton {
                                                required property var modelData
                                                width: cursorGroup.modelData.key === "family" ? (parent.width - 6) / 2 : (parent.width - 18) / 4
                                                textSize: 12; text: modelData.label.replace(" (Default)", "")
                                                foreground: center.foreground; selected: modelData.selected
                                                available: !cursorWrite.running
                                                onClicked: if (!selected) center.run(cursorWrite, ["python3", center.cursorScript, "set", cursorGroup.modelData.key, modelData.id])
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Terminal")
                        Column { width: parent.width; spacing: 6
                        Flow { width: parent.width; spacing: 6
                            Repeater { model: ["kitty", "ghostty"]
                                PanelButton {
                                    required property string modelData
                                    width: (parent.width - 6) / 2
                                    text: modelData === "kitty" ? "Kitty" : "Ghostty"
                                    foreground: center.foreground; selected: center.terminalChoice === modelData
                                    leadingIcon: selected ? "\u{F00C}" : ""
                                    available: !terminalWrite.running
                                    onClicked: if (!selected) center.run(terminalWrite, ["python3", center.terminalScript, "set", "terminal", modelData])
                                }
                            }
                        }
                        Item { width: parent.width; height: Math.max(32, terminalLabel.implicitHeight)
                            Label { id: terminalLabel; width: parent.width - 60; anchors.verticalCenter: parent.verticalCenter; wrapMode: Text.WordWrap; text: Eitr.I18n.tr("Cursor Fire: a blazing trail behind Kitty's cursor") }
                            PanelSwitch {
                                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                                checked: center.cursorFire; enabled: !fireWrite.running
                                foreground: center.foreground; accent: center.accent
                                onToggled: center.run(fireWrite, ["python3", center.effectsScript, "set", "cursor-fire", checked ? "on" : "off"])
                            }
                        }
                        }
                        }
                    }
                    Column {
                        visible: center.page === "settings"; width: parent.width; spacing: 12
                        Section { text: Eitr.I18n.tr("Language"); width: parent.width }
                        PanelButton {
                            width: parent.width; textAlignment: Text.AlignLeft
                            text: Eitr.I18n.tr("Language · %1", [Eitr.I18n.languageName])
                            foreground: center.foreground
                            onClicked: center.runAfterClose(["eitr-run", "walker/bin/walker", "--provider", "menus:language"])
                        }
                        Label {
                            width: parent.width; wrapMode: Text.WordWrap
                            text: Eitr.I18n.tr("Follows the system locale (LC_MESSAGES / LANG). Sign out and back in after changing it.")
                        }
                        Fold {
                        title: Eitr.I18n.tr("Devices")
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("Audio"); glyph: "󰕾"; onClicked: center.panelRequested("volume") }
                            GridAction { title: Eitr.I18n.tr("Microphone"); glyph: "󰍬"; onClicked: center.panelRequested("mic") }
                            GridAction { title: Eitr.I18n.tr("Display"); glyph: "󰍹"; onClicked: center.panelRequested("display") }
                            GridAction { title: Eitr.I18n.tr("Bluetooth"); glyph: "󰂯"; onClicked: center.panelRequested("bluetooth") }
                            GridAction { title: Eitr.I18n.tr("WiFi"); glyph: "󰤨"; onClicked: center.panelRequested("wifi") }
                            GridAction { title: Eitr.I18n.tr("Lighting"); glyph: "󰛨"; onClicked: center.walkerMenu("lighting") }
                            GridAction { visible: center.battery.available; title: Eitr.I18n.tr("Battery Limit"); glyph: "󰂄"; onClicked: center.walkerMenu("battery-limit") }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Keyboard")
                        Column {
                        width: parent.width; spacing: PanelStyle.selectionRowGap
                        Repeater {
                            model: center.keyboardControl.layouts
                            KeyboardLayoutRow {
                                required property var modelData
                                width: parent.width; label: modelData.label
                                foreground: center.foreground; tooltipBackground: center.background
                                selected: modelData.index === center.keyboardControl.activeLayout
                                showRemove: false
                                onActivated: center.keyboardControl.perform(["select", String(modelData.index)])
                            }
                        }
                        }
                        // Adding and removing layouts happens in Walker's Keyboard menu.
                        PanelFooterLink { text: Eitr.I18n.tr("Add or Remove Layouts…"); foreground: center.foreground; onClicked: center.walkerMenu("keyboard") }
                        Label { visible: center.keyboardControl.error !== ""; width: parent.width; wrapMode: Text.WordWrap; text: center.keyboardControl.error }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Night Light & Main Display")
                        Row { width: parent.width; spacing: 8
                            Repeater { model: ["off", "on", "auto"]
                                PanelButton { textSize: 12; iconSize: 16; required property string modelData; width: (parent.width - 16) / 3; text: modelData.charAt(0).toUpperCase() + modelData.slice(1); foreground: center.foreground; selected: center.displayControl.nightlight.mode === modelData; available: !!center.displayControl.nightlight.available; onClicked: center.displayControl.setNightlight(modelData) }
                            }
                        }
                        OptionHeading { text: Eitr.I18n.tr("Night Light schedule") }
                        Row { width: parent.width; spacing: 8
                            TextField {
                                id: scheduleStart; width: (parent.width - 8) / 2; height: 36
                                text: center.displayControl.displayTime(center.displayControl.nightlight.start || "18:00")
                                color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: 12
                                background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(center.foreground, 0.08) }
                                onEditingFinished: center.displayControl.configureNightlightTimes(text, scheduleEnd.text, center.displayControl.nightlight.mode)
                            }
                            TextField {
                                id: scheduleEnd; width: (parent.width - 8) / 2; height: 36
                                text: center.displayControl.displayTime(center.displayControl.nightlight.end || "09:00")
                                color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: 12
                                background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(center.foreground, 0.08) }
                                onEditingFinished: center.displayControl.configureNightlightTimes(scheduleStart.text, text, center.displayControl.nightlight.mode)
                            }
                        }
                        Label { visible: center.displayControl.nightlightError !== ""; width: parent.width; wrapMode: Text.WordWrap; text: center.displayControl.nightlightError }
                        OptionHeading { text: Eitr.I18n.tr("Main display") }
                        Column {
                        width: parent.width; spacing: PanelStyle.selectionRowGap
                        Repeater {
                            model: center.displayControl.monitors
                            KeyboardLayoutRow { required property var modelData; width: parent.width; label: modelData.name; foreground: center.foreground; showRemove: false; selected: modelData.name === center.displayControl.primaryDisplay; onActivated: center.displayControl.selectPrimary(modelData.name) }
                        }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Information")
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("About"); glyph: "󰋽"; onClicked: center.menuAction("system", "About") }
                            GridAction { title: Eitr.I18n.tr("Hardware"); glyph: "󰍛"; onClicked: center.panelRequested("hardware") }
                            GridAction { title: Eitr.I18n.tr("AI Usage"); glyph: ""; onClicked: center.panelRequested("ai") }
                            GridAction { title: Eitr.I18n.tr("Weather"); glyph: "󰖐"; onClicked: center.panelRequested("weather") }
                            GridAction { title: Eitr.I18n.tr("Report a Problem"); glyph: "󰃤"; onClicked: center.menuAction("system-information", "Report a Problem") }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Updates")
                        Item { width: parent.width; height: 32
                            Label { anchors.verticalCenter: parent.verticalCenter; text: center.updateChannel === "testing" ? Eitr.I18n.tr("Channel: Testing") : center.updateChannel === "stable" ? Eitr.I18n.tr("Channel: Stable") : Eitr.I18n.tr("Channel: unknown") }
                            PanelButton { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; width: 110; height: 30; textSize: 12; text: Eitr.I18n.tr("Change"); visible: center.organizationPolicy.update_channel === true; foreground: center.foreground; onClicked: center.walkerMenu("update-channel") }
                        }
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("System Update"); glyph: "󰚰"; onClicked: center.menuAction("system", "System Update") }
                            GridAction { title: Eitr.I18n.tr("What Changed"); glyph: "󰋚"; onClicked: center.menuAction("snapshots", "What Each Update Changed") }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Snapshots & Cleanup")
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("Restore a File"); glyph: "󰁯"; onClicked: center.menuAction("snapshots", "Restore a File or Folder") }
                            GridAction { title: Eitr.I18n.tr("Home Snapshots"); glyph: "󰉏"; onClicked: center.menuAction("snapshots", "Home Folder Snapshots") }
                            GridAction { title: Eitr.I18n.tr("Recovery Snapshots"); glyph: "󰆓"; onClicked: center.menuAction("snapshots", "List Recovery Snapshots") }
                            GridAction { title: Eitr.I18n.tr("Recovery Guide"); glyph: "󰋗"; onClicked: center.menuAction("snapshots", "Recovery Instructions") }
                            GridAction { title: Eitr.I18n.tr("Cleanup"); glyph: "󰃢"; onClicked: center.menuAction("system-maintenance", "Cleanup") }
                            GridAction { title: Eitr.I18n.tr("Dotfiles"); glyph: "󰘓"; onClicked: center.menuAction("settings", "Dotfiles") }
                        }
                        }
                    }
                    Column {
                        visible: center.page === "tools"; width: parent.width; spacing: 12
                        Fold {
                        title: Eitr.I18n.tr("Screenshots")
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("Selection"); glyph: "󰄀"; onClicked: center.menuAction("screenshot", "Selection") }
                            GridAction { title: Eitr.I18n.tr("Full Screen"); glyph: "󰹑"; onClicked: center.menuAction("screenshot", "Full Screen") }
                            GridAction { title: Eitr.I18n.tr("Window"); glyph: "󰖯"; onClicked: center.menuAction("screenshot", "Window") }
                            GridAction { title: Eitr.I18n.tr("Selection: Copy"); glyph: "󰆏"; onClicked: center.menuAction("screenshot", "Selection: Copy") }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Recording")
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("OBS Controls"); glyph: "󰻂"; onClicked: center.panelRequested("obs") }
                            GridAction { title: Eitr.I18n.tr("Record"); glyph: "󰑊"; onClicked: center.menuAction("screenrecord", "Record") }
                            GridAction { title: Eitr.I18n.tr("Record + Audio"); glyph: "󰕾"; onClicked: center.menuAction("screenrecord", "Record + Audio") }
                            GridAction { title: Eitr.I18n.tr("Stop Recording"); glyph: "󰓛"; onClicked: center.menuAction("screenrecord", "Stop Recording") }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Text & Color")
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("OCR Text"); glyph: "󰴑"; onClicked: center.menuAction("capture", "OCR Text") }
                            GridAction { title: Eitr.I18n.tr("QR Code"); glyph: "󰐲"; onClicked: center.menuAction("capture", "QR Code") }
                            GridAction { title: Eitr.I18n.tr("Color Picker"); glyph: "󰈊"; onClicked: center.menuAction("capture", "Color") }
                            GridAction { title: Eitr.I18n.tr("Transcode"); glyph: "󰈫"; onClicked: center.menuAction("capture", "Transcode") }
                        }
                        }
                        Fold {
                        title: Eitr.I18n.tr("Reminders & Sharing")
                        GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
                            GridAction { title: Eitr.I18n.tr("New Reminder"); glyph: "󰀠"; onClicked: center.menuAction("reminders", "New Reminder") }
                            GridAction { title: Eitr.I18n.tr("Upcoming"); glyph: "󰃰"; onClicked: center.menuAction("reminders", "Upcoming Reminders") }
                            GridAction { title: Eitr.I18n.tr("Share Clipboard"); glyph: "󰅌"; onClicked: center.menuAction("share", "Clipboard") }
                            GridAction { title: Eitr.I18n.tr("Share File"); glyph: "󰈔"; onClicked: center.menuAction("share", "File") }
                            GridAction { title: Eitr.I18n.tr("Share Folder"); glyph: "󰉋"; onClicked: center.menuAction("share", "Folder") }
                        }
                        }
                    }
                    Column {
                        visible: center.page === "general"; width: parent.width; spacing: 12
                        Section { text: Eitr.I18n.tr("Power"); width: parent.width }
                        PowerControls { visible: center.battery.available; width: parent.width; battery: center.battery; displayControl: center.displayControl; foreground: center.foreground }
                        // Lock is the everyday action; the session-ending ones sit behind one labelled button.
                        GridLayout {
                            width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
                            GridAction { title: Eitr.I18n.tr("Lock"); glyph: ""; onClicked: center.runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")]) }
                            GridAction { title: Eitr.I18n.tr("Power…"); glyph: ""; selected: center.powerOpen; onClicked: center.powerOpen = !center.powerOpen }
                            Repeater {
                                model: center.powerOpen ? [
                                    {title: Eitr.I18n.tr("Logout"), icon: "", command: ["uwsm", "stop"]},
                                    {title: Eitr.I18n.tr("Suspend"), icon: "", command: ["sh", "-c", "loginctl lock-session && sleep 1 && systemctl suspend"]},
                                    {title: Eitr.I18n.tr("Reboot"), icon: "", command: ["systemctl", "reboot", "--no-wall"]},
                                    {title: Eitr.I18n.tr("Shutdown"), icon: "", command: ["systemctl", "poweroff", "--no-wall"]}
                                ] : []
                                GridAction {
                                    required property var modelData
                                    title: modelData.title; glyph: modelData.icon
                                    onClicked: center.runAfterClose(modelData.command)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    component Section: PanelDivider {
        foreground: center.foreground
    }
    // Fold choices persist for the session; the surface encloses header and body.
    component Fold: Item {
        id: fold
        required property string title
        property bool startOpen: false
        default property alias body: foldBody.data
        readonly property bool open: center.folds[title] === undefined ? startOpen : center.folds[title]
        width: parent ? parent.width : 0
        implicitHeight: foldHeader.height + (open ? foldBody.implicitHeight + PanelStyle.selectionInset * 2 : 0)
        Rectangle {
            anchors.fill: parent
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(center.foreground, PanelStyle.selectionAlpha(false, false))
            border.width: 1; border.color: Qt.alpha(center.foreground, PanelStyle.dividerAlpha)
        }
        Rectangle {
            id: foldHeader
            width: parent.width; height: 34
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(center.foreground, foldMouse.containsMouse ? PanelStyle.selectionAlpha(false, true) : 0)
            Text {
                x: 12; width: parent.width - 42; anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                text: fold.title.toUpperCase(); color: center.foreground
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.bold: true; font.letterSpacing: 0.6
            }
            Text {
                anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
                text: fold.open ? "󰅀" : "󰅂"; color: center.accent
                font.family: DesktopFonts.family; font.pixelSize: 16
            }
            MouseArea { id: foldMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: center.setFold(fold.title, !fold.open) }
        }
        Column {
            id: foldBody
            visible: fold.open
            x: PanelStyle.selectionInset; y: foldHeader.height + PanelStyle.selectionInset
            width: fold.width - PanelStyle.selectionInset * 2; spacing: PanelStyle.selectionRowGap
        }
    }
    component OptionHeading: Label {
        width: parent.width
        topPadding: PanelStyle.selectionRowGap
        wrapMode: Text.WordWrap
        opacity: PanelStyle.secondaryTextOpacity
    }
    component GridAction: PanelButton {
        id: action
        property string tooltip: ""
        HoverHandler { id: actionHover; enabled: action.tooltip !== "" }
        BarTooltip { target: action; hovered: actionHover.hovered; text: action.tooltip; foreground: center.foreground; background: center.background }
        required property string title
        required property string glyph
        property url image: ""
        Layout.fillWidth: true; Layout.preferredWidth: 1; height: 34
        textSize: 12; iconSize: 16
        text: title; leadingIcon: glyph; leadingImage: image; foreground: center.foreground; textAlignment: Text.AlignLeft
    }
    component Label: Text {
        color: center.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
    component Tile: ControlCenterTile {
        tooltipBackground: center.background
        foreground: center.foreground; accent: center.accent; accentInk: PanelStyle.readableInk(center.accent, center.foreground, center.background)
    }
    // On/off switches: the accent fill shows the state, so no On/Off subtitle is needed.
    component ToggleTile: Tile {
        toggle: true
    }
    component Action: PanelButton {
        textSize: 12; iconSize: 16
        required property string title
        required property string glyph
        width: parent.width; height: 34
        text: title; leadingIcon: glyph; foreground: center.foreground; textAlignment: Text.AlignLeft
    }
}
