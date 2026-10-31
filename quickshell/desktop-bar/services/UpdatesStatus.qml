import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr

Scope {
    id: status
    // Checked shortly after login, every six hours, and again after System Update.
    property string updatesToken: DesktopData.observe("updates.status", "shell-updates")
    readonly property var updatesState: DesktopData.topics["updates.status"] || {status: "loading", data: {}}
    readonly property var updates: Object.assign({count: 0, repository: 0, aur: 0, downloadBytes: 0}, updatesState.data,
        {checking: updatesState.status === "loading" || (!!updatesState.inFlight && updatesState.error !== "broker-unavailable")})
    onUpdatesStateChanged: if (updatesState.status === "ready" && !updatesState.inFlight) status.announceUpdates();
    // A notification goes out only when more updates are pending than were last announced.
    property int announcedUpdates: 0
    readonly property string updatesIcon: updates.checking ? "󰁪" : updates.count > 0 ? "󰚰" : "󰗡"
    readonly property string updatesSize: updates.downloadBytes <= 0 ? ""
        : updates.downloadBytes >= 1073741824 ? (updates.downloadBytes / 1073741824).toFixed(1) + " GB"
        : Math.max(1, Math.round(updates.downloadBytes / 1048576)) + " MB"
    readonly property string updatesTooltip: {
        if (updates.checking) return "Checking for updates";
        if (updatesState.error === "offline") return Eitr.I18n.tr("Offline");
        if (updatesState.status !== "ready") return Eitr.I18n.tr("Updates unavailable · right-click to check again");
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
    }
}
