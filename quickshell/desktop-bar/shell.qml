import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import Eitr as Eitr
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Services.Pipewire
import Quickshell.Wayland
import "PanelStyle.js" as PanelStyle
import "WorkspaceModel.js" as WorkspaceModel
import "BarGeometry.js" as BarGeometry
import "EdgeSlopes.js" as EdgeSlopes

ShellRoot {
    Component.onCompleted: {
        Quickshell.watchFiles = Quickshell.env("EITR_LIVE_RELOAD") === "1";
        PluginRegistry.startDiagnostics();
    }
    id: shell
    signal handbookOpened()
    NetworkService { id: networkOwner }
    NotificationService { id: notificationsService }
    RemoteAccessService { id: remoteAccessService; observing: shell.remotePanelsOpen }
    Handbook {
        id: handbook
        foreground: shell.fg
        background: shell.barBackground()
        accent: shell.activeBg
        screen: shell.targetScreens()[0] || null
        onOpenedChanged: if (opened) shell.handbookOpened()
        onSetupRequested: function(kind) {
            // Layouts are added in Walker's Keyboard menu; the bar panel only switches them.
            if (kind === "keyboard") {
                Quickshell.execDetached([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:keyboard"]);
                return;
            }
            var script = kind === "theme" || kind === "wallpaper" ? "appearance-picker.sh" : "show-panel.sh";
            Quickshell.execDetached(["bash", Quickshell.shellDir + "/scripts/" + script, kind]);
        }
        onWelcomeChoice: function(action) { Quickshell.execDetached(shell.welcomeCommand(action)); }
        onProblemReportsChoice: function(offer) {
            Quickshell.execDetached(shell.problemReportsCommand(["set", offer ? "on" : "off"]));
        }
    }
    function problemReportsCommand(args) {
        return ["python3", Quickshell.shellDir + "/scripts/problem-reports.py"].concat(args);
    }
    // Once after the boot guard restored the system, a login hears about it.
    Timer {
        interval: 8000
        running: true
        onTriggered: Quickshell.execDetached(["bash", Quickshell.shellDir + "/scripts/boot-guard-notice.sh"])
    }
    // The welcome's "offer to report problems" switch starts from the saved choice.
    Process {
        command: shell.problemReportsCommand(["status"])
        running: true
        stdout: StdioCollector { id: problemStatusOutput }
        onExited: function(code) {
            if (code !== 0) return;
            try { handbook.offerProblemReports = JSON.parse(problemStatusOutput.text).offer; } catch (error) {}
        }
    }
    function welcomeCommand(action) {
        return ["python3", Quickshell.shellDir + "/scripts/welcome-state.py", action];
    }
    // The first-login welcome opens at most once per Quickshell session; configuration reloads keep this flag.
    PersistentProperties {
        id: welcomeSession
        reloadableId: "handbookWelcomeSession"
        property bool checked: false
    }
    Timer {
        // Let the bar and the startup wallpaper reveal settle first.
        interval: 2000
        running: !welcomeSession.checked
        onTriggered: welcomeStatus.running = true
    }
    Process {
        id: welcomeStatus
        command: shell.welcomeCommand("status")
        stdout: StdioCollector { id: welcomeOutput }
        onExited: function(code) {
            welcomeSession.checked = true;
            if (code !== 0) return;
            try {
                var state = JSON.parse(welcomeOutput.text);
                if (state.show) handbook.showWelcome(state.pending);
            } catch (error) {}
        }
    }
    PersistentProperties {
        id: pluginSession
        reloadableId: "pluginLoginSession"
        property bool dispatched: false
    }
    Timer {
        interval: 12000
        running: !pluginSession.dispatched
        onTriggered: {
            pluginSession.dispatched = true;
            Quickshell.execDetached(["python3", Eitr.Paths.code("walker/scripts/actions/install/plugins.py"), "hooks", "login"]);
        }
    }
    LiveWallpaper {}
    PluginDesktop {
        id: pluginDesktop
        foreground: shell.fg; background: shell.barBackground(); accent: shell.activeBg
        grid: shell.windowGaps[0]
    }
    RealmEffects {
        accent: shell.activeBg
        defaultScreen: shell.targetScreens()[0] || null
    }
    ReloadErrorPopup {
        foreground: shell.fg
        background: shell.barBackground()
        targetScreen: shell.targetScreens()[0] || null
        barEdge: shell.barEdge
    }

    property int remoteObservers: 0
    readonly property bool remotePanelsOpen: remoteObservers > 0
    property bool statusOpen: false
    property bool barVisible: true
    property int barHeight: 30
    property color bg: Qt.rgba(24 / 255, 24 / 255, 36 / 255, 0.38)
    property color fg: "#cdd6f4"
    property color activeFg: "#11111b"
    property color activeBg: "#cdd6f4"
    property color hoverBg: Qt.rgba(180 / 255, 190 / 255, 254 / 255, 0.15)
    property bool idleLockEnabled: false
    readonly property string idleLockGlyph: idleLockEnabled ? "󱫗" : "󱫖"
    readonly property string idleLockTooltip: idleLockEnabled ? Eitr.I18n.tr("Idle Lock: On") : Eitr.I18n.tr("Idle Lock: Off")
    function switchIdleLock() { if (!toggleIdleLock.running) toggleIdleLock.running = true; }
    property var hardwareIdentity: null
    property var battery: PowerService.battery
    readonly property string batteryIcon: battery.status === "Charging" ? "󰂄" : battery.percent < 20 ? "󰁻" : battery.percent < 60 ? "󰁾" : "󰁹"
    property string primaryDisplay: DisplayService.topology.primary
    property var preferredOutputs: DisplayService.topology.preferred
    property string workspaceStyle: "Runes"
    readonly property int workspaceCount: WorkspaceModel.ceiling(WorkspaceModel.occupied(Hyprland.toplevels.values),
        Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : 0)
    readonly property int workspaceItemSize: 24
    readonly property int workspaceItemSpacing: 4
    property color workspaceMenuBg: "#181824"
    property color workspaceMenuFg: "#cdd6f4"
    property string barAppearance: "solid"
    property string barLayout: "unified"
    property bool barPinned: false
    property bool barAutoHide: false
    property bool barDock: true
    DockClients { id: dockClients; observing: shell.barDock && !FocusMode.enabled }
    property string barMediaStyle: "bars"
    property string barClock: "12h"
    // "all" puts a bar on every display; the main one keeps notifications.
    property string barScreens: "main"
    property var windowGaps: DisplayService.topology.windowGaps
    property var screenGaps: DisplayService.topology.screenGaps
    readonly property bool islandsLayout: barLayout === "islands"
    readonly property bool notchLayout: barLayout === "notch"
    readonly property real tabStripThickness: 7
    // Radius of the four bends on each Tabs slope.
    readonly property real tabBendRound: 6
    readonly property bool centeredLayout: barLayout === "centered"
    readonly property bool iconsOpen: centeredLayout || notchLayout || statusOpen
    property string barEdge: "top"
    property bool settingsDirty: false
    property string dragCandidate: ""
    property bool barPointerHeld: false
    readonly property bool verticalBar: barEdge === "left" || barEdge === "right"
    readonly property var desktopApplications: DesktopEntries.applications.values

    function barBackground() {
        return barAppearance === "solid" ? workspaceMenuBg : bg;
    }

    function barDoubleClick(button) {
        if (button === Qt.LeftButton) updateBarSetting("appearance", barAppearance === "solid" ? "transparent" : "solid");
        else if (button === Qt.RightButton) updateBarSetting("layout", barLayout === "unified" ? "centered" : barLayout === "centered" ? "notch" : barLayout === "notch" ? "islands" : "unified");
    }

    function updateBarSetting(key, value) {
        var choices = {appearance: ["transparent", "solid"], layout: ["unified", "centered", "notch", "islands"], edge: ["top", "bottom", "left", "right"], pinned: ["yes", "no"], screens: ["main", "all"], autohide: ["yes", "no"], dock: ["yes", "no"], reduceMotion: ["yes", "no"], mediaStyle: ["bars", "line"], clock: ["12h", "24h"]};
        if (!choices[key] || choices[key].indexOf(value) === -1) return;
        if (key === "appearance") barAppearance = value;
        else if (key === "layout") barLayout = value;
        else if (key === "pinned") barPinned = value === "yes";
        else if (key === "mediaStyle") barMediaStyle = value;
        else if (key === "clock") barClock = value;
        else if (key === "screens") barScreens = value;
        else if (key === "reduceMotion") DesktopStyle.reduceMotion = value === "yes";
        else if (key === "dock") barDock = value === "yes";
        else if (key === "autohide") barAutoHide = value === "yes";
        else barEdge = value;
        settingsDirty = true;
        settingsSaveDelay.restart();
    }

    IpcHandler {
        target: "bar"
        function idleLock(enabled: bool): void { shell.idleLockEnabled = enabled; }
        function workspaces(): string { return JSON.stringify({count: shell.workspaceCount, limit: 10}); }
        function visibility(): void { shell.barVisible = !shell.barVisible; }
        function update(key: string, value: string): void { shell.updateBarSetting(key, value) }
        function toggle(kind: string): void {
            if (kind === "appearance") shell.updateBarSetting(kind, shell.barAppearance === "solid" ? "transparent" : "solid");
            else if (kind === "layout") shell.updateBarSetting(kind, shell.barLayout === "unified" ? "centered" : shell.barLayout === "centered" ? "notch" : shell.barLayout === "notch" ? "islands" : "unified");
        }
    }

    Process {
        id: barSettingsQuery
        command: ["python3", Quickshell.shellDir + "/scripts/bar-settings.py", "status"]
        running: true
        stdout: StdioCollector { id: barSettingsOutput }
        onExited: function(code) {
            if (code !== 0 || shell.settingsDirty || saveBarSettings.running) return;
            try {
                var settings = JSON.parse(barSettingsOutput.text);
                shell.barAppearance = settings.appearance;
                shell.barLayout = ["unified", "centered", "notch", "islands"].indexOf(settings.layout) >= 0 ? settings.layout : "unified";
                shell.barEdge = settings.edge;
                shell.barPinned = settings.pinned === "yes";
                shell.barMediaStyle = settings.mediaStyle === "line" ? "line" : "bars";
                shell.barClock = settings.clock === "24h" ? "24h" : "12h";
                shell.barScreens = settings.screens || "main";
                shell.barAutoHide = settings.autohide === "yes";
                shell.barDock = settings.dock !== "no";
                DesktopStyle.reduceMotion = settings.reduceMotion === "yes";
            } catch (e) {}
        }
    }

    PreferenceWatch {
        path: Eitr.Paths.config("quickshell/desktop-bar/bar-settings.json")
        onChanged: settingsReload.restart()
    }
    Timer {
        id: settingsReload
        interval: 40
        onTriggered: {
            if (barSettingsQuery.running || saveBarSettings.running || shell.settingsDirty) restart();
            else barSettingsQuery.running = true;
        }
    }

    Timer {
        id: settingsSaveDelay
        interval: 100
        onTriggered: shell.persistBarSettings()
    }

    function persistBarSettings() {
        if (saveBarSettings.running) return;
        settingsDirty = false;
        saveBarSettings.command = ["python3", Quickshell.shellDir + "/scripts/bar-settings.py",
            "set-all", barAppearance, barLayout, barEdge, barPinned ? "yes" : "no", barScreens, barAutoHide ? "yes" : "no", DesktopStyle.reduceMotion ? "yes" : "no", barMediaStyle, barDock ? "yes" : "no", barClock];
        saveBarSettings.running = true;
    }

    Process {
        id: saveBarSettings
        onExited: {
            if (shell.settingsDirty) shell.persistBarSettings();
            else if (!barSettingsQuery.running) barSettingsQuery.running = true;
        }
    }

    function setWorkspaceStyle(style) {
        shell.workspaceStyle = style;
        saveWorkspaceStyle.command = ["python3", Quickshell.shellDir + "/scripts/workspace-style.py", style];
        saveWorkspaceStyle.running = true;
    }

    Process {
        id: saveWorkspaceStyle
        onExited: if (!workspacePalette.running) workspacePalette.running = true
    }

    Process {
        id: workspacePalette
        command: ["python3", Quickshell.shellDir + "/scripts/workspace-color.py"]
        running: true
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var palette = JSON.parse(text);
                    PluginRegistry.palette = palette.palette || ({});
                    shell.activeBg = palette.background;
                    shell.activeFg = palette.foreground;
                    if (!saveWorkspaceStyle.running) shell.workspaceStyle = palette.style;
                    shell.workspaceMenuBg = palette.menuBackground;
                    shell.workspaceMenuFg = palette.menuForeground;
                    shell.fg = palette.menuForeground;
                    DesktopStyle.criticalColor = palette.critical;
                    var background = shell.workspaceMenuBg;
                    shell.bg = Qt.rgba(background.r, background.g, background.b, 0.38);
                    shell.hoverBg = Qt.rgba(shell.fg.r, shell.fg.g, shell.fg.b, 0.15);
                } catch (e) {}
            }
        }
    }

    PreferenceWatch {
        path: Eitr.Paths.config("theme/current/colors.toml")
        ancestor: Eitr.Paths.config("theme")
        onChanged: paletteReload.restart()
    }
    PreferenceWatch {
        path: Eitr.Paths.config("quickshell/desktop-bar/workspace-style.json")
        onChanged: paletteReload.restart()
    }
    Timer {
        id: paletteReload
        interval: 40
        onTriggered: {
            if (workspacePalette.running || saveWorkspaceStyle.running) restart();
            else workspacePalette.running = true;
        }
    }

    Process {
        id: idleLockStatus
        command: ["pgrep", "-x", "hypridle"]
        running: true
        onExited: function(code) { shell.idleLockEnabled = code === 0; }
    }

    Timer {
        interval: 30000
        running: true
        repeat: true
        onTriggered: if (!idleLockStatus.running && !toggleIdleLock.running) idleLockStatus.running = true
    }

    Process {
        id: toggleIdleLock
        command: ["bash", Eitr.Paths.code("walker/scripts/actions/toggle/idle-lock.sh")]
        onExited: if (!idleLockStatus.running) idleLockStatus.running = true
    }

    Connections {
        target: PowerService
        function onBatteryReceived() { shell.checkBatteryLow(); }
    }
    // The user's hooks (distro/lib/run-hook.sh): battery-low once per drop to 15%,
    // post-boot at start (the runner keeps it to once per boot).
    property bool batteryLowHookRan: false
    function runHook(args) {
        var library = Quickshell.env("EITR_LIBRARY_ROOT") || (Eitr.Paths.codeRoot + "/lib");
        Quickshell.execDetached(["bash", library + "/run-hook.sh"].concat(args));
    }
    // The lowest battery warning already given during this discharge (0 = none).
    property int batteryWarned: 0
    function checkBatteryLow() {
        var discharging = shell.battery.available && shell.battery.status === "Discharging";
        var low = discharging && shell.battery.percent <= 15;
        if (low && !batteryLowHookRan) runHook(["battery-low", String(shell.battery.percent)]);
        batteryLowHookRan = low;
        if (!discharging) { batteryWarned = 0; return; }
        var level = shell.battery.percent <= 5 ? 5 : shell.battery.percent <= 10 ? 10 : 0;
        if (level === 0 || (batteryWarned !== 0 && batteryWarned <= level)) return;
        batteryWarned = level;
        Quickshell.execDetached(["notify-send", "--app-name=Battery", "--urgency=" + (level === 5 ? "critical" : "normal"),
            "--icon=battery-caution-symbolic", level === 5 ? "Battery almost empty" : "Battery low",
            shell.battery.percent + "% left. " + (level === 5 ? "Plug in now to avoid losing work." : "Plug in soon.")]);
    }
    Timer { interval: 5000; running: true; onTriggered: shell.runHook(["post-boot"]) }
    // Reminders survive restarts: reschedule them, and show ones that came due while off.
    Timer {
        interval: 6000
        running: true
        onTriggered: Quickshell.execDetached(["python3", Eitr.Paths.codeRoot + "/walker/scripts/actions/tools/reminders.py", "restore"])
    }

    // Checked shortly after login, every six hours, and again after System Update.
    property var updates: ({checking: true, count: 0, repository: 0, aur: 0, downloadBytes: 0})
    // A notification goes out only when more updates are pending than were last announced.
    property int announcedUpdates: 0
    readonly property string updatesIcon: updates.checking ? "󰁪" : updates.count > 0 ? "󰚰" : "󰗡"
    readonly property string updatesSize: updates.downloadBytes <= 0 ? ""
        : updates.downloadBytes >= 1073741824 ? (updates.downloadBytes / 1073741824).toFixed(1) + " GB"
        : Math.max(1, Math.round(updates.downloadBytes / 1048576)) + " MB"
    readonly property string updatesTooltip: {
        if (updates.checking) return "Checking for updates";
        if (updates.count === 0) return "Up to date · right-click to check again";
        return updates.count + (updates.count === 1 ? " update" : " updates") + (updatesSize ? " · " + updatesSize : "");
    }
    function announceUpdates() {
        if (updates.count <= announcedUpdates) {
            announcedUpdates = updates.count;
            return;
        }
        announcedUpdates = updates.count;
        Quickshell.execDetached(["bash", Quickshell.shellDir + "/scripts/updates-notify.sh", String(updates.count), updatesSize]);
    }
    function checkUpdates() {
        if (updatesQuery.running) return;
        shell.updates = Object.assign({}, shell.updates, {checking: true});
        updatesQuery.running = true;
    }
    function openSystemUpdate() {
        var root = Quickshell.env("EITR_CODE_ROOT") || Quickshell.shellDir + "/../..";
        // Floating, with the theme's solid background, like terminals that menus open.
        Quickshell.execDetached([root + "/walker/bin/menu-path/kitty", "-e", "python3", root + "/walker/scripts/actions/task-terminal.py",
            "bash", root + "/walker/scripts/actions/system/update.sh", "system"]);
    }
    Process {
        id: updatesQuery
        command: ["python3", Quickshell.shellDir + "/scripts/updates.py"]
        stdout: StdioCollector { id: updatesOutput }
        onExited: {
            try { shell.updates = Object.assign({checking: false}, JSON.parse(updatesOutput.text)); }
            catch (e) { shell.updates = {checking: false, count: 0, repository: 0, aur: 0, downloadBytes: 0}; }
            shell.announceUpdates();
        }
    }
    Timer { interval: 45000; running: true; onTriggered: shell.checkUpdates() }
    Timer { interval: 6 * 60 * 60 * 1000; repeat: true; running: true; onTriggered: shell.checkUpdates() }
    IpcHandler {
        target: "updates"
        function refresh(): void { shell.checkUpdates(); }
    }
    // Hold-to-talk dictation (walker/scripts/actions/tools/dictate.sh) turns the
    // recording dot into a live waveform while the microphone listens, then a
    // slow pulse while the speech is transcribed.
    property bool dictating: false
    property bool transcribing: false
    // Microphone levels for the waveform, newest first (drawn at the centre).
    property var dictationLevels: [0, 0, 0, 0]
    IpcHandler {
        target: "dictation"
        function start(): void { shell.transcribing = false; shell.dictating = true; dictationSafety.restart(); }
        function transcribe(): void { shell.dictating = false; shell.transcribing = true; dictationSafety.restart(); }
        function stop(): void { shell.dictating = false; shell.transcribing = false; dictationSafety.stop(); }
    }
    // A lost stop must not leave the dot on.
    Timer { id: dictationSafety; interval: 300000; onTriggered: { shell.dictating = false; shell.transcribing = false; } }
    // The waveform never outlives the recording: while it shows, check every few
    // seconds that a recorder still exists (dictate.sh keeps its pid in these files).
    Timer {
        interval: 3000; repeat: true; running: shell.dictating
        onTriggered: dictationAlive.running = true
    }
    Process {
        id: dictationAlive
        command: ["sh", "-c", "for mode in dictation voice; do f=\"${XDG_RUNTIME_DIR:-/tmp}/eitr-$mode.pid\"; [ -f \"$f\" ] && kill -0 \"$(cat \"$f\")\" 2>/dev/null && exit 0; done; exit 1"]
        onExited: (code) => { if (code !== 0 && shell.dictating) shell.dictating = false; }
    }
    PwNodePeakMonitor {
        id: dictationPeak
        node: Pipewire.defaultAudioSource
        enabled: shell.dictating && node !== null
    }
    Timer {
        interval: 70; repeat: true; running: shell.dictating
        // Speech peaks sit low on a linear scale; the square root lifts them.
        onTriggered: shell.dictationLevels = [Math.min(1, Math.sqrt(dictationPeak.peak) * 1.4)].concat(shell.dictationLevels.slice(0, 3))
    }
    onDictatingChanged: if (!dictating) dictationLevels = [0, 0, 0, 0]

    TimePicker { defaultScreen: shell.targetScreens()[0] || null; foreground: shell.fg; background: shell.barBackground() }
    AppearancePicker { defaultScreen: shell.targetScreens()[0] || null }

    function focusWorkspace(id) {
        var command = WorkspaceModel.focusCommand(id);
        if (command.length) Quickshell.execDetached(command);
    }

    // With a bar on every display, each bar marks the workspace shown on its own display.
    function workspaceActive(index, screen) {
        if (barScreens === "all" && screen) {
            var monitor = Hyprland.monitorFor(screen);
            return !!(monitor && monitor.activeWorkspace && monitor.activeWorkspace.id === index);
        }
        return Hyprland.focusedWorkspace && Hyprland.focusedWorkspace.id === index;
    }

    function workspaceLabel(index, screen) {
        if (workspaceStyle === "Glyph") return workspaceActive(index + 1, screen) ? "✦" : "✧";
        return String(index + 1);
    }

    function workspaceApps(workspaceId) {
        var names = [];
        for (var window of Hyprland.toplevels.values) {
            if (!window.workspace || window.workspace.id !== workspaceId) continue;
            var info = window.lastIpcObject;
            if (info.mapped === false) continue;
            var appId = (window.wayland && window.wayland.appId) || info.class || info.initialClass || "";
            var entry = desktopApplications.find(app => app.id === appId || app.startupClass === appId)
                || DesktopEntries.heuristicLookup(appId);
            var name = entry ? entry.name : appId;
            if (name && names.indexOf(name) === -1) names.push(name);
        }
        return names.join("\n");
    }

    // display-primary.py owns the choice and reports it as primaryDisplay.
    // This fallback mirrors its choose_primary() order (saved/reported name,
    // first connected machine-local preferred output, else the largest screen)
    // so startup and unmatched names pick the same screen without a bar jump.
    function mainScreen() {
        var screens = Quickshell.screens || [];
        var byName = {};
        var largest = null;
        for (var i = 0; i < screens.length; i++) {
            if (!screens[i])
                continue;
            byName[screens[i].name] = screens[i];
            if (!largest || screens[i].width * screens[i].height > largest.width * largest.height)
                largest = screens[i];
        }
        if (primaryDisplay && byName[primaryDisplay])
            return byName[primaryDisplay];
        for (var j = 0; j < preferredOutputs.length; j++) {
            if (byName[preferredOutputs[j]])
                return byName[preferredOutputs[j]];
        }
        return largest;
    }

    // Bars by screen name, so shortcuts reach the bar of the display in use.
    property var barsByScreen: ({})
    function registerBar(bar) {
        var bars = Object.assign({}, barsByScreen);
        bars[bar.modelData.name] = bar;
        barsByScreen = bars;
    }
    function unregisterBar(bar) {
        var bars = Object.assign({}, barsByScreen);
        if (bars[bar.modelData.name] === bar) delete bars[bar.modelData.name];
        barsByScreen = bars;
    }
    function activeBar(fallback) {
        var focused = Hyprland.focusedMonitor;
        return (focused && barsByScreen[focused.name]) || fallback;
    }
    function isActiveBar(bar) {
        var active = activeBar(null);
        return active ? active === bar : bar.isMainBar;
    }

    // The main display first, then, when the bar is shown on every display, the others.
    function targetScreens() {
        var main = mainScreen();
        if (!main)
            return [];
        if (barScreens !== "all")
            return [main];
        return [main].concat((Quickshell.screens || []).filter(screen => screen && screen !== main));
    }

    Variants {
        model: FocusMode.enabled ? Quickshell.screens : []
        delegate: Component {
            PanelWindow {
                required property var modelData
                screen: modelData
                anchors { top: true; left: true; right: true }
                implicitHeight: 28; exclusiveZone: 28
                color: "transparent"
                WlrLayershell.namespace: "eitr-focus-strip"
                FocusStrip {
                    anchors.fill: parent
                    tabs: FocusMode.tabs(modelData)
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    clockText: Qt.formatDateTime(focusClock.date, shell.barClock === "24h" ? "HH:mm" : "h:mm AP")
                    networkText: shell.focusNetworkGlyph
                    batteryText: shell.battery.available ? shell.batteryIcon + " " + Math.round(shell.battery.percent) + "%" : ""
                    onSelected: address => FocusMode.activate(address)
                }
            }
        }
    }
    SystemClock { id: focusClock; precision: SystemClock.Minutes }
    readonly property string wifiGlyph: networkOwner.glyph
    readonly property string focusNetworkGlyph: networkOwner.focusGlyph


    Variants {
        model: shell.targetScreens()

        delegate: Component {
            PanelWindow {
                id: bar

                required property var modelData
                readonly property bool isMainBar: modelData === shell.mainScreen()
                readonly property Item stripItem: barContents
                // Vertical bars keep the horizontal depth: the clock stacks and the weather shows only its icon.
                readonly property real normalThickness: shell.barHeight
                readonly property real thinThickness: normalThickness
                // Space between a tab's outermost item and its slope, the same on every tab.
                readonly property real tabsPadding: 4
                function tabItemStart(item) {
                    var start = 0;
                    while (item && item !== barContents) {
                        start += shell.verticalBar ? item.y : item.x;
                        item = item.parent;
                    }
                    return start;
                }
                readonly property real tabLeadingEnd: (shell.verticalBar
                    ? tabItemStart(verticalStart) + verticalStart.height
                    : tabItemStart(hardwareStatus) + hardwareStatus.width) + tabsPadding
                readonly property real tabTrailingStart: tabItemStart(shell.verticalBar ? verticalEnd : rightSide) - tabsPadding
                readonly property real tabCenterStart: (shell.verticalBar
                    ? tabItemStart(verticalMedia.visible ? verticalMedia : verticalCapture.shown ? verticalCapture : verticalCalendarIcon)
                    : tabItemStart(mediaStrip.visible ? mediaStrip : barCapture.shown ? barCapture : centerInfo)) - tabsPadding
                readonly property real tabCenterEnd: (shell.verticalBar
                    ? tabItemStart(verticalCalendarIcon) + verticalCalendarIcon.height + (notchLayout ? weatherReveal : 3 + verticalWeatherIcon.height)
                    : tabItemStart(centerInfo) + centerInfo.width + (notchLayout ? weatherReveal : 6 + barWeather.width)) + tabsPadding
                readonly property var outerGaps: shell.screenGaps
                readonly property bool centeredLayout: shell.centeredLayout
                readonly property bool islandsLayout: shell.islandsLayout
                // Islands float half the outer gap off the screen edge; pills keep the full gap between them.
                readonly property real islandGap: outerGaps[({top: 0, right: 1, bottom: 2, left: 3})[shell.barEdge]] / 2
                readonly property real islandSpacing: islandGap * 2 + 8
                readonly property real reservedThickness: normalThickness + (islandsLayout ? islandGap : 0)
                readonly property bool notchLayout: shell.notchLayout
                readonly property real panelGap: shell.verticalBar ? shell.windowGaps[1] + shell.windowGaps[3] : shell.windowGaps[0] + shell.windowGaps[2]
                property bool hoverExpanded: false
                readonly property bool pointerInside: barHover.hovered || centeredHover.hovered
                onPointerInsideChanged: {
                    if (pointerInside) { collapseDelay.stop(); hoverExpanded = true; }
                    else collapseDelay.restart();
                }
                readonly property bool expanded: !centeredLayout || shell.barPinned || hoverExpanded || panelOpen || pendingPanel !== null || shell.barPointerHeld
                readonly property real itemGap: shell.workspaceItemSpacing
                readonly property real endPadding: shell.verticalBar ? 8 : 12
                readonly property real centerPadding: (centerExtent - (shell.verticalBar ? verticalCalendarIcon.height : centerInfo.width)) / 2
                readonly property real leadingExtent: endPadding - centerPadding + (shell.verticalBar
                    ? verticalStart.height + itemGap + (mediaStrip.player ? verticalMedia.height + itemGap : 0) + verticalPin.height + itemGap + (verticalCapture.shown ? verticalCapture.height + itemGap : 0)
                    : workspaces.width + itemGap + hardwareStatus.width + itemGap + (mediaStrip.visible ? mediaStrip.width + itemGap : 0) + barPin.width + itemGap + (barCapture.shown ? barCapture.width + itemGap : 0))
                readonly property real trailingExtent: endPadding - centerPadding + (shell.verticalBar
                    ? itemGap + verticalWeatherIcon.height + itemGap + verticalEnd.height
                    : itemGap + barWeather.width + itemGap + rightSide.width + itemGap + notificationIcon.width)
                property real leadingReveal: centeredLayout && expanded ? Math.min(leadingExtent, (shell.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : 0
                property real trailingReveal: centeredLayout && expanded ? Math.min(trailingExtent, (shell.verticalBar ? bar.height : bar.width) / 2 - centerExtent / 2) : 0
                Behavior on leadingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
                Behavior on trailingReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
                property bool weatherHovered: false
                readonly property bool weatherExpanded: weatherHovered || weatherMenu.visible || pendingPanel === weatherMenu
                readonly property real weatherExtent: shell.verticalBar ? 3 + verticalWeatherIcon.height : 6 + barWeather.width
                property real weatherReveal: notchLayout && weatherExpanded ? weatherExtent : 0
                Behavior on weatherReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
                Timer {
                    id: weatherCollapseDelay
                    interval: collapseDelay.interval
                    onTriggered: bar.weatherHovered = false
                }
                readonly property real centerExtent: shell.verticalBar ? 56 : centerInfo.width + 24
                Timer {
                    id: collapseDelay
                    interval: 350
                    onTriggered: bar.hoverExpanded = false
                }
                readonly property var dockPanels: [wifiMenu, bluetoothMenu, brightnessMenu, volumeMenu, tailscaleMenu, streamingMenu,
                    keyboardMenu, calendarMenu, weatherMenu, hardwareMenu, aiMenu, obsMenu, recordingMenu, workspaceMenu, notificationCenter, controlCenter, mediaMenu, batteryMenu, pluginPanel]
                readonly property bool panelOpen: dockPanels.some(panel => panel.visible)
                readonly property var panelFocusWindows: notificationPopups.visible ? [bar, notificationPopups] : [bar]
                property var pendingPanel: null
                property bool pendingOverview: false

                function closePanels() {
                    pendingPanel = null;
                    pendingOverview = false;
                    overview.opened = false;
                    dockPanels.forEach(panel => panel.opened = false);
                }
                Connections {
                    target: shell
                    function onHandbookOpened() { bar.closePanels(); }
                }
                function showPanel(panel) {
                    pendingOverview = false;
                    overview.opened = false;
                    pendingPanel = panel;
                    dockPanels.forEach(other => other.opened = false);
                    finishPanelSwitch();
                }
                function togglePanel(panel) {
                    if (panel.opened || pendingPanel === panel) closePanels();
                    else showPanel(panel);
                }
                function toggleOverview() {
                    if (overview.opened || pendingOverview) { closePanels(); return; }
                    pendingPanel = null;
                    pendingOverview = true;
                    dockPanels.forEach(panel => panel.opened = false);
                    finishPanelSwitch();
                }
                EdgeDock {
                    screen: bar.screen
                    barEdge: shell.barEdge
                    clients: dockClients.clients
                    dockEnabled: shell.barDock && shell.barVisible && !FocusMode.enabled
                    foreground: shell.fg
                    background: shell.barBackground()
                }
                WorkspaceOverview {
                    id: overview
                    ipcEnabled: bar.isMainBar
                    screen: bar.screen
                    foreground: shell.fg
                    background: shell.bg
                    accent: shell.activeBg
                }
                function finishPanelSwitch() {
                    if (dockPanels.some(panel => panel.visible) || overview.visible) return;
                    if (pendingOverview) {
                        pendingOverview = false;
                        overview.opened = true;
                        return;
                    }
                    if (!pendingPanel) return;
                    var next = pendingPanel;
                    pendingPanel = null;
                    next.opened = true;
                }
                Timer {
                    interval: 16
                    repeat: true
                    running: bar.pendingPanel !== null || bar.pendingOverview
                    onTriggered: bar.finishPanelSwitch()
                }

                screen: modelData
                visible: shell.barVisible || panelOpen
                implicitWidth: modelData.width
                implicitHeight: modelData.height
                color: "transparent"
                exclusionMode: ExclusionMode.Normal
                // Auto-hide reserves no space, so revealing the bar slides it over windows instead of re-tiling them.
                exclusiveZone: !FocusMode.enabled && shell.barVisible && !shell.barAutoHide ? bar.reservedThickness : 0
                WlrLayershell.namespace: "desktop-bar"
                // Notification popups must have a strictly higher layer than
                // panels, rather than depending on same-layer mapping order.
                WlrLayershell.layer: panelOpen && !notificationPopups.visible ? WlrLayer.Overlay : WlrLayer.Top
                mask: dockInput
                WlrLayershell.keyboardFocus: panelOpen ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

                BarAutoHide {
                    id: autoHide
                    autoHide: shell.barAutoHide
                    pointerInside: bar.pointerInside || edgeHover.hovered
                    held: bar.panelOpen || bar.pendingPanel !== null || bar.pendingOverview || overview.visible || shell.barPointerHeld || notificationPopups.visible
                }
                Item {
                    id: edgeSensor
                    width: shell.verticalBar ? 1 : bar.width
                    height: shell.verticalBar ? bar.height : 1
                    x: shell.barEdge === "right" ? bar.width - width : 0
                    y: shell.barEdge === "bottom" ? bar.height - height : 0
                    visible: shell.barAutoHide
                    HoverHandler { id: edgeHover }
                }
                Region {
                    id: dockInput
                    width: 0; height: 0
                    // Focus hides the bar but keeps its window: hiding the window crashes Quickshell.
                    Region { item: edgeSensor.visible && !FocusMode.enabled ? edgeSensor : null }
                    Region { item: shell.barPointerHeld && !FocusMode.enabled ? bar.contentItem : null }
                    Region { item: FocusMode.enabled ? null : shell.notchLayout ? tabStrip : shell.centeredLayout || shell.islandsLayout ? null : barContents }
                    IslandMask { surfaces: islandSurfaces.children }
                    CenteredBarMask { surface: centeredOutline; edge: shell.barEdge; depth: bar.normalThickness; bendRound: shell.tabBendRound }
                    Region { item: shell.notchLayout && !FocusMode.enabled ? leadingTab : null }
                    Region { item: shell.notchLayout && !FocusMode.enabled ? notchTab : null }
                    Region { item: shell.notchLayout && !FocusMode.enabled ? trailingTab : null }
                    Region { item: wifiMenu.opened ? wifiMenu : null }
                    Region { item: bluetoothMenu.opened ? bluetoothMenu : null }
                    Region { item: brightnessMenu.opened ? brightnessMenu : null }
                    Region { item: volumeMenu.opened ? volumeMenu : null }
                    Region { item: tailscaleMenu.opened ? tailscaleMenu : null }
                    Region { item: streamingMenu.opened ? streamingMenu : null }
                    Region { item: keyboardMenu.opened ? keyboardMenu : null }
                    Region { item: calendarMenu.opened ? calendarMenu : null }
                    Region { item: weatherMenu.opened ? weatherMenu : null }
                    Region { item: hardwareMenu.opened ? hardwareMenu : null }
                    Region { item: aiMenu.opened ? aiMenu : null }
                    Region { item: obsMenu.opened ? obsMenu : null }
                    Region { item: recordingMenu.opened ? recordingMenu : null }
                    Region { item: workspaceMenu.opened ? workspaceMenu : null }
                    Region { item: notificationCenter.opened ? notificationCenter : null }
                    Region { item: controlCenter.opened ? controlCenter : null }
                    Region { item: mediaMenu.opened ? mediaMenu : null }
                    Region { item: batteryMenu.opened ? batteryMenu : null }
                    Region { item: pluginPanel.opened ? pluginPanel : null }
                }

                Connections {
                    target: notificationsService
                    function onToggleRequested() {
                        // With a bar on every display, only the one in use opens the center.
                        if (shell.isActiveBar(bar)) bar.togglePanel(notificationCenter);
                    }
                }
                Connections {
                    target: shell
                    function onBarVisibleChanged() {
                        if (!shell.barVisible) bar.closePanels();
                    }
                }

                NotificationPopups {
                    id: notificationPopups
                    screen: bar.screen
                    shown: bar.isMainBar
                    service: notificationsService
                    foreground: shell.fg
                    background: shell.barBackground()
                    accent: shell.activeBg
                    barEdge: shell.barEdge
                }

                NotificationCenter {
                    id: notificationCenter
                    service: notificationsService
                    maximumHeight: bar.screen.height - 70
                    target: shell.verticalBar ? verticalNotificationIcon : notificationIcon
                    barEdge: shell.barEdge
                    surfaceColor: shell.barBackground()
                    foreground: shell.fg
                    background: shell.workspaceMenuBg
                    accent: shell.activeBg
                }

                PluginPanel {
                    id: pluginPanel
                    target: notificationIcon
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                }
                function openPluginPanel(plugin, panel, target) {
                    var entry = PluginRegistry.entries.find(entry => entry.plugin === plugin && entry.id === panel && entry.kind === "panels");
                    if (!entry) return;
                    pluginPanel.target = target;
                    pluginPanel.entry = entry;
                    showPanel(pluginPanel);
                }
                ControlCenter {
                    id: controlCenter
                    screenMargins: shell.screenGaps
                    target: barContents
                    surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    service: notificationsService
                    wifiControl: networkOwner; bluetoothControl: bluetoothMenu; displayControl: brightnessMenu
                    keyboardControl: keyboardMenu
                    wifiGlyph: shell.verticalBar ? verticalWifiIcon.text : wifiIcon.text
                    battery: shell.battery; mediaPlayer: mediaStrip.player
                    idleEnabled: shell.idleLockEnabled; idleBusy: toggleIdleLock.running
                    barPosition: shell.barEdge; appearance: shell.barAppearance; layout: shell.barLayout; barScreens: shell.barScreens; barAutoHide: shell.barAutoHide; barDock: shell.barDock; mediaStyle: shell.barMediaStyle; clockFormat: shell.barClock; workspaceStyle: shell.workspaceStyle
                    onIdleToggleRequested: if (!toggleIdleLock.running) toggleIdleLock.running = true
                    onLockRequested: runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")])
                    onSettingRequested: function(key, value) { shell.updateBarSetting(key, value); }
                    onWorkspaceStyleRequested: function(value) { shell.setWorkspaceStyle(value); }
                    onPanelRequested: function(kind) { panelIpc.show(kind); }
                    onPickerRequested: function(kind) { runAfterClose(["bash", Quickshell.shellDir + "/scripts/appearance-picker.sh", kind]); }
                }
                MediaMenu {
                    id: mediaMenu
                    target: shell.verticalBar ? verticalCalendarIcon : mediaStrip
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    player: mediaStrip.player
                }
                BatteryMenu {
                    id: batteryMenu
                    target: shell.verticalBar ? verticalBatteryIcon : batteryBarIcon
                    barEdge: shell.barEdge; surfaceColor: shell.barBackground()
                    foreground: shell.fg; background: shell.workspaceMenuBg; accent: shell.activeBg
                    battery: shell.battery; displayControl: brightnessMenu
                }
                function showControlCenter(page) {
                    // Accept the System and Capture aliases for Settings and Tools.
                    page = ({system: "settings", capture: "tools"})[page] || page;
                    if (["general", "plugins", "style", "tools", "settings"].indexOf(page) === -1) return;
                    controlCenter.page = page;
                    showPanel(controlCenter);
                }
                function toggleControlCenter() { togglePanel(controlCenter); }
                function showKind(kind) {
                    var panels = {wifi: wifiMenu, bluetooth: bluetoothMenu, brightness: brightnessMenu, display: brightnessMenu, volume: volumeMenu,
                        mic: volumeMenu, tailscale: tailscaleMenu, streaming: streamingMenu, keyboard: keyboardMenu, calendar: calendarMenu,
                        weather: weatherMenu, hardware: hardwareMenu, ai: aiMenu, obs: obsMenu,
                        workspace: workspaceMenu, recording: recordingMenu, notifications: notificationCenter,
                        center: controlCenter, media: mediaMenu, battery: batteryMenu};
                    if (kind === "overview") { toggleOverview(); return; }
                    if (!panels[kind]) return;
                    if (kind === "mic" || kind === "volume") volumeMenu.microphone = kind === "mic";
                    showPanel(panels[kind]);
                }
                function inspectPanels() {
                    return JSON.stringify(dockPanels.map(panel => ({name: panel.toString(), visible: panel.visible,
                        x: panel.x, y: panel.y, width: panel.width, height: panel.height,
                        progress: panel.revealProgress, opened: panel.opened, screen: bar.modelData.name,
                        parent: String(panel.parent), host: String(panel.hostWindow)})));
                }
                Component.onCompleted: shell.registerBar(bar)
                Component.onDestruction: shell.unregisterBar(bar)

                // The main bar receives shortcuts and forwards them to the bar of the display in use.
                IpcHandler {
                    enabled: bar.isMainBar
                    target: "controlCenter"
                    function toggle(): void { shell.activeBar(bar).toggleControlCenter(); }
                    function show(page: string): void { shell.activeBar(bar).showControlCenter(page); }
                }

                IpcHandler {
                    id: panelIpc
                    enabled: bar.isMainBar
                    target: "panels"
                    function inspect(): string { return shell.activeBar(bar).inspectPanels(); }
                    function close(): void { shell.activeBar(bar).closePanels(); }
                    function show(kind: string): void { shell.activeBar(bar).showKind(kind); }
                }

                anchors {
                    top: shell.barEdge === "top" || shell.verticalBar
                    bottom: shell.barEdge === "bottom" || shell.verticalBar
                    left: shell.barEdge === "top" || shell.barEdge === "bottom" || shell.barEdge === "left"
                    right: shell.barEdge === "top" || shell.barEdge === "bottom" || shell.barEdge === "right"
                }

                Shape {
                    id: centeredOutline
                    visible: shell.centeredLayout && !FocusMode.enabled
                    readonly property real slope: bar.normalThickness + shell.tabBendRound
                    x: barContents.x - (shell.verticalBar ? 0 : slope) + (shell.verticalBar ? (shell.barEdge === "left" ? -1 : 1) * bar.normalThickness * (1 - autoHide.progress) : 0)
                    y: barContents.y - (shell.verticalBar ? slope : 0) + (!shell.verticalBar ? (shell.barEdge === "top" ? -1 : 1) * bar.normalThickness * (1 - autoHide.progress) : 0)
                    width: barContents.width + (shell.verticalBar ? 0 : 2 * slope)
                    height: barContents.height + (shell.verticalBar ? 2 * slope : 0)
                    HoverHandler { id: centeredHover }
                    BarGestureArea {
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }
                    antialiasing: true
                    ShapePath {
                        strokeWidth: -1
                        fillColor: shell.barBackground()
                        PathSvg { path: EdgeSlopes.outline(shell.barEdge,
                            shell.verticalBar ? centeredOutline.height : centeredOutline.width,
                            bar.normalThickness, 0, shell.tabBendRound,
                            [[centeredOutline.slope, (shell.verticalBar ? centeredOutline.height : centeredOutline.width) - centeredOutline.slope]]) }
                    }
                }

                Item {
                    id: barContents
                    visible: !FocusMode.enabled
                    transform: Translate {
                        x: shell.verticalBar ? (shell.barEdge === "left" ? -1 : 1) * (bar.normalThickness + (shell.islandsLayout ? bar.islandGap : 0)) * (1 - autoHide.progress) : 0
                        y: !shell.verticalBar ? (shell.barEdge === "top" ? -1 : 1) * (bar.normalThickness + (shell.islandsLayout ? bar.islandGap : 0)) * (1 - autoHide.progress) : 0
                    }
                    width: shell.verticalBar ? bar.thinThickness : (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.width)
                    height: shell.verticalBar ? (bar.centeredLayout ? bar.centerExtent + bar.leadingReveal + bar.trailingReveal : bar.height) : bar.thinThickness
                    x: shell.verticalBar ? (shell.barEdge === "right" ? bar.width - width - (bar.islandsLayout ? bar.islandGap : 0) : (bar.islandsLayout ? bar.islandGap : 0)) : bar.centeredLayout ? (bar.width - bar.centerExtent) / 2 - bar.leadingReveal : 0
                    y: shell.verticalBar ? (bar.centeredLayout ? (bar.height - bar.centerExtent) / 2 - bar.leadingReveal : 0) : (shell.barEdge === "bottom" ? bar.height - height - (bar.islandsLayout ? bar.islandGap : 0) : (bar.islandsLayout ? bar.islandGap : 0))
                    clip: bar.centeredLayout
                    Item {
                        id: tabStrip
                        visible: shell.notchLayout
                        width: shell.verticalBar ? shell.tabStripThickness : parent.width
                        height: shell.verticalBar ? parent.height : shell.tabStripThickness
                        x: shell.barEdge === "right" ? parent.width - width : 0
                        y: shell.barEdge === "bottom" ? parent.height - height : 0
                    }
                    TabSurface { id: leadingTab; start: 0; end: bar.tabLeadingEnd }
                    TabSurface { id: notchTab; start: bar.tabCenterStart; end: bar.tabCenterEnd }
                    TabSurface { id: trailingTab; start: bar.tabTrailingStart; end: shell.verticalBar ? barContents.height : barContents.width }
                    component TabSurface: Item {
                        property real start
                        property real end
                        readonly property string barEdge: shell.barEdge
                        readonly property real revealProgress: 1
                        readonly property bool detached: false
                        visible: shell.notchLayout
                        width: shell.verticalBar ? bar.normalThickness - shell.tabStripThickness : end - start
                        height: shell.verticalBar ? end - start : bar.normalThickness - shell.tabStripThickness
                        x: shell.verticalBar ? (shell.barEdge === "right" ? 0 : shell.tabStripThickness) : start
                        y: shell.verticalBar ? start : (shell.barEdge === "bottom" ? 0 : shell.tabStripThickness)

                    }
                    Shape {
                        id: tabsOutline
                        anchors.fill: parent
                        visible: shell.notchLayout
                        antialiasing: true
                        // One alpha silhouette also defines Hyprland's blur coverage.
                        ShapePath {
                            strokeWidth: -1
                            fillColor: shell.barBackground()
                            PathSvg { path: {
                                return EdgeSlopes.outline(shell.barEdge,
                                    shell.verticalBar ? tabsOutline.height : tabsOutline.width,
                                    bar.normalThickness, shell.tabStripThickness, shell.tabBendRound,
                                    [[0, bar.tabLeadingEnd], [bar.tabCenterStart, bar.tabCenterEnd], [bar.tabTrailingStart, shell.verticalBar ? tabsOutline.height : tabsOutline.width]]);
                            } }
                        }
                    }
                    HoverHandler {
                        id: barHover
                        // The bar's own handler also sees the pointer over the clock and the weather,
                        // whose mouse areas would hide it from a separate hover box behind them.
                        readonly property bool overCenterTab: {
                            if (!hovered || !bar.notchLayout) return false;
                            var along = shell.verticalBar ? point.position.y : point.position.x;
                            return along >= bar.tabCenterStart && along <= bar.tabCenterEnd;
                        }
                        onOverCenterTabChanged: {
                            if (overCenterTab) { weatherCollapseDelay.stop(); bar.weatherHovered = true; }
                            else weatherCollapseDelay.restart();
                        }
                    }

                PanelWindow {
                    screen: bar.screen
                    visible: shell.dragCandidate !== ""
                    color: "transparent"
                    exclusionMode: ExclusionMode.Ignore
                    WlrLayershell.namespace: "desktop-bar-edge-preview"
                    WlrLayershell.layer: WlrLayer.Overlay
                    mask: Region {}
                    anchors { top: true; bottom: true; left: true; right: true }
                    Rectangle {
                        readonly property bool vertical: shell.dragCandidate === "left" || shell.dragCandidate === "right"
                        x: shell.dragCandidate === "right" ? parent.width - width : 0
                        y: shell.dragCandidate === "bottom" ? parent.height - height : 0
                        width: vertical ? shell.barHeight : parent.width
                        height: vertical ? parent.height : shell.barHeight
                        radius: DesktopStyle.radius(6)
                        color: Qt.alpha(shell.workspaceMenuBg, 0.65)
                        border.width: 1
                        border.color: shell.activeBg
                    }
                }

                Item {
                    id: islandSurfaces
                    visible: !FocusMode.enabled
                    anchors.fill: parent
                    IslandSurface { first: shell.verticalBar ? verticalControlCenterLogo : controlCenterLogo }
                    IslandSurface { first: shell.verticalBar ? verticalOverviewIcon : overviewIcon; last: shell.verticalBar ? verticalWorkspaces : workspaces }
                    IslandSurface { first: shell.verticalBar ? verticalHardware : hardwareStatus }
                    IslandSurface { first: shell.verticalBar ? verticalCalendarIcon : centerInfo }
                    IslandSurface { first: shell.verticalBar ? verticalWeatherIcon : barWeather }
                    IslandSurface { first: shell.verticalBar ? verticalMedia : mediaStrip; shown: shell.verticalBar ? verticalMedia.visible : mediaStrip.visible }
                    IslandSurface { first: shell.verticalBar ? verticalCapture : barCapture; shown: shell.verticalBar ? verticalCapture.shown : barCapture.shown }
                    IslandSurface { first: shell.verticalBar ? verticalEnd : rightSide; last: shell.verticalBar ? verticalEnd : notificationIcon }
                }
                component IslandSurface: Rectangle {
                    required property Item first
                    property Item last: first
                    property bool shown: true
                    visible: bar.islandsLayout && shown
                    readonly property point leading: itemPosition(first)
                    readonly property point trailing: itemPosition(last)
                    function itemPosition(item) {
                        var horizontal = 0;
                        var vertical = 0;
                        while (item && item !== barContents) {
                            horizontal += item.x;
                            vertical += item.y;
                            item = item.parent;
                        }
                        return Qt.point(horizontal, vertical);
                    }
                    x: shell.verticalBar ? 0 : leading.x - 4
                    y: shell.verticalBar ? leading.y - 4 : 0
                    width: shell.verticalBar ? bar.normalThickness : trailing.x + last.width - leading.x + 8
                    height: shell.verticalBar ? trailing.y + last.height - leading.y + 8 : bar.normalThickness
                    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                    color: shell.barBackground()
                    BarGestureArea {
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }
                }

                BarSection {
                    id: verticalSurface
                    anchors.fill: parent
                    visible: shell.verticalBar
                    edge: shell.barEdge
                    background: shell.notchLayout || shell.centeredLayout || shell.islandsLayout ? "transparent" : shell.barBackground()
                    radius: 0

                    BarGestureArea {
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }

                    Column {
                        id: verticalStart
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
                        y: bar.islandsLayout ? shell.screenGaps[0] + 4 : bar.centeredLayout ? bar.endPadding : 8
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: shell.workspaceItemSpacing
                        Column {
                            id: verticalWorkspaces
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: shell.workspaceItemSpacing
                            EitrLogo {
                                id: verticalControlCenterLogo
                                foreground: shell.fg; background: shell.workspaceMenuBg
                                slotWidth: shell.workspaceItemSize
                                anchors.horizontalCenter: parent.horizontalCenter
                                onClicked: bar.toggleControlCenter()
                            }
                            Item { width: 1; height: bar.islandsLayout ? bar.islandSpacing - 2 * shell.workspaceItemSpacing : 0; visible: bar.islandsLayout }
                            VerticalBarIcon { id: verticalOverviewIcon; icon: "󰕮"; tooltip: Eitr.I18n.tr("Overview"); open: true; clickable: true; onClicked: bar.toggleOverview() }
                            Repeater {
                                model: shell.workspaceCount
                                BarButton {
                                    text: shell.workspaceLabel(index, bar.screen)
                                    tooltip: active ? "" : shell.workspaceApps(index + 1)
                                    visualStyle: shell.workspaceStyle
                                    active: shell.workspaceActive(index + 1, bar.screen)
                                    width: shell.workspaceItemSize; buttonHeight: shell.workspaceItemSize; fontSize: 14; cornerRadius: 6; textOffsetY: 0
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    onClicked: shell.focusWorkspace(index + 1)
                                    onRightClicked: bar.togglePanel(workspaceMenu)
                                }
                            }
                        }
                        Item { width: 1; height: bar.islandsLayout ? bar.islandSpacing - 2 * shell.workspaceItemSpacing : 0; visible: bar.islandsLayout }
                        Column {
                            id: verticalHardware
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: shell.workspaceItemSpacing
                            VerticalBarIcon { id: verticalAiIcon; icon: ""; iconSize: 16; tooltip: Eitr.I18n.tr("AI Usage"); open: true; clickable: true; onClicked: bar.togglePanel(aiMenu) }
                            VerticalBarIcon { id: verticalHardwareIcon; icon: "󰍛"; iconSize: 18; tooltip: Eitr.I18n.tr("Hardware"); open: true; clickable: true; onClicked: bar.togglePanel(hardwareMenu) }
                            VerticalBarIcon { id: verticalIdleLockIcon; icon: shell.idleLockGlyph; iconSize: 17; tooltip: shell.idleLockTooltip; open: true; clickable: true; onClicked: shell.switchIdleLock() }
                        }
                    }

                    Item {
                        id: verticalMiddle
                        anchors.alignWhenCentered: false
                        anchors.horizontalCenterOffset: 0
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: bar.centeredLayout ? (bar.leadingReveal - bar.trailingReveal) / 2 : 0
                        width: parent.width
                        height: 40
                        Column {
                            id: verticalMedia
                            anchors.horizontalCenterOffset: 0
                            anchors.bottom: bar.centeredLayout ? verticalPin.top : verticalCapture.top
                            anchors.bottomMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: bar.centeredLayout ? bar.itemGap : 2
                            visible: mediaStrip.player !== null && bar.expanded
                            MediaIndicator {
                                anchors.horizontalCenter: parent.horizontalCenter
                                rotation: 90
                                style: shell.barMediaStyle
                                playing: mediaStrip.playing
                                active: shell.barVisible && shell.verticalBar && bar.expanded
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                                title: mediaStrip.title
                                onDetailsRequested: bar.togglePanel(mediaMenu)
                            }
                            VerticalBarIcon {
                                icon: "󰒮"; tooltip: Eitr.I18n.tr("Previous"); open: true
                                clickable: !!mediaStrip.player && mediaStrip.player.canGoPrevious
                                onClicked: mediaStrip.player.previous()
                            }
                            VerticalBarIcon {
                                icon: mediaStrip.playing ? "󰏤" : "󰐊"; tooltip: mediaStrip.title; open: true
                                clickable: !!mediaStrip.player && mediaStrip.player.canTogglePlaying
                                onClicked: mediaStrip.player.togglePlaying()
                            }
                            VerticalBarIcon {
                                icon: "󰒭"; tooltip: Eitr.I18n.tr("Next"); open: true
                                clickable: !!mediaStrip.player && mediaStrip.player.canGoNext
                                onClicked: mediaStrip.player.next()
                            }
                            VerticalBarIcon {
                                icon: "󰝚"; tooltip: Eitr.I18n.tr("Media"); open: true; clickable: true
                                onClicked: bar.togglePanel(mediaMenu)
                            }
                        }
                        CaptureIndicator {
                            id: verticalCapture
                            anchors.bottom: verticalCalendarIcon.top
                            anchors.horizontalCenterOffset: 0
                            anchors.bottomMargin: shown ? (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3) : 0
                            anchors.horizontalCenter: parent.horizontalCenter
                            height: shown ? 24 : 0
                            recording: obsMenu.obsState.recording || obsMenu.obsState.streaming
                            recordingPaused: obsMenu.obsState.paused && !obsMenu.obsState.streaming
                            streaming: obsMenu.obsState.streaming
                            dictating: shell.dictating
                            transcribing: shell.transcribing
                            dictationLevels: shell.dictationLevels
                            onRecordingClicked: bar.togglePanel(recordingMenu)
                        }
                        VerticalBarIcon {
                            id: verticalPin
                            anchors.horizontalCenterOffset: 0
                            anchors.bottom: verticalCapture.top
                            anchors.bottomMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3
                            anchors.horizontalCenter: parent.horizontalCenter
                            icon: shell.barPinned ? "󰐃" : "󰐄"
                            tooltip: shell.barPinned ? Eitr.I18n.tr("Unpin bar") : Eitr.I18n.tr("Pin bar open")
                            visible: bar.centeredLayout && bar.expanded
                            open: true; clickable: true
                            onClicked: shell.updateBarSetting("pinned", shell.barPinned ? "no" : "yes")
                        }
                        ClockButton {
                            id: verticalCalendarIcon
                            anchors.centerIn: parent
                            compact: true
                            onClicked: bar.togglePanel(calendarMenu)
                        }
                        Item {
                            anchors.top: verticalCalendarIcon.bottom
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: parent.width
                            height: bar.notchLayout ? bar.weatherReveal : (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 3) + verticalWeatherIcon.height
                            clip: bar.notchLayout
                            WeatherWidget {
                                id: verticalWeatherIcon
                                visible: bar.expanded
                                enabled: !bar.notchLayout || bar.weatherExpanded
                                y: parent.height - height
                                anchors.horizontalCenter: parent.horizontalCenter
                                autoRefresh: false
                                compact: true
                                text: barWeather.text
                                temp: barWeather.temp
                                onClicked: bar.togglePanel(weatherMenu)
                            }
                        }
                    }

                    Column {
                        id: verticalEnd
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: bar.islandsLayout ? shell.screenGaps[2] + 4 : bar.centeredLayout ? bar.endPadding : 8
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: shell.workspaceItemSpacing
                        VerticalBarIcon {
                            icon: shell.statusOpen ? "⌄" : "⌃"
                            visible: !bar.centeredLayout && !shell.notchLayout
                            tooltip: shell.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")
                            open: true; clickable: true
                            onClicked: shell.statusOpen = !shell.statusOpen
                        }
                        PluginBarItems {
                            foreground: shell.fg; background: shell.barBackground(); accent: shell.activeBg
                            vertical: true; open: shell.iconsOpen; slotSize: shell.workspaceItemSize; slotSpacing: shell.workspaceItemSpacing
                            onPanelRequested: function(plugin, panel, target) { bar.openPluginPanel(plugin, panel, target); }
                        }
                        StatusCommand {
                            id: verticalWifiIcon
                            text: shell.wifiGlyph
                            hoverLabel: "WiFi"; fontSize: 16
                            open: shell.iconsOpen; height: open ? 24 : 0; fixedWidth: 56; clickable: true
                            anchors.horizontalCenter: parent.horizontalCenter
                            onClicked: bar.togglePanel(wifiMenu)
                            onOpenChanged: if (!open) wifiMenu.opened = false
                        }
                        VerticalBarIcon { id: verticalBluetoothIcon; icon: "󰂯"; tooltip: Eitr.I18n.tr("Bluetooth"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(bluetoothMenu); onOpenChanged: if (!open) bluetoothMenu.opened = false }
                        VerticalBarIcon { id: verticalDisplayIcon; icon: "󰍹"; tooltip: Eitr.I18n.tr("Display"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(brightnessMenu); onOpenChanged: if (!open) brightnessMenu.opened = false }
                        VerticalBarIcon { id: verticalVolumeIcon; icon: "\u{F02CE}"; tooltip: Eitr.I18n.tr("Audio/Mic"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(volumeMenu); onOpenChanged: if (!open) volumeMenu.opened = false }
                        VerticalBarIcon { id: verticalTailscaleIcon; visible: remoteAccessService.allowed; icon: "󰌘"; tooltip: "Tailscale"; open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(tailscaleMenu); onOpenChanged: if (!open) tailscaleMenu.opened = false }
                        VerticalBarIcon { id: verticalStreamingIcon; visible: remoteAccessService.allowed; icon: "󰢹"; tooltip: Eitr.I18n.tr("Streaming"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(streamingMenu); onOpenChanged: if (!open) streamingMenu.opened = false }
                        VerticalBarIcon { id: verticalObsIcon; icon: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? "󰏤" : "󰑋") : "󰻂"; iconSize: obsMenu.obsState.recording && !obsMenu.obsState.paused ? 22 : 16; tooltip: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? Eitr.I18n.tr("Recording paused") : Eitr.I18n.tr("Recording")) : Eitr.I18n.tr("OBS Studio"); open: shell.iconsOpen; clickable: true; onClicked: bar.togglePanel(obsMenu); onOpenChanged: if (!open) obsMenu.opened = false }
                        VerticalBarIcon { id: verticalKeyboardIcon; icon: keyboardMenu.activeCode || "󰌌"; iconSize: 11; tooltip: keyboardMenu.activeLabel ? Eitr.I18n.tr("Keyboard · {layout}", {layout: keyboardMenu.activeLabel}) : Eitr.I18n.tr("Keyboard"); open: shell.iconsOpen && keyboardMenu.layouts.length > 1; clickable: true; onClicked: bar.togglePanel(keyboardMenu); onOpenChanged: if (!open) keyboardMenu.opened = false }
                        VerticalBarIcon {
                            id: verticalUpdatesIcon
                            icon: shell.updatesIcon; iconSize: 17; spinning: shell.updates.checking
                            tooltip: shell.updatesTooltip; open: shell.iconsOpen
                            clickable: true; rightClickable: true
                            onClicked: function(button) { if (button === Qt.RightButton) shell.checkUpdates(); else shell.openSystemUpdate(); }
                        }
                        VerticalBarIcon { id: verticalBatteryIcon; icon: shell.batteryIcon; tooltip: Math.round(shell.battery.percent) + "% · " + shell.battery.status; open: shell.battery.available; visible: shell.battery.available; clickable: true; onClicked: bar.togglePanel(batteryMenu) }
                        VerticalBarIcon {
                            id: verticalNotificationIcon
                            icon: notificationIcon.text; tooltip: Eitr.I18n.tr("Notifications"); open: true; clickable: true
                            onClicked: bar.togglePanel(notificationCenter)
                        }
                    }
                }

                BarSection {
                    id: surface
                    anchors.fill: parent
                    visible: !shell.verticalBar
                    edge: shell.barEdge
                    background: shell.notchLayout || shell.centeredLayout || shell.islandsLayout ? "transparent" : shell.barBackground()
                    radius: 0


                    BarGestureArea {
                        id: barGestures
                        anchors.fill: parent
                        hostWindow: bar
                        edge: shell.barEdge
                        onCandidateChanged: shell.dragCandidate = candidate
                        onPointerHeld: function(held) { shell.barPointerHeld = held }
                        onDoubleTapped: function(button) { shell.barDoubleClick(button) }
                        onDropped: function(edge) { shell.updateBarSetting("edge", edge) }
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: bar.islandsLayout ? shell.screenGaps[3] + 4 : bar.centeredLayout ? bar.endPadding : 12
                        anchors.rightMargin: 9
                        spacing: 0

                        Row {
                            id: workspaces
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded
                            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }

                            spacing: shell.workspaceItemSpacing
                            Layout.alignment: Qt.AlignVCenter

                            EitrLogo {
                                id: controlCenterLogo
                                foreground: shell.fg; background: shell.workspaceMenuBg
                                slotWidth: shell.workspaceItemSize
                                anchors.verticalCenter: parent.verticalCenter
                                onClicked: bar.toggleControlCenter()
                            }
                            Item { width: bar.islandsLayout ? bar.islandSpacing - 2 * shell.workspaceItemSpacing : 0; height: 1; visible: bar.islandsLayout }
                            StatusIcon {
                                id: overviewIcon
                                icon: "󰕮"; tooltip: Eitr.I18n.tr("Overview"); open: true; clickable: true
                                slotWidth: shell.workspaceItemSize
                                anchors.verticalCenter: parent.verticalCenter
                                onClicked: bar.toggleOverview()
                            }
                            Repeater {
                                model: shell.workspaceCount

                                BarButton {
                                    text: shell.workspaceLabel(index, bar.screen)
                                    tooltip: active ? "" : shell.workspaceApps(index + 1)
                                    visualStyle: shell.workspaceStyle
                                    active: shell.workspaceActive(index + 1, bar.screen)
                                    width: shell.workspaceItemSize
                                    buttonHeight: shell.workspaceItemSize
                                    anchors.verticalCenter: parent.verticalCenter
                                    fontSize: 14
                                    cornerRadius: 6
                                    textOffsetY: 0
                                    onClicked: shell.focusWorkspace(index + 1)
                                    onRightClicked: bar.togglePanel(workspaceMenu)
                                }

                            }

                            WorkspaceStyleMenu {
                                id: workspaceMenu
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalWorkspaces : workspaces
                                barEdge: shell.barEdge
                                currentStyle: shell.workspaceStyle
                                accent: shell.activeBg
                                foreground: shell.workspaceMenuFg
                                background: shell.workspaceMenuBg
                                selectedForeground: shell.activeFg
                                onSelected: function(style) {
                                    shell.setWorkspaceStyle(style);
                                }
                            }

                        }

                        Row {
                            id: hardwareStatus
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded
                            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
                            Layout.alignment: Qt.AlignVCenter
                            Layout.leftMargin: bar.islandsLayout ? bar.islandSpacing : shell.workspaceItemSpacing
                            spacing: shell.workspaceItemSpacing

                            StatusIcon {
                                id: aiIcon
                                slotWidth: shell.workspaceItemSize
                                icon: ""
                                iconSize: 16
                                tooltip: Eitr.I18n.tr("AI Usage")
                                open: true
                                clickable: true
                                onClicked: bar.togglePanel(aiMenu)
                            }

                            StatusIcon {
                                id: hardwareIcon
                                slotWidth: shell.workspaceItemSize
                                icon: "󰍛"
                                iconSize: 18
                                tooltip: Eitr.I18n.tr("Hardware")
                                open: true
                                clickable: true
                                onClicked: bar.togglePanel(hardwareMenu)
                            }

                            // A plain switch: a click turns automatic idle locking on or off.
                            StatusIcon {
                                id: idleLockIcon
                                slotWidth: shell.workspaceItemSize
                                icon: shell.idleLockGlyph
                                iconSize: 17
                                tooltip: shell.idleLockTooltip
                                open: true
                                clickable: true
                                onClicked: shell.switchIdleLock()
                            }
                        }

                        SystemMonitorMenu {
                            id: hardwareMenu
                            identity: shell.hardwareIdentity
                            onIdentityReceived: identity => shell.hardwareIdentity = identity
                            surfaceColor: shell.barBackground()
                            maximumHeight: bar.screen.height - 70
                            target: shell.verticalBar ? verticalHardwareIcon : hardwareIcon
                            barEdge: shell.barEdge
                            accent: shell.activeBg
                            foreground: shell.fg
                            background: shell.workspaceMenuBg
                        }

                        AiUsageMenu {
                            id: aiMenu
                            surfaceColor: shell.barBackground()
                            maximumHeight: bar.screen.height - 70
                            leftAligned: true
                            target: shell.verticalBar ? verticalAiIcon : aiIcon
                            barEdge: shell.barEdge
                            accent: shell.activeBg
                            foreground: shell.fg
                            background: shell.workspaceMenuBg
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                    }

                        Row {
                            id: rightSide
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded
                            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }

                            spacing: shell.workspaceItemSpacing
                            anchors.right: notificationIcon.left
                            anchors.rightMargin: shell.workspaceItemSpacing
                            anchors.verticalCenter: parent.verticalCenter

                            StatusIcon {
                                id: statusToggle
                                visible: !bar.centeredLayout && !shell.notchLayout
                                tooltip: shell.statusOpen ? Eitr.I18n.tr("Hide icons") : Eitr.I18n.tr("Show icons")

                                icon: shell.statusOpen ? "›" : "‹"
                                open: true
                                clickable: true
                                iconSize: 21
                                glyphOffsetY: -1
                                onClicked: shell.statusOpen = !shell.statusOpen
                            }

                            PluginBarItems {
                                foreground: shell.fg; background: shell.barBackground(); accent: shell.activeBg
                                open: shell.iconsOpen; slotSize: shell.workspaceItemSize; slotSpacing: shell.workspaceItemSpacing
                                onPanelRequested: function(plugin, panel, target) { bar.openPluginPanel(plugin, panel, target); }
                            }

                            StatusCommand {
                                id: wifiIcon
                                text: shell.wifiGlyph
                                hoverLabel: "WiFi"
                                fontSize: 16
                                open: shell.iconsOpen
                                slotWidth: shell.workspaceItemSize
                                fixedWidth: shell.workspaceItemSize
                                clickable: true
                                onClicked: bar.togglePanel(wifiMenu)
                                onOpenChanged: if (!open) wifiMenu.opened = false
                            }

                            WifiMenu {
                                id: wifiMenu
                                networkService: networkOwner
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalWifiIcon : (shell.iconsOpen ? wifiIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {
                                id: bluetoothIcon
                                icon: "󰂯"
                                tooltip: Eitr.I18n.tr("Bluetooth")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(bluetoothMenu)
                                onOpenChanged: if (!open) bluetoothMenu.opened = false
                            }

                            BluetoothMenu {
                                id: bluetoothMenu
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalBluetoothIcon : (shell.iconsOpen ? bluetoothIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {
                                id: brightnessIcon
                                icon: "󰍹"
                                tooltip: Eitr.I18n.tr("Display")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(brightnessMenu)
                                onOpenChanged: if (!open) brightnessMenu.opened = false
                            }

                            BrightnessMenu {
                                id: brightnessMenu
                                maximumHeight: bar.screen.height - 70
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalDisplayIcon : (shell.iconsOpen ? brightnessIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                                onPrimarySelected: DisplayService.refresh()
                            }

                            StatusIcon {
                                id: volumeIcon
                                icon: "\u{F02CE}"
                                tooltip: Eitr.I18n.tr("Audio/Mic")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(volumeMenu)
                                onOpenChanged: if (!open) volumeMenu.opened = false
                            }

                            AudioMenu {
                                id: volumeMenu
                                surfaceColor: shell.barBackground()
                                maximumHeight: bar.screen.height - 70
                                target: shell.verticalBar ? verticalVolumeIcon : (shell.iconsOpen ? volumeIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {
                                id: tailscaleIcon
                                visible: remoteAccessService.allowed
                                icon: "󰌘"
                                tooltip: "Tailscale"
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(tailscaleMenu)
                                onOpenChanged: if (!open) tailscaleMenu.opened = false
                            }
                            RemoteAccessMenu {
                                id: tailscaleMenu
                                kind: "tailscale"
                                service: remoteAccessService
                                onObservationChanged: observing => shell.remoteObservers += observing ? 1 : -1
                                maximumHeight: bar.screen.height - 70
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalTailscaleIcon : tailscaleIcon
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }
                            StatusIcon {
                                id: streamingIcon
                                visible: remoteAccessService.allowed
                                icon: "󰢹"
                                tooltip: Eitr.I18n.tr("Streaming")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(streamingMenu)
                                onOpenChanged: if (!open) streamingMenu.opened = false
                            }
                            RemoteAccessMenu {
                                id: streamingMenu
                                kind: "streaming"
                                service: remoteAccessService
                                onObservationChanged: observing => shell.remoteObservers += observing ? 1 : -1
                                maximumHeight: bar.screen.height - 70
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalStreamingIcon : streamingIcon
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {
                                id: obsIcon
                                icon: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? "󰏤" : "󰑋") : "󰻂"
                                iconSize: obsMenu.obsState.recording && !obsMenu.obsState.paused ? 22 : 16
                                tooltip: obsMenu.obsState.recording ? (obsMenu.obsState.paused ? Eitr.I18n.tr("Recording paused") : Eitr.I18n.tr("Recording")) : Eitr.I18n.tr("OBS Studio")
                                open: shell.iconsOpen
                                clickable: true
                                onClicked: bar.togglePanel(obsMenu)
                                onOpenChanged: if (!open) obsMenu.opened = false
                            }

                            StatusIcon {
                                id: keyboardIcon
                                // Like macOS's input menu: the active layout's code, shown
                                // only when there is more than one layout to switch between.
                                icon: keyboardMenu.activeCode || "󰌌"
                                iconSize: 11
                                tooltip: keyboardMenu.activeLabel ? Eitr.I18n.tr("Keyboard · {layout}", {layout: keyboardMenu.activeLabel}) : Eitr.I18n.tr("Keyboard")
                                open: shell.iconsOpen && keyboardMenu.layouts.length > 1
                                clickable: true
                                onClicked: bar.togglePanel(keyboardMenu)
                                onOpenChanged: if (!open) keyboardMenu.opened = false
                            }

                            KeyboardLayoutMenu {
                                id: keyboardMenu
                                surfaceColor: shell.barBackground()
                                target: shell.verticalBar ? verticalKeyboardIcon : (shell.iconsOpen ? keyboardIcon : notificationIcon)
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            StatusIcon {
                                id: updatesIcon
                                icon: shell.updatesIcon
                                iconSize: 17
                                spinning: shell.updates.checking
                                tooltip: shell.updatesTooltip
                                open: shell.iconsOpen
                                clickable: true
                                rightClickable: true
                                onClicked: function(button) {
                                    if (button === Qt.RightButton) shell.checkUpdates();
                                    else shell.openSystemUpdate();
                                }
                            }

                            StatusIcon {
                                id: batteryBarIcon
                                icon: shell.batteryIcon
                                tooltip: Math.round(shell.battery.percent) + "% · " + shell.battery.status
                                open: shell.battery.available; visible: shell.battery.available
                                clickable: true; onClicked: bar.togglePanel(batteryMenu)
                            }

                            ObsMenu {
                                id: obsMenu
                                surfaceColor: shell.barBackground()
                                onCaptureStarting: recordingMenu.opened = false
                                target: shell.verticalBar ? verticalObsIcon : obsIcon
                                barEdge: shell.barEdge
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                            RecordingMenu {
                                id: recordingMenu
                                surfaceColor: shell.barBackground()
                                controller: obsMenu
                                target: shell.verticalBar ? verticalCapture : barCapture
                                barEdge: shell.barEdge
                                centered: true
                                accent: shell.activeBg
                                foreground: shell.fg
                                background: shell.workspaceMenuBg
                            }

                        }

                    NotificationWidget {
                        id: notificationIcon
                        onOpenRequested: bar.togglePanel(notificationCenter)
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        visible: !shell.verticalBar
                        anchors.right: parent.right
                        anchors.rightMargin: bar.islandsLayout ? shell.screenGaps[1] + 4 : bar.centeredLayout ? bar.endPadding : 13
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    ClockButton {
                        id: centerInfo
                        anchors.alignWhenCentered: false
                        anchors.centerIn: parent
                        anchors.horizontalCenterOffset: bar.centeredLayout ? (bar.leadingReveal - bar.trailingReveal) / 2 : 0
                        anchors.verticalCenterOffset: 0
                        onClicked: bar.togglePanel(calendarMenu)
                    }

                    CaptureIndicator {
                        id: barCapture
                        anchors.right: centerInfo.left
                        anchors.rightMargin: shown ? (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 6) : 0
                        anchors.verticalCenter: parent.verticalCenter
                        recording: obsMenu.obsState.recording || obsMenu.obsState.streaming
                        recordingPaused: obsMenu.obsState.paused && !obsMenu.obsState.streaming
                        streaming: obsMenu.obsState.streaming
                        dictating: shell.dictating
                        transcribing: shell.transcribing
                        dictationLevels: shell.dictationLevels
                        onRecordingClicked: bar.togglePanel(recordingMenu)
                    }

                    StatusIcon {
                        id: barPin
                        visible: bar.centeredLayout && bar.expanded
                        anchors.right: barCapture.left
                        anchors.rightMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 6
                        anchors.verticalCenter: parent.verticalCenter
                        icon: shell.barPinned ? "󰐃" : "󰐄"
                        tooltip: shell.barPinned ? Eitr.I18n.tr("Unpin bar") : Eitr.I18n.tr("Pin bar open")
                        open: true; clickable: true
                        onClicked: shell.updateBarSetting("pinned", shell.barPinned ? "no" : "yes")
                    }

                    MediaStrip {
                        id: mediaStrip
                        mediaStyle: shell.barMediaStyle
                        audioEnabled: shell.barVisible && !shell.verticalBar && bar.expanded
                        opacity: bar.expanded ? 1 : 0
                        enabled: bar.expanded
                        anchors.right: bar.centeredLayout ? barPin.left : barCapture.left
                        anchors.rightMargin: bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 12
                        anchors.verticalCenter: parent.verticalCenter
                        itemSpacing: bar.centeredLayout ? bar.itemGap : 1
                        indicatorSpacing: bar.centeredLayout ? bar.itemGap : 6
                        availableWidth: bar.centeredLayout
                            ? Math.max(0, bar.width / 2 - centerInfo.width / 2 - workspaces.width - hardwareStatus.width - barPin.width - barCapture.width - bar.itemGap * (barCapture.shown ? 5 : 4) - bar.endPadding)
                            : Math.max(0, centerInfo.x - hardwareStatus.mapToItem(centerInfo.parent, hardwareStatus.width, 0).x - (bar.islandsLayout ? 2 * bar.islandSpacing + (barCapture.shown ? barCapture.width + bar.islandSpacing : 0) : 24))
                        foreground: shell.fg
                        background: shell.workspaceMenuBg
                        onDetailsRequested: bar.togglePanel(mediaMenu)
                    }

                    Item {
                        anchors.left: centerInfo.right
                        anchors.verticalCenter: centerInfo.verticalCenter
                        width: bar.notchLayout ? bar.weatherReveal : (bar.islandsLayout ? bar.islandSpacing : bar.centeredLayout ? bar.itemGap : 6) + barWeather.width
                        height: barWeather.height
                        clip: bar.notchLayout
                        WeatherWidget {
                            id: barWeather
                            x: parent.width - width
                            opacity: bar.expanded ? 1 : 0
                            enabled: bar.expanded && (!bar.notchLayout || bar.weatherExpanded)
                            onClicked: bar.togglePanel(weatherMenu)
                        }
                    }

                    CalendarMenu {
                        id: calendarMenu
                        surfaceColor: shell.barBackground()
                        target: shell.verticalBar ? verticalCalendarIcon : centerInfo
                        barEdge: shell.barEdge
                        centered: true
                        accent: shell.activeBg
                        foreground: shell.fg
                        background: shell.workspaceMenuBg
                    }

                    WeatherMenu {
                        id: weatherMenu
                        surfaceColor: shell.barBackground()
                        defaultWeatherData: barWeather.latestData
                        target: shell.verticalBar ? verticalWeatherIcon : centerInfo
                        barEdge: shell.barEdge
                        centered: true
                        accent: shell.activeBg
                        foreground: shell.fg
                        background: shell.workspaceMenuBg
                        onDefaultWeatherUpdated: function(data) { barWeather.updateData(data); }
                    }

                }

                }

            }

        }

    }

    component BarButton: Rectangle {
        id: button

        property string text: ""
        property string tooltip: ""
        property bool active: false
        property int fontSize: 15
        property int buttonHeight: 24
        property int cornerRadius: 7
        property int textOffsetY: 0
        property string visualStyle: "Runes"

        signal clicked()
        signal rightClicked()

        width: 24
        height: buttonHeight
        radius: DesktopStyle.radius(cornerRadius)
        color: visualStyle === "Numbers" || visualStyle === "Runes" ? (!active && mouse.containsMouse ? shell.hoverBg : "transparent") : "transparent"

        WorkspaceMarker {
            anchors.fill: parent
            style: button.visualStyle
            label: button.text
            active: button.active
            accent: shell.activeBg
            foreground: shell.fg
            selectedForeground: shell.activeFg
            fontSize: button.fontSize
            textOffsetY: button.textOffsetY
        }


        MouseArea {
            id: mouse

            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            cursorShape: Qt.PointingHandCursor
            onEntered: Hyprland.refreshToplevels()
            onClicked: function(event) {
                if (event.button === Qt.RightButton) button.rightClicked();
                else button.clicked();
            }
        }

        BarTooltip {
            target: button
            hovered: mouse.containsMouse && !button.active
            text: button.tooltip
            foreground: shell.fg
            background: shell.workspaceMenuBg
        }

        Behavior on color {
            ColorAnimation {
                duration: DesktopStyle.motionDuration(120)
            }

        }

    }

    component StatusIcon: Item {
        id: item

        property string icon: ""
        // An SVG drawn instead of the glyph, tinted with the bar's foreground.
        property url iconSource: ""
        property string tooltip: ""
        property bool open: true
        property bool clickable: false
        property bool rightClickable: false
        property int iconSize: 15
        property int glyphOffsetY: 0
        property int slotWidth: shell.workspaceItemSize
        property bool spinning: false

        signal clicked(int button)

        width: open ? slotWidth : 0
        height: 24
        opacity: open ? 1 : 0
        clip: true

        Row {
            id: content

            anchors.centerIn: parent
            spacing: 3
            leftPadding: 4
            rightPadding: 4

            Image {
                visible: item.iconSource != ""
                anchors.verticalCenter: parent.verticalCenter
                width: item.iconSize; height: item.iconSize
                source: item.iconSource
                // Drawn at its shown size: scaling a larger render down leaves jagged edges.
                sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio), Math.ceil(height * Screen.devicePixelRatio))
                smooth: true
                layer.enabled: visible
                layer.effect: MultiEffect { colorization: 1; colorizationColor: shell.fg }
            }
            Text {
                id: glyph
                visible: item.iconSource == ""
                text: item.icon
                y: item.glyphOffsetY
                color: shell.fg
                font.family: DesktopFonts.family
                font.pixelSize: item.iconSize
                font.bold: true

                // Spin around the glyph's drawn centre; the text box centre sits above it.
                transform: Rotation {
                    id: spin
                    origin.x: glyphInk.tightBoundingRect.x + glyphInk.tightBoundingRect.width / 2
                    origin.y: glyph.baselineOffset + glyphInk.tightBoundingRect.y + glyphInk.tightBoundingRect.height / 2

                    NumberAnimation on angle {
                        running: !DesktopStyle.reduceMotion && (item.spinning)
                        from: 0; to: 360
                        duration: 1200
                        loops: Animation.Infinite
                        onStopped: spin.angle = 0
                    }
                }

                TextMetrics {
                    id: glyphInk
                    font: glyph.font
                    text: glyph.text
                }
            }

        }

        MouseArea {
            id: iconMouse
            anchors.fill: parent
            enabled: item.open && item.clickable
            acceptedButtons: item.rightClickable ? Qt.LeftButton | Qt.RightButton : Qt.LeftButton
            hoverEnabled: true
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: function(event) { item.clicked(event.button); }
        }

        BarTooltip {
            background: shell.workspaceMenuBg
            foreground: shell.fg
            target: item
            hovered: iconMouse.containsMouse && item.open
            text: item.tooltip
        }

        Behavior on width {
            NumberAnimation {
                duration: DesktopStyle.motionDuration(180)
                easing.type: Easing.InOutCubic
            }

        }

        Behavior on opacity {
            NumberAnimation {
                duration: DesktopStyle.motionDuration(120)
                easing.type: Easing.InOutCubic
            }

        }

    }

    component VerticalBarIcon: StatusIcon {
        anchors.horizontalCenter: parent.horizontalCenter
        height: open ? 24 : 0
    }

    component StatusCommand: Item {
        id: item

        property string hoverLabel: ""
        property bool clickable: false
        signal clicked()
        property bool open: true
        property string text: ""
        property int slotWidth: 44
        property int fixedWidth: 0
        property int fontSize: 13

        width: open ? (fixedWidth > 0 ? fixedWidth : Math.max(slotWidth, label.implicitWidth + 8)) : 0
        height: 24
        opacity: open ? 1 : 0
        clip: true

        Text {
            id: label

            anchors.centerIn: parent
            text: item.text
            textFormat: Text.RichText
            color: shell.fg
            font.family: DesktopFonts.family
            font.pixelSize: item.fontSize
            font.bold: true
        }

        MouseArea {
            id: commandMouse
            anchors.fill: parent
            enabled: item.open && item.clickable
            hoverEnabled: true
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: item.clicked()
        }

        BarTooltip {
            background: shell.workspaceMenuBg
            foreground: shell.fg
            target: item
            hovered: commandMouse.containsMouse && item.open
            text: item.hoverLabel
        }
        Behavior on width {
            NumberAnimation {
                duration: DesktopStyle.motionDuration(180)
                easing.type: Easing.InOutCubic
            }

        }

        Behavior on opacity {
            NumberAnimation {
                duration: DesktopStyle.motionDuration(120)
                easing.type: Easing.InOutCubic
            }

        }
    }

    // OBS recording or streaming, and dictation (SUPER+D): a red dot or the
    // microphone's level bars just before the clock. Hidden, it takes no space.
    component CaptureIndicator: Item {
        id: capture
        signal recordingClicked()
        property bool recording: false
        property bool recordingPaused: false
        property bool streaming: false
        property bool dictating: false
        property bool transcribing: false
        property var dictationLevels: [0, 0, 0, 0]
        readonly property bool listening: dictating || transcribing
        readonly property bool shown: recording || listening
        property real transcribePhase: 0
        NumberAnimation on transcribePhase {
            running: !DesktopStyle.reduceMotion && (capture.transcribing)
            from: 0; to: 1; duration: 900; loops: Animation.Infinite
        }
        width: shown ? recordingDot.width : 0
        height: 24
        Item {
            id: recordingDot
            visible: capture.shown
            width: 22
            height: 24
            Rectangle {
                visible: !capture.listening
                anchors.right: parent.right
                anchors.rightMargin: 2
                anchors.verticalCenter: parent.verticalCenter
                width: 6
                height: 6
                radius: 3
                color: capture.recordingPaused ? shell.fg : "#e05c68"
            }
            // Dictation: seven bars mirrored around the centre line, fed by the
            // microphone while listening and pulsing while transcribing.
            Row {
                visible: capture.listening
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 1
                Repeater {
                    model: 7
                    Rectangle {
                        required property int index
                        anchors.verticalCenter: parent.verticalCenter
                        width: 2
                        radius: 1
                        color: "#e05c68"
                        height: capture.transcribing
                            ? 3 + 9 * (0.5 + 0.5 * Math.sin((capture.transcribePhase - index / 7) * 2 * Math.PI))
                            : 3 + 11 * (capture.dictationLevels[Math.abs(index - 3)] || 0)
                        // Smooths the 70 ms microphone samples only: the pulse changes every
                        // frame, and a Behavior restarted each frame never leaves its start.
                        Behavior on height { enabled: !capture.transcribing; NumberAnimation { duration: DesktopStyle.motionDuration(70) } }
                    }
                }
            }
            MouseArea {
                id: recordingMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: capture.recording ? Qt.PointingHandCursor : Qt.ArrowCursor
                onClicked: if (capture.recording) capture.recordingClicked()
            }
            BarTooltip {
                target: recordingDot
                hovered: recordingMouse.containsMouse
                text: capture.dictating ? Eitr.I18n.tr("Dictating") : capture.transcribing ? Eitr.I18n.tr("Transcribing")
                    : capture.recordingPaused ? "Recording paused" : capture.streaming ? "Live" : "Recording"
                foreground: shell.fg
                background: shell.workspaceMenuBg
            }
        }
    }

    component WeatherWidget: Item {
        id: weather
        signal clicked()
        property bool autoRefresh: true
        property bool compact: false
        property string text: "󰖐"
        property string location: ""
        property string condition: ""
        property string temp: ""
        property string feels: ""
        property string wind: ""
        property string humidity: ""
        property string forecast: ""
        property var latestData: ({})
        property int dataRevision: 0
        property int requestedRevision: 0

        function refresh() {
            if (process.running)
                return ;

            process.command = ["bash", Quickshell.shellDir + "/scripts/weather-status.sh"];
            requestedRevision = dataRevision;
            process.running = true;
        }

        function updateData(data) {
            dataRevision++;
            latestData = data;
            weather.text = String(data.text || weather.text);
            weather.location = String(data.location || "");
            weather.condition = String(data.condition || "");
            weather.temp = String(data.temp || "");
            weather.feels = String(data.feels || "");
            weather.wind = String(data.wind || "");
            weather.humidity = String(data.humidity || "");
            weather.forecast = String(data.forecast || "");
        }

        function parse(raw) {
            // A panel refresh may have supplied newer data during this request.
            if (requestedRevision !== dataRevision) return;
            var value = String(raw || "").trim();
            if (value === "")
                return ;

            try {
                var data = JSON.parse(value.split("\n").pop());
                weather.updateData(data);
            } catch (e) {
                weather.text = "󰖐";
                weather.condition = "Weather unavailable";
            }
        }

        readonly property string temperature: weather.temp || (weather.text.indexOf(" ") >= 0 ? weather.text.slice(weather.text.indexOf(" ") + 1).trim() : "")
        readonly property real contentWidth: Math.max(26, label.implicitWidth + 8)
        width: contentWidth
        height: 24
        Component.onCompleted: if (autoRefresh) refresh()

        Row {
            id: label
            anchors.centerIn: parent
            spacing: 3
            Text {
                text: weather.text.split(" ")[0]
                color: shell.fg
                font.family: DesktopFonts.family
                font.pixelSize: weather.compact ? 12 : 14
                font.bold: true
            }
            Text {
                visible: !weather.compact
                text: weather.temperature
                color: shell.fg
                font.family: DesktopFonts.family
                font.pixelSize: weather.compact ? 12 : 14
                font.bold: true
            }
        }

        MouseArea {
            id: weatherMouse
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: weather.clicked()
        }

        BarTooltip {
            background: shell.workspaceMenuBg
            foreground: shell.fg
            target: weather
            hovered: weatherMouse.containsMouse
            // Vertical bars show only the icon; the temperature moves to the tooltip.
            text: weather.compact && weather.temperature ? Eitr.I18n.tr("Weather") + " · " + weather.temperature : Eitr.I18n.tr("Weather")
        }

        Timer {
            interval: 900000
            running: weather.autoRefresh
            repeat: true
            onTriggered: weather.refresh()
        }

        Process {
            id: process

            running: false
            command: []
            onExited: weather.parse(weatherOutput.text)

            stdout: StdioCollector {
                id: weatherOutput

                waitForEnd: true
            }

        }

    }

    component NotificationWidget: Rectangle {
        id: notifications
        // A click opens the center on the bar that was clicked, not on the focused display.
        signal openRequested()

        readonly property bool hasNotifications: notificationsService.count > 0
        readonly property string text: notificationsService.doNotDisturb ? (hasNotifications ? "󰂠" : "󰪓") : (hasNotifications ? "󱅫" : "󰂜")
        readonly property string tooltip: notificationsService.doNotDisturb ? Eitr.I18n.tr("Do Not Disturb") : (hasNotifications ? (notificationsService.count === 1 ? Eitr.I18n.tr("{count} notification", {count: notificationsService.count}) : Eitr.I18n.tr("{count} notifications", {count: notificationsService.count})) : Eitr.I18n.tr("No notifications"))

        width: shell.workspaceItemSize
        height: 24
        radius: DesktopStyle.radius(7)
        color: "transparent"

        Text {
            anchors.fill: parent
            text: notifications.text
            color: shell.fg
            font.family: DesktopFonts.family
            font.pixelSize: 18
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        MouseArea {
            id: mouse

            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: function(event) {
                if (event.button === Qt.RightButton)
                    notificationsService.toggleDnd();
                else
                    notifications.openRequested();
            }
        }

        BarTooltip {
            background: shell.workspaceMenuBg
            foreground: shell.fg
            target: notifications
            hovered: mouse.containsMouse
            text: notifications.tooltip
        }

        Behavior on color {
            ColorAnimation {
                duration: DesktopStyle.motionDuration(120)
            }

        }

    }

    component ClockButton: Rectangle {
        id: clock

        property date now: new Date()
        property bool compact: false

        signal clicked()

        width: compact ? shell.barHeight - 2 : label.implicitWidth + 17
        height: compact ? compactLabel.implicitHeight + 6 : 24
        radius: DesktopStyle.radius(7)
        color: "transparent"

        Timer {
            interval: 1000
            running: clock.visible
            repeat: true
            triggeredOnStart: true
            onTriggered: clock.now = new Date()
        }

        Text {
            id: label

            anchors.centerIn: parent
            visible: !clock.compact
            text: Qt.formatDateTime(clock.now, shell.barClock === "24h" ? Eitr.I18n.tr("ddd MMM dd HH:mm") : Eitr.I18n.tr("ddd MMM dd hh:mm AP"))
            horizontalAlignment: Text.AlignHCenter
            color: shell.fg
            font.family: DesktopFonts.family
            font.pixelSize: 14
            font.bold: true
        }

        // Vertical bars stack the hour over the minutes (and AM/PM for 12-hour time), with a calendar glyph below.
        Column {
            id: compactLabel

            anchors.centerIn: parent
            visible: clock.compact
            spacing: 2
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatDateTime(clock.now, shell.barClock === "24h" ? "HH\nmm" : "hh\nmm")
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 0.9
                color: shell.fg
                font.family: DesktopFonts.family
                font.pixelSize: 13
                font.bold: true
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: shell.barClock !== "24h"
                text: Qt.formatDateTime(clock.now, "AP")
                color: shell.fg
                font.family: DesktopFonts.family
                font.pixelSize: 9
                font.bold: true
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "\u{F00ED}"
                color: shell.fg
                font.family: DesktopFonts.family
                font.pixelSize: 14
            }
        }

        MouseArea {
            id: mouse

            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: clock.clicked()
        }

        BarTooltip {
            background: shell.workspaceMenuBg
            foreground: shell.fg
            target: clock
            hovered: mouse.containsMouse
            text: clock.compact ? Qt.formatDateTime(clock.now, Eitr.I18n.tr("ddd MMM dd")) : Eitr.I18n.tr("Calendar")
        }

    }

}
