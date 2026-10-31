import ".."
import QtQuick
import Quickshell
import Eitr as Eitr

// The user's hooks and session chores: battery-low once per drop to 15% and the
// low-battery warnings, post-boot at start, and restoring reminders.
Scope {
    id: hooks
    property var host
    Connections {
        target: PowerService
        function onBatteryReceived() { hooks.checkBatteryLow(); }
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
        var discharging = host.battery.available && host.battery.status === "Discharging";
        var low = discharging && host.battery.percent <= 15;
        if (low && !batteryLowHookRan) runHook(["battery-low", String(host.battery.percent)]);
        batteryLowHookRan = low;
        if (!discharging) { batteryWarned = 0; return; }
        var level = host.battery.percent <= 5 ? 5 : host.battery.percent <= 10 ? 10 : 0;
        if (level === 0 || (batteryWarned !== 0 && batteryWarned <= level)) return;
        batteryWarned = level;
        Quickshell.execDetached(["notify-send", "--app-name=Battery", "--urgency=" + (level === 5 ? "critical" : "normal"),
            "--icon=battery-caution-symbolic", level === 5 ? "Battery almost empty" : "Battery low",
            host.battery.percent + "% left. " + (level === 5 ? "Plug in now to avoid losing work." : "Plug in soon.")]);
    }
    Timer { interval: 5000; running: true; onTriggered: hooks.runHook(["post-boot"]) }
    // Reminders survive restarts: reschedule them, and show ones that came due while off.
    Timer {
        interval: 6000
        running: true
        onTriggered: Quickshell.execDetached(["python3", Eitr.Paths.codeRoot + "/walker/scripts/actions/tools/reminders.py", "restore"])
    }
}
