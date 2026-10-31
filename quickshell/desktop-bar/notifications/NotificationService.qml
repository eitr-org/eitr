import ".."
import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io
import Quickshell.Services.Notifications
import "../NotificationLogic.js" as Logic

Item {
    id: service
    property bool doNotDisturb: false
    property bool centerOpen: false
    property var timestamps: ({})
    property var popupDeadlines: ({})
    property var popupIds: []
    property var pausedPopupIds: []
    property var retainedImages: ({})
    // Decoded RGBA thumbnail storage; visible images are pinned even over budget.
    property int retainedImageBudget: 32 * 1024 * 1024
    property int retainedImageBytes: 0
    property var imageOrder: []
    signal toggleRequested()
    readonly property var tracked: server.trackedNotifications.values
    property var all: []
    function syncNotifications() {
        all = tracked.slice();
    }
    // Coalesce dismiss bursts before rebuilding groups and their card delegates.
    onTrackedChanged: Qt.callLater(syncNotifications)
    readonly property var history: all.filter(notification => !notification.transient)
    readonly property var groups: Logic.grouped(all, timestamps)
    readonly property int count: history.length
    property var preferenceData: ({version: 1})
    property bool preferenceWritable: false
    readonly property var popups: all.filter(notification => popupIds.indexOf(notification.id) !== -1)
    readonly property var popupGroups: Logic.grouped(popups, timestamps, true).slice(0, 4)

    // Senders such as Satty delete their thumbnail file on exit. Keep the decoded
    // image alive immediately, even when popups are hidden or DND is enabled.
    // Cards use the identical source/size so they share Qt's in-memory image cache.
    Component {
        id: retainedImageComponent
        Image {
            required property var notification
            visible: false
            source: Logic.imageSource(notification)
            sourceSize: Qt.size(Logic.thumbnailWidth, Logic.thumbnailHeight)
            asynchronous: false
            cache: true
        }
    }
    function retainImage(notification) {
        releaseImage(notification.id);
        var image = retainedImageComponent.createObject(service, {notification: notification});
        retainedImages[notification.id] = image;
        imageOrder = imageOrder.concat([notification.id]);
        retainedImageBytes += image.sourceSize.width * image.sourceSize.height * 4;
    }
    function releaseImage(id) {
        var image = retainedImages[id];
        if (!image) return;
        retainedImageBytes -= image.sourceSize.width * image.sourceSize.height * 4;
        image.source = "";
        image.destroy();
        delete retainedImages[id];
        imageOrder = imageOrder.filter(value => value !== Number(id));
    }
    function imagePinned(id) {
        if (centerOpen) return true;
        var pendingPopups = tracked.filter(notification => popupIds.indexOf(notification.id) !== -1);
        return Logic.grouped(pendingPopups, timestamps, true).slice(0, 4).some(group =>
            group.notifications[0].id === Number(id));
    }
    function trimImages() {
        imageOrder.slice().forEach(id => {
            if (retainedImageBytes > retainedImageBudget && !imagePinned(id)) releaseImage(id);
        });
    }
    onPopupIdsChanged: { trimImages(); Qt.callLater(pruneHistory); scheduleExpiry(); }
    onPausedPopupIdsChanged: scheduleExpiry()
    onPopupDeadlinesChanged: scheduleExpiry()
    onRetainedImageBudgetChanged: trimImages()
    function scheduleExpiry() {
        expiry.stop();
        var now = Date.now();
        var nearest = Infinity;
        all.forEach(notification => {
            var id = notification.id;
            var deadline = popupDeadlines[id];
            if (deadline && popupIds.indexOf(id) !== -1 && pausedPopupIds.indexOf(id) === -1)
                nearest = Math.min(nearest, deadline);
            if (notification.appName === "Reminders" && notification.expireTimeout > 0)
                nearest = Math.min(nearest, timestamps[id] + notification.expireTimeout);
        });
        if (isFinite(nearest)) {
            expiry.interval = Math.max(1, Math.min(2147483647, nearest - now));
            expiry.start();
        }
    }

    function hidePopup(id) {
        popupIds = popupIds.filter(value => value !== id);
    }
    function hidePopupGroup(name) {
        var ids = popups.filter(notification => (notification.appName || "Application") === name).map(notification => notification.id);
        ids.forEach(id => hidePopup(id));
        pausedPopupIds = pausedPopupIds.filter(id => ids.indexOf(id) === -1);
    }
    function pausePopup(id, paused) {
        pausedPopupIds = pausedPopupIds.filter(value => value !== id);
        if (paused) pausedPopupIds = pausedPopupIds.concat([id]);
        else if (popupDeadlines[id]) {
            var deadlines = Object.assign({}, popupDeadlines);
            deadlines[id] = Math.max(deadlines[id], Date.now() + 1500);
            popupDeadlines = deadlines;
        }
    }
    function clear() {
        all.slice().forEach(notification => notification.dismiss());
        popupIds = [];
    }
    function clearApp(appName) {
        all.slice().filter(notification => (notification.appName || "Application") === appName).forEach(notification => notification.dismiss());
    }
    function toggleDnd() {
        if (!preferenceWritable) return doNotDisturb;
        doNotDisturb = !doNotDisturb;
        preferenceData = Object.assign({}, preferenceData, {version: 1, doNotDisturb: doNotDisturb});
        settings.setText(JSON.stringify(preferenceData) + "\n");
        return doNotDisturb;
    }
    onDoNotDisturbChanged: if (doNotDisturb) popupIds = []
    onCenterOpenChanged: { if (centerOpen) popupIds = []; trimImages(); Qt.callLater(pruneHistory); }
    function pruneHistory() {
        // Keep the existing history length, but never dismiss a displayed card.
        all.slice(0, Math.max(0, all.length - 100)).forEach(notification => {
            if (!imagePinned(notification.id)) notification.dismiss();
        });
    }
    onAllChanged: {
        var ids = all.map(notification => notification.id);
        Object.keys(retainedImages).forEach(id => {
            if (ids.indexOf(Number(id)) === -1) {
                releaseImage(id);
            }
        });
        popupIds = popupIds.filter(id => ids.indexOf(id) !== -1);
        pausedPopupIds = pausedPopupIds.filter(id => ids.indexOf(id) !== -1);
        var times = {}, deadlines = {};
        ids.forEach(id => {
            if (timestamps[id] !== undefined) times[id] = timestamps[id];
            if (popupDeadlines[id] !== undefined) deadlines[id] = popupDeadlines[id];
        });
        timestamps = times;
        popupDeadlines = deadlines;
        pruneHistory();
        trimImages();
        scheduleExpiry();
    }

    IpcHandler {
        target: "notifications"
        function toggle(): void { service.toggleRequested(); }
        function clear(): void { service.clear(); }
        function clearApp(appName: string): void { service.clearApp(appName); }
        function dnd(): bool { return service.toggleDnd(); }
        function status(): string { return JSON.stringify({count: service.count, doNotDisturb: service.doNotDisturb, popups: service.popups.length}); }
        function imageStatus(): string {
            return JSON.stringify(Object.keys(service.retainedImages).map(id => ({
                id: Number(id), status: service.retainedImages[id].status
            })));
        }
    }

    FileView {
        id: settings
        path: Eitr.Paths.config("quickshell/desktop-bar/notification-settings.json")
        atomicWrites: true
        printErrors: false
        onLoadFailed: function(error) {
            if (error === FileViewError.FileNotFound) settings.setText('{"version":1,"doNotDisturb":false}\n');
            else console.warn("Could not read notification settings:", error);
        }
        onLoaded: {
            try {
                service.preferenceData = Eitr.Paths.settings(text());
                service.doNotDisturb = service.preferenceData.doNotDisturb === true;
                service.preferenceWritable = true;
            } catch (error) {
                service.preferenceWritable = false;
                console.warn("Invalid notification settings:", error);
            }
        }
    }

    NotificationServer {
        id: server
        keepOnReload: true
        persistenceSupported: true
        actionsSupported: true
        imageSupported: true
        bodyMarkupSupported: false
        inlineReplySupported: true
        onNotification: function(notification) {
            if (Logic.ignored(notification.appName)) return;
            notification.tracked = true;
            service.retainImage(notification);
            var times = Object.assign({}, service.timestamps);
            times[notification.id] = Date.now();
            service.timestamps = times;
            if (!notification.lastGeneration && !service.doNotDisturb && !service.centerOpen) {
                var duration = Logic.popupDuration(notification);
                var deadlines = Object.assign({}, service.popupDeadlines);
                deadlines[notification.id] = duration ? Date.now() + duration : 0;
                service.popupDeadlines = deadlines;
                service.popupIds = service.popupIds.filter(id => id !== notification.id).concat([notification.id]);
            } else if (notification.transient) {
                notification.expire();
            }
            service.trimImages();
        }
    }

    Timer {
        id: expiry
        repeat: false
        onTriggered: {
            var now = Date.now();
            service.all.slice().forEach(notification => {
                var id = notification.id;
                var deadline = service.popupDeadlines[id];
                if (deadline && deadline <= now && service.popupIds.indexOf(id) !== -1
                        && service.pausedPopupIds.indexOf(id) === -1) {
                    service.hidePopup(id);
                    if (notification.transient) notification.expire();
                }
                if (notification.appName === "Reminders" && notification.expireTimeout > 0
                        && now - service.timestamps[id] >= notification.expireTimeout)
                    notification.expire();
            });
            service.scheduleExpiry();
        }
    }
}
