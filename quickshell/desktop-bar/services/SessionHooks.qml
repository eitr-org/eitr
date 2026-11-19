import ".."
import QtQuick
import Quickshell
import Eitr as Eitr

// The user's hooks and session chores: battery-low once per drop to the low level
// (Settings, 10% by default) and the low-battery warnings, post-boot at start, and restoring reminders.
Scope {
    id: hooks
    property var host
    Connections {
        target: PowerService
        function onBatteryReceived() { hooks.checkBatteryLow(); hooks.checkCharger(); }
    }
    // The user's hooks (distro/lib/run-hook.sh): battery-low once per drop to the low level,
    // post-boot at start (the runner keeps it to once per boot).
    property bool batteryLowHookRan: false
    function runHook(args) {
        var library = Quickshell.env("EITR_LIBRARY_ROOT") || (Eitr.Paths.codeRoot + "/lib");
        Quickshell.execDetached(["bash", library + "/run-hook.sh"].concat(args));
    }
    // Whether the charger was connected at the last battery reading (null before the first).
    property var chargerConnected: null
    function checkCharger() {
        if (!host.battery.available) return;
        var connected = host.battery.status !== "Discharging";
        if (chargerConnected !== null && connected !== chargerConnected) EventSounds.chargerPlugged(connected);
        chargerConnected = connected;
    }
    // The lowest battery warning already given during this discharge (0 = none).
    property int batteryWarned: 0
    function checkBatteryLow() {
        var discharging = host.battery.available && host.battery.status === "Discharging";
        var lowLevel = host.battery.low !== undefined ? host.battery.low : 10;
        var criticalLevel = host.battery.critical !== undefined ? host.battery.critical : 5;
        var low = discharging && host.battery.percent <= lowLevel;
        if (low && !batteryLowHookRan) runHook(["battery-low", String(host.battery.percent)]);
        batteryLowHookRan = low;
        if (!discharging) { batteryWarned = 0; return; }
        var level = host.battery.percent <= criticalLevel ? criticalLevel : host.battery.percent <= lowLevel ? lowLevel : 0;
        if (level === 0 || (batteryWarned !== 0 && batteryWarned <= level)) return;
        batteryWarned = level;
        Quickshell.execDetached(["notify-send", "--app-name=Battery", "--urgency=" + (level === criticalLevel ? "critical" : "normal"),
            "--icon=battery-caution-symbolic", level === criticalLevel ? "Battery almost empty" : "Battery low",
            host.battery.percent + "% left. " + (level === criticalLevel ? "Plug in now to avoid losing work." : "Plug in soon.")]);
    }
    Timer { interval: 5000; running: true; onTriggered: hooks.runHook(["post-boot"]) }
    // Reminders survive restarts: reschedule them, and show ones that came due while off.
    Timer {
        interval: 6000
        running: true
        onTriggered: Quickshell.execDetached(["python3", Eitr.Paths.codeRoot + "/walker/scripts/actions/tools/reminders.py", "restore"])
    }
}
