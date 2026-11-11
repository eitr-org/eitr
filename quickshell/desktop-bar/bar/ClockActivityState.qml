import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Hyprland
import "../ReminderModel.js" as ReminderModel

// What is happening around a bar's clock, for every layout: a new notification rings the
// bell twice (the bar's own bell, or one that slides out beside the clock where the layout
// hides it); a timer or focus session and an event starting within ten minutes put a mark
// beside the clock; changing workspace (where the workspaces are hidden) and a running-low
// battery briefly show over the time. Volume and brightness keep their own popup. CaptureIndicator and Drop's pill draw it;
// ClockButton draws the flash.
Item {
    id: activity
    required property var host
    required property var barHost
    visible: false
    readonly property var notifications: barHost.notificationsRef
    // Layouts that show no bell or workspaces at rest: Drop, Centered collapsed, Dynamic at rest.
    readonly property bool bellHidden: barHost.dropLayout || (barHost.centeredLayout && !barHost.expanded)
        || (barHost.dynamicLayout && !barHost.dynamicSurfaces.trailingIsland.expanded)
    readonly property bool workspacesHidden: barHost.dropLayout || (barHost.centeredLayout && !barHost.expanded)
        || (barHost.dynamicLayout && !barHost.dynamicSurfaces.leadingIsland.expanded)

    // From a new popup until the popups have gone; auto-hide keeps the bar out meanwhile.
    property bool alerting: false
    // The slid-out bell beside the clock, where the layout hides its own.
    readonly property bool bellOut: alerting && bellHidden
    // The ringing bell's angle, for whichever bell is on screen.
    property real bellAngle: 0
    property int popupCount: notifications ? notifications.popups.length : 0
    property int seenPopups: 0
    onPopupCountChanged: {
        if (popupCount > seenPopups && !notifications.doNotDisturb) ring.restart();
        else if (popupCount === 0 && !ring.running) alerting = false;
        seenPopups = popupCount;
    }
    SequentialAnimation {
        id: ring
        PropertyAction { target: activity; property: "alerting"; value: true }
        // Long enough for a hidden bar to come out and a bell to slide out before it rings.
        PauseAnimation { duration: DesktopStyle.motionDuration(activity.host.barAutoHide ? 640 : activity.bellHidden ? 320 : 0) }
        SequentialAnimation {
            loops: 2
            NumberAnimation { target: activity; property: "bellAngle"; to: 18; duration: 90 }
            NumberAnimation { target: activity; property: "bellAngle"; to: -16; duration: 140 }
            NumberAnimation { target: activity; property: "bellAngle"; to: 10; duration: 120 }
            NumberAnimation { target: activity; property: "bellAngle"; to: 0; duration: 110 }
            PauseAnimation { duration: 260 }
        }
        ScriptAction { script: if (activity.popupCount === 0) activity.alerting = false }
    }

    // A timer or focus session running, and the next event when it is less than ten
    // minutes away (checked each minute).
    readonly property bool timing: FocusTimer.active
    property bool meetingSoon: false
    property string meetingTitle: ""
    function checkMeeting() {
        const calendar = barHost.calendarMenu;
        const now = Date.now() / 1000;
        const soon = calendar ? ReminderModel.dayItems(calendar.reminders || [], calendar.events || [], new Date())
            .find(item => !item.allDay && item.due > now && item.due - now <= 600) : null;
        meetingSoon = !!soon;
        meetingTitle = soon ? soon.text : "";
    }
    Timer { interval: 60000; repeat: true; running: true; triggeredOnStart: true; onTriggered: activity.checkMeeting() }

    // 0 shows the time, 1 the flash: a workspace number or a battery warning rises over
    // the time and falls back.
    property real flash: 0
    property string flashText: ""
    property color flashColor: host.fg
    function showFlash(text, color) {
        flashText = text; flashColor = color;
        flashing.restart();
    }
    SequentialAnimation {
        id: flashing
        NumberAnimation { target: activity; property: "flash"; to: 1; duration: DesktopStyle.motionDuration(260); easing.type: Easing.OutBack }
        PauseAnimation { duration: 900 }
        NumberAnimation { target: activity; property: "flash"; to: 0; duration: DesktopStyle.motionDuration(260); easing.type: Easing.InCubic }
    }
    // Only a real screen has a Hyprland monitor (test hosts pass a plain object).
    readonly property var monitor: {
        try { return barHost.screen ? Hyprland.monitorFor(barHost.screen) : null; }
        catch (error) { return null; }
    }
    readonly property int workspaceId: monitor && monitor.activeWorkspace ? monitor.activeWorkspace.id : 0
    property int seenWorkspace: 0
    onWorkspaceIdChanged: {
        if (workspacesHidden && seenWorkspace !== 0 && workspaceId > 0 && workspaceId !== seenWorkspace) {
            const entry = host.workspaceRows(barHost.screen).find(row => row.id === workspaceId);
            showFlash(String(entry ? entry.number : workspaceId), host.fg);
        }
        if (workspaceId > 0) seenWorkspace = workspaceId;
    }
    // A running-low battery flashes its percentage in red once as it reaches 15% and 5%.
    readonly property var battery: PowerService.battery
    readonly property int batteryPercent: battery && battery.available && battery.status !== "Charging" ? Math.round(battery.percent) : 100
    property int warnedAt: 100
    onBatteryPercentChanged: {
        if (batteryPercent > 15) { warnedAt = 100; return; }
        const level = batteryPercent <= 5 ? 5 : 15;
        if (level < warnedAt) { warnedAt = level; showFlash("󰁺 " + batteryPercent + "%", "#e05c68"); }
    }
}
