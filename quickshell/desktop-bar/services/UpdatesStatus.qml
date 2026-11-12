import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr

Scope {
    id: status
    // Checked shortly after login, every six hours, and again after System Update.
    property string updatesToken: ""
    Component.onCompleted: updatesToken = DesktopData.observe("updates.status", status)
    Component.onDestruction: DesktopData.releaseOwner(status)
    readonly property var updatesState: DesktopData.topics["updates.status"] || {status: "loading", data: {}}
    // After a successful System Update nothing is pending: show up to date until the next
    // successful scheduled check, instead of checking again right after pacman.
    property bool updatedNow: false
    property int updatedSeq: -1
    function markUpdated() {
        updatedSeq = updatesState.seq !== undefined ? updatesState.seq : -1;
        updatedNow = true;
        announcedUpdates = 0;
    }
    readonly property var updates: updatedNow
        ? {count: 0, repository: 0, aur: 0, downloadBytes: 0, checking: false}
        : Object.assign({count: 0, repository: 0, aur: 0, downloadBytes: 0}, updatesState.data,
            {checking: updatesState.status === "loading" || (!!updatesState.inFlight && updatesState.error !== "broker-unavailable")})
    onUpdatesStateChanged: {
        if (updatedNow && updatesState.status === "ready" && !updatesState.inFlight && (updatesState.seq || 0) > updatedSeq) updatedNow = false;
        if (!updatedNow && updatesState.status === "ready" && !updatesState.inFlight) status.announceUpdates();
    }
    // A notification goes out only when more updates are pending than were last announced.
    property int announcedUpdates: 0
    readonly property string updatesIcon: updates.checking ? "󰁪" : updates.count > 0 ? "󰚰" : "󰗡"
    readonly property string updatesSize: updates.downloadBytes <= 0 ? ""
        : updates.downloadBytes >= 1073741824 ? (updates.downloadBytes / 1073741824).toFixed(1) + " GB"
        : Math.max(1, Math.round(updates.downloadBytes / 1048576)) + " MB"
    readonly property string updatesTooltip: {
        if (updates.checking) return "Checking for updates";
        if (!updatedNow && updatesState.error === "offline") return Eitr.I18n.tr("Offline");
        if (!updatedNow && updatesState.status !== "ready") return Eitr.I18n.tr("Could not check for updates · right-click to try again");
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
        justFound = true;
        foundTimer.restart();
    }
    // True while the "updates available" notification is on screen (a popup's default time),
    // so Drop's pill can show it beside the time.
    property bool justFound: false
    Timer { id: foundTimer; interval: 6500; onTriggered: status.justFound = false }
    function checkUpdates() { DesktopData.refresh("updates.status"); }
    function openSystemUpdate() {
        var root = Quickshell.env("EITR_CODE_ROOT") || Quickshell.shellDir + "/../..";
        // Floating, with the theme's solid background, like terminals that menus open.
        Quickshell.execDetached([root + "/walker/bin/menu-path/kitty", "-e", "python3", root + "/walker/scripts/actions/task-terminal.py",
            "bash", root + "/walker/scripts/actions/system/update.sh", "system"]);
    }
    IpcHandler {
        target: "updates"
        function refresh(): void { status.checkUpdates(); }
        function updated(): void { status.markUpdated(); }
    }
}
