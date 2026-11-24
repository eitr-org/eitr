import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../NetworkStatus.js" as NetworkStatus

// The Handbook window and what a login starts around it: the first-login welcome,
// the problem-report choice, the boot-guard notice and plugins' login hooks.
Scope {
    id: session
    property var host
    property var networkSummary: ({status: "loading", data: {}})
    readonly property bool online: NetworkStatus.hasConnection(networkSummary)
    onOnlineChanged: if (online) Qt.callLater(tryStarterThemes)
    Component.onCompleted: if (online) Qt.callLater(tryStarterThemes)

    function tryStarterThemes() {
        if (online && !welcomeSession.starterThemesDone && !starterThemes.running && !starterRetry.running)
            starterThemes.running = true;
    }

    Process {
        id: starterThemes
        command: ["timeout", "--kill-after=5s", "300s", "python3", Eitr.Paths.library("eitr_starter_themes.py")]
        onExited: function(code) {
            if (code === 0) {
                welcomeSession.starterThemesDone = true;
            } else {
                starterRetry.start();
            }
        }
    }
    Timer {
        id: starterRetry
        interval: welcomeSession.starterRetryDelay
        onTriggered: {
            welcomeSession.starterRetryDelay = Math.min(interval * 2, 300000);
            session.tryStarterThemes();
        }
    }
    readonly property bool opened: handbookLoader.item?.opened ?? false
    // The crash-notification preference's default, until the saved choice has been read.
    property bool offerProblemReports: true
    function reader() {
        handbookLoader.active = true;
        handbookLoader.asynchronous = false;
        return handbookLoader.item;
    }
    Loader {
        id: handbookLoader
        active: false
        sourceComponent: Handbook {
            ipcEnabled: false
            offerProblemReports: session.offerProblemReports
            foreground: host.fg
            background: host.barBackground()
            accent: host.activeBg
            screen: host.targetScreens()[0] || null
            onOpenedChanged: if (opened) host.handbookOpened()
            // The welcome's setup cards open their Settings page, such as "connections/wifi".
            onSetupRequested: function(route) { host.showSettings(route); }
            onWelcomeChoice: function(action) { Quickshell.execDetached(session.welcomeCommand(action)); }
            onProblemReportsChoice: function(offer) {
                Quickshell.execDetached(session.problemReportsCommand(["set", offer ? "on" : "off"]));
            }
        }
    }
    IpcHandler {
        target: "handbook"
        function toggle(): void { session.reader().toggle(); }
        function open(chapter: string): void { session.reader().show(chapter); }
        function close(): void { if (handbookLoader.item) handbookLoader.item.opened = false; }
        function scroll(y: int): void { if (handbookLoader.item) handbookLoader.item.scrollTo(y); }
        function status(): string {
            return handbookLoader.item ? handbookLoader.item.status()
                : JSON.stringify({opened: false, chapter: "getting-started", chapters: 0, scroll: 0, error: ""});
        }
    }
    function problemReportsCommand(args) {
        return ["python3", Quickshell.shellDir + "/scripts/problem-reports.py"].concat(args);
    }
    // Once after the boot guard restored the system, a login hears about it.
    Timer {
        interval: 8000
        running: !welcomeSession.noticesChecked
        onTriggered: {
            welcomeSession.noticesChecked = true;
            Quickshell.execDetached(["bash", Quickshell.shellDir + "/scripts/boot-guard-notice.sh"]);
            Quickshell.execDetached(["python3", Eitr.Paths.library("eitr_input_methods.py"), "offer"]);
        }
    }
    // The welcome's "offer to report problems" switch starts from the saved choice, read
    // once when the Handbook is first built rather than at every login.
    Process {
        command: session.problemReportsCommand(["status"])
        running: handbookLoader.active
        stdout: StdioCollector { id: problemStatusOutput }
        onExited: function(code) {
            if (code !== 0) return;
            try { session.offerProblemReports = JSON.parse(problemStatusOutput.text).offer; } catch (error) {}
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
        property bool noticesChecked: false
        property bool starterThemesDone: false
        property int starterRetryDelay: 30000
    }
    Timer {
        // Let the bar and the startup wallpaper reveal settle first.
        interval: 2000
        running: !welcomeSession.checked
        onTriggered: welcomeStatus.running = true
    }
    Process {
        id: welcomeStatus
        command: session.welcomeCommand("status")
        stdout: StdioCollector { id: welcomeOutput }
        onExited: function(code) {
            welcomeSession.checked = true;
            if (code !== 0) return;
            try {
                var state = JSON.parse(welcomeOutput.text);
                if (state.show) session.reader().showWelcome(state.pending);
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
}
