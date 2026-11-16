import ".."
import QtQuick
import "DynamicMoments.js" as Queue

// Only BarDynamic instantiates this owner. No other layout subscribes to moments.
Item {
    id: moments
    required property var host
    required property var barHost
    required property var middle
    required property var media
    property bool accepting: barHost.dynamicLayout && !FocusMode.enabled
    property var queueState: Queue.create()
    readonly property var current: accepting ? queueState.active : null
    readonly property bool middleBlocked: middle.hovered || middle.expanded || middle.morphed
    readonly property bool mediaBlocked: media.hovered || media.expanded || media.morphed
    function blocked(island) { return !accepting || (island === "media" ? mediaBlocked : middleBlocked); }
    function submit(payload) {
        if (!barHost.dynamicLayout) return;
        queueState = Queue.push(queueState, payload, Date.now(), blocked);
        schedule();
    }
    function refresh() { queueState = Queue.advance(queueState, Date.now(), blocked); schedule(); }
    function schedule() {
        expiry.stop();
        const delay = Queue.wakeAt(queueState, Date.now());
        if (delay) { expiry.interval = delay; expiry.start(); }
    }
    function retainNotifications(ids) { queueState = Queue.retainNotifications(queueState, ids); refresh(); }
    onMiddleBlockedChanged: refresh()
    onMediaBlockedChanged: refresh()
    onAcceptingChanged: refresh()
    Timer { id: expiry; onTriggered: moments.refresh() }
    DynamicMomentSources { host: moments.host; barHost: moments.barHost; owner: moments }
}
