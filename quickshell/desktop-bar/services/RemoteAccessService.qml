import ".."
import QtQuick
import "../JsonState.js" as JsonState

Item {
    id: service
    property bool observing: false
    readonly property bool refreshPending: !!(snapshot && snapshot.pending)
    property var state: ({})
    readonly property bool allowed: state.allowed === true
    readonly property bool busy: !!((snapshot && snapshot.inFlight) || (availability && availability.inFlight))
    readonly property var snapshot: DesktopData.topics["remote.status"]
    readonly property var availability: DesktopData.topics["remote.availability"]
    property string statusToken: ""
    function refresh() {
        DesktopData.refresh("remote.availability");
        if (observing) DesktopData.refresh("remote.status");
    }
    function updateObservation() {
        if (observing && !statusToken) statusToken = DesktopData.observe("remote.status", service);
        else if (!observing && statusToken) {
            DesktopData.release(statusToken);
            statusToken = "";
        }
    }
    onSnapshotChanged: if (snapshot && snapshot.status === "ready" && JsonState.changed(state, snapshot.data)) state = snapshot.data
    onAvailabilityChanged: if (availability && availability.status === "ready") {
        const next = Object.assign({}, state, availability.data);
        if (JsonState.changed(state, next)) state = next;
    }
    Component.onCompleted: {
        DesktopData.observe("remote.availability", service);
        updateObservation();
    }
    Component.onDestruction: DesktopData.releaseOwner(service)
    PreferenceWatch { path: "/etc/eitr/policies.json"; onChanged: service.refresh() }
    onObservingChanged: updateObservation()
}
