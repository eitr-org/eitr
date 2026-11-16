import ".."
import QtQuick
import "BarMoments.js" as Queue

// One queue per bar; layouts supply only presentation and interaction state.
Item {
    id: moments
    required property var host
    required property var barHost
    property var middle: barHost.dynamicSurfaces ? barHost.dynamicSurfaces.middleIsland : null
    property var media: barHost.dynamicSurfaces ? barHost.dynamicSurfaces.mediaIsland : null
    readonly property var clock: host.verticalBar ? barHost.verticalCalendarIcon : barHost.centerInfo
    readonly property bool enabledSetting: host.barMoments !== false
    readonly property bool accepting: enabledSetting && !FocusMode.enabled
    readonly property bool panelsBlocked: !!barHost.panelOpen || !!barHost.pendingPanel || !!barHost.overviewOpen || !!barHost.pendingOverview
    property bool mediaHovered: false
    property bool surfaceHovered: false
    readonly property bool clockHovered: surfaceHovered || (!!clock && !!clock.hovered)
    // Only Dynamic has a media island wide enough for a title; elsewhere the song shows
    // where every other moment does, in the clock slot.
    readonly property bool songInMedia: barHost.dynamicLayout && !!media && media.visible !== false
    property var queueState: Queue.create()
    readonly property var current: accepting ? queueState.active : null
    readonly property var clockMoment: current && (current.kind !== "song" || !songInMedia) ? current : null
    readonly property var songMoment: current && current.kind === "song" && songInMedia ? current : null
    readonly property bool middleBlocked: barHost.dynamicLayout && middle
        ? middle.hovered || middle.expanded || middle.morphed : panelsBlocked || clockHovered
    readonly property bool mediaBlocked: barHost.dynamicLayout && media
        ? media.hovered || media.expanded || media.morphed : panelsBlocked || (songInMedia ? mediaHovered : clockHovered)
    function blocked(island) { return !accepting || (island === "media" ? mediaBlocked : middleBlocked); }
    function holding(island) {
        if (!accepting) return false;
        if (barHost.dynamicLayout) {
            const target = island === "media" ? media : middle;
            return !!target && target.hovered && !target.morphed;
        }
        return !panelsBlocked && (island === "media" && songInMedia ? mediaHovered : clockHovered);
    }
    function submit(payload) {
        if (!enabledSetting) return;
        queueState = Queue.push(queueState, payload, Date.now(), blocked, holding);
        schedule();
    }
    function refresh() {
        queueState = enabledSetting ? Queue.advance(queueState, Date.now(), blocked, holding) : Queue.create();
        schedule();
    }
    function schedule() {
        expiry.stop();
        const delay = Queue.wakeAt(queueState, Date.now());
        if (delay) { expiry.interval = delay; expiry.start(); }
    }
    function retainNotifications(ids) { queueState = Queue.retainNotifications(queueState, ids); refresh(); }
    onMiddleBlockedChanged: refresh()
    onMediaBlockedChanged: refresh()
    onPanelsBlockedChanged: refresh()
    onSongInMediaChanged: refresh()
    onAcceptingChanged: refresh()
    Timer { id: expiry; onTriggered: moments.refresh() }
    BarMomentSources { host: moments.host; barHost: moments.barHost; owner: moments }
}
