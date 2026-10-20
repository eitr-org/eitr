import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io
import Quickshell.Services.Notifications
import "NotificationLogic.js" as Logic

Item {
    id: service
    property bool doNotDisturb: false
    property bool centerOpen: false
    property var timestamps: ({})
    property var popupDeadlines: ({})
    property var popupIds: []
    property var pausedPopupIds: []
    property var retainedImages: ({})
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
            asynchronous: false
            cache: true
        }
    }
    function retainImage(notification) {
        if (retainedImages[notification.id]) return;
        retainedImages[notification.id] = retainedImageComponent.createObject(service,
            {notification: notification});
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
    onCenterOpenChanged: if (centerOpen) popupIds = []
    onAllChanged: {
        var ids = all.map(notification => notification.id);
        Object.keys(retainedImages).forEach(id => {
            if (ids.indexOf(Number(id)) === -1) {
                retainedImages[id].destroy();
                delete retainedImages[id];
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
        }
    }

    Timer {
        interval: 250
        running: service.popupIds.length > 0
        repeat: true
        onTriggered: {
            var now = Date.now();
            service.all.slice().forEach(notification => {
                var deadline = service.popupDeadlines[notification.id];
                if (deadline && deadline <= now && service.popupIds.indexOf(notification.id) !== -1 && service.pausedPopupIds.indexOf(notification.id) === -1) {
                    service.hidePopup(notification.id);
                    if (notification.transient) notification.expire();
                }
            });
        }
    }
    Timer {
        interval: 60000
        running: service.all.length > 100
        repeat: true
        onTriggered: service.all.slice(0, service.all.length - 100).forEach(notification => notification.dismiss())
    }
}
