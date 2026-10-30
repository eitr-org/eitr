import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr

// The Handbook overlay and what a login starts around it: the first-login welcome,
// the problem-report choice, the boot-guard notice and plugins' login hooks.
Scope {
    id: session
    property var host
    Handbook {
        id: handbook
        foreground: host.fg
        background: host.barBackground()
        accent: host.activeBg
        screen: host.targetScreens()[0] || null
        onOpenedChanged: if (opened) host.handbookOpened()
        onSetupRequested: function(kind) {
            // Layouts are added in Walker's Keyboard menu; the bar panel only switches them.
            if (kind === "keyboard") {
                Quickshell.execDetached([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:keyboard"]);
                return;
            }
            var script = kind === "theme" || kind === "wallpaper" ? "appearance-picker.sh" : "show-panel.sh";
            Quickshell.execDetached(["bash", Quickshell.shellDir + "/scripts/" + script, kind]);
        }
        onWelcomeChoice: function(action) { Quickshell.execDetached(session.welcomeCommand(action)); }
        onProblemReportsChoice: function(offer) {
            Quickshell.execDetached(session.problemReportsCommand(["set", offer ? "on" : "off"]));
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
        command: session.problemReportsCommand(["status"])
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
        command: session.welcomeCommand("status")
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
}
