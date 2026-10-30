pragma Singleton
import QtQuick
import Quickshell.Hyprland

QtObject {
    id: obs
    property var state: ({running: false, ready: false, recording: false, paused: false, streaming: false})
    readonly property bool hasWindow: Hyprland.toplevels.values.some(window => /^(com\.obsproject\.studio|obs)$/i.test((window.lastIpcObject || {}).class))
    property int detailObservers: 0
    property bool pending: false
    readonly property bool busy: DesktopData.captureDomain.busy
    readonly property var summary: DesktopData.topics["capture.summary"]
    readonly property var details: DesktopData.topics["capture.details"]
    property string summaryToken: ""
    property string detailsToken: ""
    signal received(var snapshot)
    signal detailsReceived(var snapshot)
    function refresh() {
        DesktopData.refresh(detailObservers > 0 ? "capture.details" : "capture.summary");
    }
    function act(action, argument, callback) {
        return DesktopData.client.actCapture(action, {argument: argument || ""}, callback);
    }
    onSummaryChanged: {
        if (!summary) return;
        if (summary.status === "ready") state = summary.data;
        else state = Object.assign({}, state, {ready: false});
        received(state);
    }
    onDetailsChanged: if (details && details.status === "ready") detailsReceived(details.data)
    onDetailObserversChanged: {
        if (detailObservers > 0 && !detailsToken) detailsToken = DesktopData.observe("capture.details", obs);
        else if (detailObservers <= 0 && detailsToken) {
            DesktopData.release(detailsToken);
            detailsToken = "";
        }
    }
    Component.onCompleted: {
        DesktopData.client.setCapturePresence(hasWindow);
        summaryToken = DesktopData.observe("capture.summary", obs);
    }
    Component.onDestruction: DesktopData.releaseOwner(obs)
    onHasWindowChanged: DesktopData.client.setCapturePresence(hasWindow)
}
