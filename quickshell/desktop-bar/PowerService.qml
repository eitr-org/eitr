pragma Singleton
import QtQuick

QtObject {
    id: service
    property var battery: ({available: false, percent: 0, status: "", health: 0, hours: 0})
    property var profile: ({available: false, active: "", profiles: []})
    property var radios: ({available: false, enabled: false})
    readonly property bool busy: DesktopData.powerDomain.busy
    readonly property var batterySnapshot: DesktopData.topics["power.battery"]
    readonly property var profileSnapshot: DesktopData.topics["power.profile"]
    readonly property var radioSnapshot: DesktopData.topics["power.radios"]
    property string warmProfile: ""
    property string warmRadios: ""
    property Timer warmup: Timer {
        interval: 8000; running: true
        onTriggered: {
            service.warmProfile = DesktopData.observe("power.profile", service);
            service.warmRadios = DesktopData.observe("power.radios", service);
        }
    }
    signal batteryReceived()
    onBatterySnapshotChanged: if (batterySnapshot && batterySnapshot.status === "ready") {
        battery = batterySnapshot.data;
        batteryReceived();
    }
    onProfileSnapshotChanged: {
        if (profileSnapshot && profileSnapshot.status === "ready") profile = profileSnapshot.data;
        if (warmProfile && profileSnapshot && profileSnapshot.status !== "loading") {
            const token = warmProfile; warmProfile = ""; DesktopData.release(token);
        }
    }
    onRadioSnapshotChanged: {
        if (radioSnapshot && radioSnapshot.status === "ready") radios = radioSnapshot.data;
        if (warmRadios && radioSnapshot && radioSnapshot.status !== "loading") {
            const token = warmRadios; warmRadios = ""; DesktopData.release(token);
        }
    }
    function observe(owner, interval, radios) {
        const tokens = [DesktopData.observe("power.profile", owner, interval)];
        if (radios) tokens.push(DesktopData.observe("power.radios", owner));
        return tokens;
    }
    function release(tokens) { tokens.forEach(token => DesktopData.release(token)); }
    function refresh() { DesktopData.refresh("power.profile"); }
    function act(name, value, callback) {
        return DesktopData.client.actPower(name, name === "profile" ? {path: value} : {extra: value}, callback);
    }
    Component.onCompleted: DesktopData.observe("power.battery", service)
    Component.onDestruction: DesktopData.releaseOwner(service)
}
