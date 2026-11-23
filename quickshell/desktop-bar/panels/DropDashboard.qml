import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

// Drop's dashboard, opened by clicking its time pill: a row of pages dragged sideways
// (dragging right goes forward, left goes back, both wrapping). It opens on Calendar and
// weather, then Media (skipped while nothing plays), OBS (while it is open or capturing),
// quick controls, Streaming, Performance, AI Usage and
// Notifications. Arrow keys and horizontal scrolling switch pages too.
ThemedPopup {
    id: dashboard
    required property var barHost
    required property var player
    centered: true
    Keys.onLeftPressed: step(-1)
    Keys.onRightPressed: step(1)
    Keys.onEscapePressed: if (!backPlugin()) opened = false
    // The rails sit inside the card along its sides (top and bottom on a side bar), and the
    // pages keep their own width between them.
    readonly property real railRoom: rails.reserve
    implicitWidth: Math.max(580, pluginEntry && pluginEntry.width ? pluginEntry.width : 0) + (verticalAttachment ? 0 : railRoom)
    // The page sets the height; a longer rail scrolls instead of growing the card.
    implicitHeight: viewport.current.implicitHeight + verticalContentInset + (verticalAttachment ? railRoom : 0)
    readonly property var railSurfaces: rails.inputSurfaces
    property Item railItem: DropRails { id: rails; parent: dashboard; owner: dashboard }
    property var pluginEntry: null
    property var pluginHistory: []
    function openPlugin(plugin, panel, remember) {
        if (PluginRegistry.barItemShown && !PluginRegistry.barItemShown(plugin)) return;
        const entry = PluginRegistry.entries.find(candidate => candidate.plugin === plugin && candidate.id === panel && candidate.kind === "panels" && !candidate.disabled);
        if (!entry) return;
        if (entry.bundled && plugin === "ai-usage" && panel === "limits") {
            if (PluginRegistry.aiUsageEnabled) go("ai", 1);
            return;
        }
        if (entry.bundled && plugin === "hardware" && (panel === "details" || panel === "hardware" || panel === "monitor")) {
            if (PluginRegistry.hardwareEnabled) go("performance", 1);
            return;
        }
        pluginHistory = remember && pluginEntry ? pluginHistory.concat([pluginEntry]) : [];
        pluginEntry = entry;
    }
    function backPlugin() {
        if (!pluginEntry) return false;
        pluginEntry = pluginHistory.length ? pluginHistory[pluginHistory.length - 1] : null;
        pluginHistory = pluginHistory.slice(0, -1);
        return true;
    }
    escapeHandler: backPlugin
    property Connections pluginChanges: Connections {
        target: PluginRegistry
        function onEntriesChanged() {
            dashboard.pluginHistory = [];
            if (dashboard.pluginEntry) dashboard.pluginEntry = (!PluginRegistry.barItemShown || PluginRegistry.barItemShown(dashboard.pluginEntry.plugin)) ? (PluginRegistry.entries.find(candidate => candidate.plugin === dashboard.pluginEntry.plugin && candidate.id === dashboard.pluginEntry.id && candidate.kind === "panels" && !candidate.disabled) || null) : null;
        }
        function onPlacementsChanged() {
            if (dashboard.pluginEntry && PluginRegistry.barItemShown && !PluginRegistry.barItemShown(dashboard.pluginEntry.plugin)) {
                dashboard.pluginHistory = [];
                dashboard.pluginEntry = null;
            }
        }
    }
    property date now: new Date()
    // Pages start their data reads only once the card has finished growing (like the
    // Control Center): results arriving mid-animation would rebuild it and make it stutter.
    readonly property bool settled: opened && revealProgress >= 1
    Timer { interval: 1000; running: dashboard.opened; repeat: true; triggeredOnStart: true; onTriggered: dashboard.now = new Date() }

    // The Control Center's chat, when an assistant is set up and policy allows it.
    readonly property bool assistantAvailable: {
        const center = barHost.controlCenter;
        return !!center && !!center.chatAssistant.identifier && center.organizationPolicy.development !== false
            && center.organizationPolicy.assistants_together !== false;
    }
    readonly property var pages: ["home", dashboard.player ? "media" : "", dashboard.obsShown ? "obs" : "", "controls", "display", dashboard.barHost.remoteServiceRef && dashboard.barHost.remoteServiceRef.allowed ? "streaming" : "", PluginRegistry.hardwareEnabled ? "performance" : "", PluginRegistry.aiUsageEnabled ? "ai" : "", dashboard.assistantAvailable ? "assistant" : "", "plugins", "notifications"].filter(Boolean)
    readonly property var obsState: barHost.obsMenu ? barHost.obsMenu.obsState : ({})
    readonly property bool obsShown: !!obsState.recording || !!obsState.streaming || ObsStatus.hasWindow
    property string page: "home"
    readonly property int index: Math.max(0, pages.indexOf(page))
    // The slide: the current page sits at `shift`; the page it is leaving, or the one peeking
    // in during a drag, sits one page further on `otherSide` (-1 left, 1 right).
    property real shift: 0
    property string otherPage: ""
    property int otherSide: 1
    readonly property real span: content.width + 24
    // The page the next opening starts on (the pill's bell and note pick theirs).
    property string startPage: "home"
    function show(target) {
        startPage = pages.indexOf(target) >= 0 ? target : "home";
        if (opened) { go(startPage, 1); startPage = "home"; }
        else barHost.showPanel(dashboard);
    }
    // Opens on the home page with a day's plans showing (the pill's calendar mark).
    property var pendingDay: null
    function showDay(day) {
        if (opened) { show("home"); home.weatherOpen = false; home.selectedDay = day; return; }
        pendingDay = day;
        show("home");
    }
    property bool pendingWeather: false
    function showWeather() {
        if (opened) { show("home"); home.selectedDay = null; home.weatherOpen = true; return; }
        pendingWeather = true;
        show("home");
    }
    onOpenedChanged: {
        pluginEntry = null;
        pluginHistory = [];
        if (!opened) return;
        page = startPage;
        startPage = "home";
        otherPage = "";
        slide.stop();
        shift = 0;
        home.monthOffset = 0;
        home.selectedDay = pendingDay;
        home.weatherOpen = pendingWeather && home.weatherEnabled;
        pendingDay = null;
        pendingWeather = false;
    }
    onPagesChanged: if (pages.indexOf(page) < 0) page = "home"

    function neighbour(direction) {
        return pages[(index + direction + pages.length) % pages.length];
    }
    // Forward (1) brings the next page in from the left, as a drag to the right does.
    function go(target, direction) {
        pluginEntry = null; pluginHistory = [];
        if (target === page || pages.length < 2) return;
        const side = direction > 0 ? -1 : 1;
        otherPage = page;
        page = target;
        shift = shift + side * span;
        otherSide = -side;
        slide.restart();
    }
    function step(direction) { go(neighbour(direction), direction); }
    NumberAnimation { id: slide; target: dashboard; property: "shift"; to: 0; duration: DesktopStyle.motionDuration(280); easing.type: Easing.OutCubic }

    Column {
        id: content
        x: dashboard.verticalAttachment ? 0 : dashboard.railRoom
        y: dashboard.verticalAttachment ? dashboard.railRoom : 0
        width: parent.width - (dashboard.verticalAttachment ? 0 : dashboard.railRoom)
        spacing: 12
        focus: true
        Keys.onLeftPressed: dashboard.step(-1)
        Keys.onRightPressed: dashboard.step(1)

        Item {
            id: viewport
            width: parent.width
            clip: true
            readonly property Item current: dashboard.pluginEntry ? pluginPage : ({home: home, media: media, obs: obs, controls: controls, display: display, streaming: streaming, performance: performance, ai: ai, assistant: assistant, plugins: plugins, notifications: notifications})[dashboard.page] || home
            height: Math.min(current.implicitHeight, Math.max(0, dashboard.height - dashboard.verticalContentInset - (dashboard.verticalAttachment ? dashboard.railRoom : 0)))
            Behavior on height { NumberAnimation { duration: DesktopStyle.motionDuration(240); easing.type: Easing.OutCubic } }
            function place(id) {
                return id === dashboard.page ? dashboard.shift : dashboard.shift + dashboard.otherSide * dashboard.span;
            }
            function shown(id) {
                return !dashboard.pluginEntry && (id === dashboard.page || (id === dashboard.otherPage && (slide.running || drag.active)));
            }

            DropPluginPage {
                id: pluginPage
                visible: !!dashboard.pluginEntry
                width: viewport.width
                owner: dashboard
            }
            DropHomePage {
                id: home
                x: viewport.place("home"); visible: viewport.shown("home")
                width: viewport.width
                barHost: dashboard.barHost; now: dashboard.now
                foreground: dashboard.foreground; accent: dashboard.accent; background: dashboard.background
            }
            MediaPage {
                id: media
                x: viewport.place("media"); visible: viewport.shown("media")
                width: viewport.width
                player: dashboard.player
                host: dashboard.barHost.host
                active: dashboard.opened && visible
                foreground: dashboard.foreground; accent: dashboard.accent; background: dashboard.background
            }
            DropObsPage {
                id: obs
                x: viewport.place("obs"); visible: viewport.shown("obs")
                width: viewport.width
                obs: dashboard.barHost.obsMenu
                active: dashboard.opened && visible
                foreground: dashboard.foreground; accent: dashboard.accent; background: dashboard.background
            }
            // Quick controls is the Control Center's General page, embedded: one set of tiles,
            // opening WiFi, Bluetooth and the sound devices in place. It shares the bar's
            // Control Center controllers, so it is built once that one exists.
            Loader {
                id: controls
                readonly property var main: dashboard.barHost.controlCenter
                x: viewport.place("controls"); visible: viewport.shown("controls")
                width: viewport.width
                height: item ? item.implicitHeight : 0
                active: dashboard.opened && !!main
                sourceComponent: Component {
                    ControlCenter {
                        inlineParent: controls
                        target: null
                        anchors.fill: parent
                        barRef: dashboard.barHost
                        service: controls.main.service
                        wifiControl: controls.main.wifiControl; bluetoothControl: controls.main.bluetoothControl; displayControl: controls.main.displayControl
                        wifiGlyph: controls.main.wifiGlyph
                        battery: controls.main.battery; mediaPlayer: controls.main.mediaPlayer
                        idleEnabled: controls.main.idleEnabled; idleBusy: controls.main.idleBusy
                        foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                        opened: dashboard.settled && controls.visible
                        onIdleToggleRequested: controls.main.idleToggleRequested()
                        onLockRequested: runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")])
                        onPanelRequested: function(kind) { dashboard.opened = false; controls.main.panelRequested(kind); }
                        onSettingsRequested: function(page) { dashboard.barHost.host.showSettings(page); }
                        onClockRequested: function(page) { dashboard.barHost.host.showClock(page); }
                        onCloseRequested: dashboard.opened = false
                    }
                }
            }
            // The Control Center's Plugins page, embedded like Quick controls.
            Loader {
                id: plugins
                x: viewport.place("plugins"); visible: viewport.shown("plugins")
                width: viewport.width
                height: item ? item.implicitHeight : 0
                active: dashboard.opened && !!controls.main
                sourceComponent: Component {
                    ControlCenter {
                        inlineParent: plugins
                        target: null
                        anchors.fill: parent
                        page: "plugins"
                        barRef: dashboard.barHost
                        service: controls.main.service
                        wifiControl: controls.main.wifiControl; bluetoothControl: controls.main.bluetoothControl; displayControl: controls.main.displayControl
                        wifiGlyph: controls.main.wifiGlyph
                        battery: controls.main.battery; mediaPlayer: controls.main.mediaPlayer
                        idleEnabled: controls.main.idleEnabled; idleBusy: controls.main.idleBusy
                        foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                        opened: dashboard.settled && plugins.visible
                        onSettingsRequested: function(page) { dashboard.barHost.host.showSettings(page); }
                        onCloseRequested: dashboard.opened = false
                    }
                }
            }
            // The bar's own Display panel: brightness, displays and the power profile.
            Loader {
                id: display
                x: viewport.place("display"); visible: viewport.shown("display")
                width: viewport.width
                height: item ? item.implicitHeight : 0
                active: dashboard.opened
                sourceComponent: Component {
                    BrightnessMenu {
                        inlineParent: display
                        target: null
                        anchors.fill: parent
                        maximumHeight: Math.max(240, dashboard.barHost.screen.height * 0.6)
                        foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                        opened: dashboard.settled && display.visible
                        onPrimarySelected: DisplayService.refresh()
                    }
                }
            }
            // The Control Center's assistant chat, as its own page.
            Loader {
                id: assistant
                x: viewport.place("assistant"); visible: viewport.shown("assistant")
                width: viewport.width
                height: item ? item.implicitHeight : 0
                active: dashboard.opened && dashboard.pages.includes("assistant")
                sourceComponent: Component {
                    AssistantChat {
                        // The chat fills what it is given and reports no size; the card sizes from this.
                        implicitHeight: 420
                        foreground: dashboard.foreground; background: dashboard.background
                        assistant: dashboard.barHost.controlCenter.chatAssistant
                        onClosed: dashboard.go("home", -1)
                    }
                }
            }
            Loader {
                id: streaming
                x: viewport.place("streaming"); visible: viewport.shown("streaming")
                width: viewport.width
                height: item ? item.implicitHeight : 0
                active: dashboard.opened && dashboard.pages.includes("streaming")
                sourceComponent: Component {
                    RemoteAccessMenu {
                        kind: "streaming"
                        service: dashboard.barHost.remoteServiceRef
                        onObservationChanged: observing => dashboard.barHost.host.remoteObservers += observing ? 1 : -1
                        inlineParent: streaming
                        target: null
                        anchors.fill: parent
                        maximumHeight: Math.max(240, dashboard.barHost.screen.height * 0.6)
                        foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                        opened: dashboard.settled && streaming.visible
                    }
                }
            }
            Loader {
                id: performance
                x: viewport.place("performance"); visible: viewport.shown("performance")
                width: viewport.width
                height: item ? item.implicitHeight : 0
                active: dashboard.opened && PluginRegistry.hardwareEnabled
                sourceComponent: Component {
                    SystemMonitorMenu {
                        inlineParent: performance
                        target: null
                        anchors.fill: parent
                        maximumHeight: Math.max(240, dashboard.barHost.screen.height * 0.6)
                        foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                        opened: dashboard.settled && performance.visible
                    }
                }
            }
            Loader {
                id: ai
                x: viewport.place("ai"); visible: viewport.shown("ai")
                width: viewport.width
                height: item ? item.implicitHeight : 0
                active: dashboard.opened && PluginRegistry.aiUsageEnabled
                sourceComponent: Component {
                    AiUsageMenu {
                        inlineParent: ai
                        target: null
                        anchors.fill: parent
                        maximumHeight: Math.max(240, dashboard.barHost.screen.height * 0.6)
                        foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                        opened: dashboard.settled && ai.visible
                    }
                }
            }
            // The notification center's own list, with its Do Not Disturb and Clear buttons.
            NotificationList {
                id: notifications
                x: viewport.place("notifications"); visible: viewport.shown("notifications")
                // Grows with its notifications up to most of the screen, then scrolls.
                width: viewport.width; implicitHeight: height
                height: service.count === 0 ? 150 : Math.min(contentHeight, Math.max(380, dashboard.barHost.screen.height * 0.7))
                Behavior on height { NumberAnimation { duration: DesktopStyle.motionDuration(240); easing.type: Easing.OutCubic } }
                service: dashboard.barHost.notificationsRef
                foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                onActivated: dashboard.opened = false
                // Reading here counts as the notification center being open.
                readonly property bool reading: dashboard.opened && visible && !dashboard.pluginEntry && dashboard.page === "notifications"
                onReadingChanged: service.centerOpen = reading
            }
            // Dragging sideways anywhere on a page moves it; a short drag springs back.
            DragHandler {
                id: drag
                target: null
                enabled: !dashboard.pluginEntry
                xAxis.enabled: true; yAxis.enabled: false
                cursorShape: Qt.ClosedHandCursor
                onTranslationChanged: {
                    if (!active) return;
                    slide.stop();
                    dashboard.shift = translation.x;
                    dashboard.otherSide = translation.x > 0 ? -1 : 1;
                    dashboard.otherPage = dashboard.neighbour(translation.x > 0 ? 1 : -1);
                }
                onActiveChanged: {
                    if (active) return;
                    if (Math.abs(dashboard.shift) > Math.min(90, viewport.width / 5)) dashboard.step(dashboard.shift > 0 ? 1 : -1);
                    else slide.restart();
                }
            }
            WheelHandler {
                orientation: Qt.Horizontal
                property real gathered: 0
                onWheel: function(event) {
                    gathered += event.angleDelta.x;
                    if (Math.abs(gathered) < 120 || slide.running) return;
                    dashboard.step(gathered < 0 ? 1 : -1);
                    gathered = 0;
                }
            }
        }
    }
}
